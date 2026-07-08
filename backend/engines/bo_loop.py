import numpy as np
import warnings
warnings.filterwarnings('ignore')

try:
    import torch
    from sklearn.preprocessing import MinMaxScaler, StandardScaler
    from botorch.models import ModelListGP
    from botorch.fit import fit_gpytorch_mll
    from gpytorch.mlls import ExactMarginalLogLikelihood
    from botorch.optim import optimize_acqf
    from engines.gp_model import create_gp_model
    from engines.acquisition import create_log_nehvi_acquisition
    HAS_BOTORCH = True
except ImportError:
    HAS_BOTORCH = False

class ActiveLearningLoop:
    def __init__(self, domain, strategy):
        self.domain = domain
        self.strategy = strategy
        self.history_X = []
        self.history_Y = []
        self.seed_count = 0
        
    def add_experiment_result(self, x: list[float], y: list[float]):
        """
        Add a physical lab result into the history to update the GP model.
        """
        self.history_X.append(x)
        self.history_Y.append(y)
        
    def _enforce_mass_balance(self, suggestion: dict) -> dict:
        """
        Ensures that dynamic excipient concentrations + API dose do not exceed 100%.
        Excipient keys are keys ending in '_pct' (except process inputs like granulation_moisture_pct).
        We cap the sum of these excipient percentages at 70.0% (leaving 30% for API/lubricant).
        """
        excip_keys = [
            k for k in suggestion.keys() 
            if k.endswith('_pct') and k not in ('granulation_moisture_pct', 'coating_thickness_pct')
        ]
        if not excip_keys:
            return suggestion
            
        max_excip_allowable = 70.0
        
        # Collect min bounds
        min_bounds = {}
        for k in excip_keys:
            inp = next((i for i in self.domain.inputs if i.key == k), None)
            min_bounds[k] = inp.bounds[0] if inp else 0.0
            
        sum_min = sum(min_bounds.values())
        if sum_min >= max_excip_allowable:
            # If the minimum bounds already exceed or equal the allowable limit,
            # set each excipient to its minimum bound.
            for k in excip_keys:
                suggestion[k] = min_bounds[k]
            return suggestion
            
        total_excip = sum(suggestion[k] for k in excip_keys)
        if total_excip > max_excip_allowable:
            # Scale down the excess above the minimum bounds
            suggested_excess = sum(max(0.0, suggestion[k] - min_bounds[k]) for k in excip_keys)
            allowed_excess = max_excip_allowable - sum_min
            
            if suggested_excess > 0.0:
                scale = allowed_excess / suggested_excess
                for k in excip_keys:
                    excess = max(0.0, suggestion[k] - min_bounds[k])
                    suggestion[k] = min_bounds[k] + excess * scale
            else:
                for k in excip_keys:
                    suggestion[k] = min_bounds[k]
                    
        return suggestion

    def suggest_next(self):
        """
        Optimizes the UCB / qLogNEHVI acquisition function using a GP surrogate.
        """
        # 1. Spaced seed configurations for initial evaluations
        if len(self.history_X) < 3:
            suggestion = {}
            offset = (self.seed_count % 3) * 0.35 + 0.15  # 0.15, 0.50, 0.85
            self.seed_count += 1
            for inp in self.domain.inputs:
                lower, upper = inp.bounds
                suggestion[inp.key] = lower + (upper - lower) * offset
            return self._enforce_mass_balance(suggestion)

        # Use BoTorch if available
        if HAS_BOTORCH:
            try:
                # 2. Extract and transform X and Y data
                X = np.array(self.history_X)
                Y = np.array(self.history_Y)

                # Scale inputs X to [0, 1] using MinMaxScaler
                scaler_x = MinMaxScaler()
                X_scaled = scaler_x.fit_transform(X)
                X_t = torch.tensor(X_scaled, dtype=torch.float64)

                # Transform Y to maximize all objectives
                Y_trans = np.zeros_like(Y)
                Y_trans[:, 0:4] = Y[:, 0:4]  # dissolution_q15/30/45/60 (maximize)
                Y_trans[:, 4] = -np.abs(Y[:, 4] - 100.0)  # hardness_n target midpoint 100
                Y_trans[:, 5] = -Y[:, 5]  # friability_pct (minimize)
                Y_trans[:, 6] = -np.abs(Y[:, 6] - 100.0)  # content_uniformity_pct target midpoint 100
                Y_trans[:, 7] = -np.abs(Y[:, 7] - 0.115)  # heckel slope target midpoint 0.115

                # Scale transformed Y using StandardScaler
                scalers_y = []
                models = []
                Y_scaled_cols = []
                for col_idx in range(Y_trans.shape[1]):
                    y_col = Y_trans[:, col_idx].reshape(-1, 1)
                    scaler_y = StandardScaler()
                    y_scaled = scaler_y.fit_transform(y_col)
                    scalers_y.append(scaler_y)
                    Y_scaled_cols.append(y_scaled)
                    
                    y_t = torch.tensor(y_scaled, dtype=torch.float64)
                    model = create_gp_model(X_t, y_t)
                    mll = ExactMarginalLogLikelihood(model.likelihood, model)
                    fit_gpytorch_mll(mll)
                    model.eval()
                    models.append(model)

                Y_scaled = np.column_stack(Y_scaled_cols)
                Y_scaled_t = torch.tensor(Y_scaled, dtype=torch.float64)
                model_list = ModelListGP(*models)

                # 3. Reference point selection (slightly below the worst observed value)
                ref_point = Y_scaled_t.min(dim=0).values - 0.1 * Y_scaled_t.std(dim=0)

                # 4. Construct qLogNEHVI acquisition function
                acqf = create_log_nehvi_acquisition(model_list, ref_point.tolist(), X_t)

                # 5. Optimize acquisition function across normalized bounds [0, 1]
                bounds_t = torch.zeros(2, X.shape[1], dtype=torch.float64)
                bounds_t[1] = 1.0

                candidate_sc, acqf_val = optimize_acqf(
                    acq_function=acqf,
                    bounds=bounds_t,
                    q=1,
                    num_restarts=3,
                    raw_samples=128
                )

                candidate_sc_np = candidate_sc.detach().numpy().reshape(1, -1)
                candidate_orig = scaler_x.inverse_transform(candidate_sc_np)[0]

                # 6. Apply dynamic physical parameter constraints from domain bounds
                suggestion = {}
                for idx, inp in enumerate(self.domain.inputs):
                    lower, upper = inp.bounds
                    suggestion[inp.key] = float(np.clip(candidate_orig[idx], lower, upper))

                # Enforce mass-balance
                suggestion = self._enforce_mass_balance(suggestion)

                # 7. Feasibility check (prune and print warnings if candidate violates specs)
                with torch.no_grad():
                    candidate_check_sc = scaler_x.transform(np.array([list(suggestion.values())]))
                    candidate_check_t = torch.tensor(candidate_check_sc, dtype=torch.float64)
                    
                    feasible = True
                    cqa = self.strategy.cqa_targets
                    
                    # Map specs to Y_trans space:
                    spec_diss_q30 = float(cqa.dissolution_q30_min_pct)
                    hardness_min_n = float(cqa.hardness_min_kp) * 9.807
                    hardness_max_n = float(cqa.hardness_max_kp) * 9.807
                    spec_hardness = -max(abs(hardness_min_n - 100.0), abs(hardness_max_n - 100.0))
                    spec_friability = -float(cqa.friability_max_pct)
                    spec_cu = -max(abs(cqa.content_uniformity_min_pct - 100.0), abs(cqa.content_uniformity_max_pct - 100.0))
                    spec_heckel = -max(abs(cqa.heckel_slope_min - 0.115), abs(cqa.heckel_slope_max - 0.115))
                    
                    spec_mins = {
                        2: spec_diss_q30,
                        4: spec_hardness,
                        5: spec_friability,
                        6: spec_cu,
                        7: spec_heckel
                    }
                    
                    for col_idx, model in enumerate(models):
                        if col_idx not in spec_mins:
                            continue
                        posterior = model.posterior(candidate_check_t)
                        mean_sc = posterior.mean.item()
                        std_sc = posterior.variance.sqrt().item()
                        
                        scaler_y = scalers_y[col_idx]
                        mean_orig = mean_sc * scaler_y.scale_[0] + scaler_y.mean_[0]
                        std_orig = std_sc * scaler_y.scale_[0]
                        
                        conservative_val = mean_orig - std_orig
                        if conservative_val < spec_mins[col_idx]:
                            feasible = False
                            
                    if not feasible:
                        print(f"  ⚠ Suggested configuration {suggestion} predicted potentially infeasible under targets.")

                return suggestion

            except Exception as e:
                # If BoTorch execution fails, fall back to scikit-learn
                print(f"  ⚠ BoTorch optimization failed with error: {e}. Falling back to scikit-learn.")
                pass

        # 8. Fallback to scikit-learn UCB GP Loop
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import Matern

        X = np.array(self.history_X)
        Y = np.array(self.history_Y)

        gps = []
        for col in range(Y.shape[1]):
            gp = GaussianProcessRegressor(kernel=Matern(nu=2.5), alpha=1e-2, random_state=42)
            gp.fit(X, Y[:, col])
            gps.append(gp)

        n_candidates = 1000
        candidates = []
        for inp in self.domain.inputs:
            lower, upper = inp.bounds
            candidates.append(np.random.uniform(lower, upper, n_candidates))
        candidates = np.column_stack(candidates)

        best_score = -float('inf')
        best_candidate = candidates[0]

        for cand in candidates:
            cand_reshaped = cand.reshape(1, -1)
            scores = []
            for col, gp in enumerate(gps):
                mean, std = gp.predict(cand_reshaped, return_std=True)
                mean = mean[0]
                std = std[0]
                
                if col in [0, 1, 2, 3]:
                    scores.append(mean + 1.5 * std)
                elif col == 4:
                    scores.append(120.0 - abs(mean - 100.0) + 1.5 * std)
                elif col == 5:
                    scores.append(-mean + 1.5 * std)
                elif col == 6:
                    scores.append(105.0 - abs(mean - 100.0) + 1.5 * std)
                elif col == 7:
                    scores.append(0.15 - abs(mean - 0.115) + 1.5 * std)
            
            total_score = sum(scores)
            if total_score > best_score:
                best_score = total_score
                best_candidate = cand

        suggestion = {}
        for idx, inp in enumerate(self.domain.inputs):
            suggestion[inp.key] = float(best_candidate[idx])
        return self._enforce_mass_balance(suggestion)


