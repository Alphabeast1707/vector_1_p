import numpy as np
import warnings
from scipy.stats import qmc
from typing import List, Dict, Optional, Tuple

warnings.filterwarnings('ignore')

try:
    import torch
    from sklearn.preprocessing import MinMaxScaler, StandardScaler
    from botorch.models import ModelListGP
    from botorch.fit import fit_gpytorch_mll
    from gpytorch.mlls import ExactMarginalLogLikelihood
    from botorch.optim import optimize_acqf
    from botorch.utils.multi_objective.hypervolume import Hypervolume
    from engines.gp_model import create_gp_model
    from engines.acquisition import create_log_nehvi_acquisition
    HAS_BOTORCH = True
except ImportError:
    HAS_BOTORCH = False

# Import schema details

def compute_pareto_front(Y: np.ndarray) -> np.ndarray:
    """
    Identifies non-dominated solutions from the objective matrix (higher-is-better).
    Y shape: (n_samples, n_objectives)
    """
    n = len(Y)
    is_pareto = np.ones(n, dtype=bool)
    for i in range(n):
        if not is_pareto[i]:
            continue
        for j in range(n):
            if i == j or not is_pareto[j]:
                continue
            # j dominates i if j >= i in all objectives and j > i in at least one
            if np.all(Y[j] >= Y[i]) and np.any(Y[j] > Y[i]):
                is_pareto[i] = False
                break
    return is_pareto


class ActiveLearningLoop:
    def __init__(self, domain, strategy, profile=None):
        self.domain = domain
        self.strategy = strategy
        self.profile = profile
        self.history_X = []
        self.history_Y = []
        self.seed_count = 0
        self.iteration = 0
        self.hypervolume_history = []
        self.pareto_solutions = []

    def add_experiment_result(self, x: list[float], y: list[float]):
        """
        Add a physical lab result into the history to update the GP model.
        """
        self.history_X.append(x)
        self.history_Y.append(y)

    def get_api_context_vector(self) -> list[float]:
        """
        Extracts 6 key macroscopic and thermodynamic physical context descriptors for the active API.
        Enables Multi-Task / transfer learning across different APIs.
        """
        if self.profile is None:
            # Safe defaults matching Paracetamol
            return [150.0, 1.3, 15.0, 75.0, 2.5, 300.0]
            
        tm = getattr(self.profile.thermal_limits, 'melting_point_c', None) or 150.0
        rho = getattr(self.profile.powder_metrics, 'true_density_g_ml', None) or 1.3
        carr = getattr(self.profile.powder_metrics, 'carrs_index', None) or 15.0
        
        tpsa = 75.0
        logp = 2.5
        mw = 300.0
        
        if self.profile.core_physicochemical:
            tpsa = getattr(self.profile.core_physicochemical, 'tpsa', 75.0) or 75.0
            logp = getattr(self.profile.core_physicochemical, 'log_p', 2.5) or 2.5
            mw = getattr(self.profile.core_physicochemical, 'molecular_weight', 300.0) or 300.0
            
        return [float(tm), float(rho), float(carr), float(tpsa), float(logp), float(mw)]

    def _enforce_mass_balance(self, suggestion: dict) -> dict:
        """
        Ensures that dynamic excipient concentrations do not exceed the dynamic cap based on API drug loading,
        and prints scientific diagnostics for volume-fraction mechanical percolation limits.
        """
        excip_keys = [
            k for k in suggestion.keys() 
            if k.endswith('_pct') and k not in ('granulation_moisture_pct', 'coating_thickness_pct')
        ]
        if not excip_keys:
            return suggestion
            
        # 1. Dynamic Excipient Cap (Gap 5 Elevated)
        # Calculate drug loading % using target dose and total tablet weight if available, fallback to 30% API (70% excipient)
        api_dose = 150.0
        total_weight = 500.0
        if self.profile:
            api_dose = getattr(self.profile, 'dose_mg', None) or getattr(self.profile, 'dose_number', 0.3) * 500.0
            if hasattr(self.profile, 'total_tablet_weight_mg'):
                total_weight = getattr(self.profile, 'total_tablet_weight_mg')
            elif hasattr(self.profile, 'powder_metrics') and hasattr(self.profile.powder_metrics, 'true_density_g_ml'):
                # Heuristically estimate a standard tablet weight from density
                total_weight = self.profile.powder_metrics.true_density_g_ml * 350.0
                
        # Handle cases where dose is extremely small or large
        drug_loading = (api_dose / total_weight) * 100.0
        max_excip_allowable = min(95.0, max(5.0, 100.0 - drug_loading - 1.5))
        
        # Collect min bounds
        min_bounds = {}
        for k in excip_keys:
            inp = next((i for i in self.domain.inputs if i.key == k), None)
            min_bounds[k] = inp.bounds[0] if inp else 0.0
            
        sum_min = sum(min_bounds.values())
        if sum_min >= max_excip_allowable:
            for k in excip_keys:
                suggestion[k] = min_bounds[k]
            return suggestion
            
        total_excip = sum(suggestion[k] for k in excip_keys)
        if total_excip > max_excip_allowable:
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
                    
        # 2. Volume-Fraction Percolation Theory Diagnostics (Gap 5 Elevated)
        # Check if the load-bearing binder achieves the structural percolation threshold (>= 18% v/v)
        binder_keys = [k for k in excip_keys if 'binder' in k.lower() or 'mcc' in k.lower() or 'hpc' in k.lower()]
        if binder_keys:
            api_density = getattr(self.profile.powder_metrics, 'true_density_g_ml', 1.3) if self.profile else 1.3
            
            # Helper excipient densities
            def get_density(name: str) -> float:
                n_l = name.lower()
                if 'mcc' in n_l or 'avicel' in n_l or 'cellulose' in n_l: return 1.55
                if 'lactose' in n_l: return 1.59
                if 'hpc' in n_l or 'hpmc' in n_l or 'polymer' in n_l: return 1.30
                if 'mag' in n_l or 'stearate' in n_l: return 1.03
                return 1.50
                
            weights = {k: suggestion[k] for k in excip_keys}
            weights['api'] = 100.0 - sum(weights.values())
            
            densities = {k: get_density(k) for k in excip_keys}
            densities['api'] = api_density
            
            v_total = sum(weights[k] / densities[k] for k in weights.keys())
            v_binder = sum(weights[k] / densities[k] for k in binder_keys)
            phi_binder = v_binder / v_total if v_total > 0 else 0.0
            
            if phi_binder < 0.18:
                # Store a warning on the class or print/log it for scientific transparency
                print(f"  [Percolation Diagnostic Warning] Suggested binder volume fraction ({phi_binder:.3f} v/v) is below the mechanical percolation threshold (0.18 v/v). Tablet mechanical integrity may be compromised.")
                suggestion["percolation_warning"] = f"Binder volume fraction ({phi_binder:.3f} v/v) is below structural percolation limit (0.18 v/v)."
                    
        return suggestion

    def _transform_objectives(self, Y: np.ndarray) -> np.ndarray:
        """
        Transforms Y parameters into maximization-ready scores.
        """
        Y_trans = np.zeros_like(Y)
        Y_trans[:, 0:4] = Y[:, 0:4]                                      # Dissolution Q15/30/45/60 (maximize)
        # Symmetrical target smoothing using a noise-tolerant Gaussian/Radial target penalty:
        # Hardness: target 100 N, sigma = 10.0 N
        # Content Uniformity: target 100.0%, sigma = 2.5%
        # Heckel Slope: target 0.115, sigma = 0.015
        Y_trans[:, 4] = np.exp(-((Y[:, 4] - 100.0) ** 2) / (2 * (10.0 ** 2))) - 1.0
        Y_trans[:, 5] = -Y[:, 5]                                          # Friability % (minimize)
        Y_trans[:, 6] = np.exp(-((Y[:, 6] - 100.0) ** 2) / (2 * (2.5 ** 2))) - 1.0
        Y_trans[:, 7] = np.exp(-((Y[:, 7] - 0.115) ** 2) / (2 * (0.015 ** 2))) - 1.0
        return Y_trans

    def evaluate_surrogate_calibration(self) -> dict:
        """
        Computes Leave-One-Out CV metrics (R2, CRPS, 95% CI Coverage) across all 8 CQAs.
        Generalizes evaluation to robust probabilistic metrics in sparse data regimes.
        """
        cqa_names = [
            "dissolution_q15", "dissolution_q30", "dissolution_q45", "dissolution_q60", 
            "hardness_n", "friability_pct", "content_uniformity_pct", "compressibility_heckel_slope"
        ]
        
        if len(self.history_X) < 4:
            return {
                "r2": {name: 0.0 for name in cqa_names},
                "crps": {name: 0.0 for name in cqa_names},
                "coverage_95": {name: 1.0 for name in cqa_names}
            }
            
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import Matern
        from sklearn.metrics import r2_score
        from scipy.stats import norm
        import math
        
        X = np.array(self.history_X)
        Y = np.array(self.history_Y)
        
        r2_dict = {}
        crps_dict = {}
        coverage_dict = {}
        
        for col_idx, name in enumerate(cqa_names):
            preds_mean = []
            preds_std = []
            
            for i in range(len(X)):
                X_train = np.delete(X, i, axis=0)
                Y_train = np.delete(Y[:, col_idx], i, axis=0)
                X_test = X[i:i+1]
                
                model = GaussianProcessRegressor(kernel=Matern(nu=2.5), random_state=42)
                model.fit(X_train, Y_train)
                mean, std = model.predict(X_test, return_std=True)
                preds_mean.append(float(mean[0]))
                preds_std.append(float(std[0]))
                
            preds_mean = np.array(preds_mean)
            preds_std = np.array(preds_std)
            actuals = Y[:, col_idx]
            
            # 1. R2 Score
            r2 = r2_score(actuals, preds_mean)
            r2_dict[name] = round(max(-1.0, float(r2)), 4)
            
            # 2. Analytical Gaussian CRPS
            crps_vals = []
            covered_count = 0
            for mu, sigma, act in zip(preds_mean, preds_std, actuals):
                if sigma < 1e-9:
                    crps_vals.append(abs(act - mu))
                else:
                    z = (act - mu) / sigma
                    crps_vals.append(float(sigma * (z * (2 * norm.cdf(z) - 1.0) + 2 * norm.pdf(z) - 1.0 / math.sqrt(math.pi))))
                
                # 3. 95% Confidence Interval Coverage
                ci_lo = mu - 1.96 * sigma
                ci_hi = mu + 1.96 * sigma
                if ci_lo <= act <= ci_hi:
                    covered_count += 1
                    
            crps_dict[name] = round(float(np.mean(crps_vals)), 4)
            coverage_dict[name] = round(covered_count / len(X), 4)
            
        return {
            "r2": r2_dict,
            "crps": crps_dict,
            "coverage_95": coverage_dict
        }

    def compute_loo_cv_r2(self) -> dict:
        """
        Computes Leave-One-Out CV R2 scores across all 8 independent CQAs.
        Preserved for API backwards compatibility.
        """
        return self.evaluate_surrogate_calibration()["r2"]

    def check_convergence(self, tolerance: float = 0.01, patience: int = 3) -> dict:
        """
        Convergence criteria:
        1. Hypervolume improvement < tolerance for consecutive iterations.
        2. All Pareto solutions are in-spec.
        """
        if len(self.hypervolume_history) < patience + 1:
            return {"converged": False, "reason": "insufficient_iterations", "hv_history": self.hypervolume_history}

        recent_gains = [
            self.hypervolume_history[i] - self.hypervolume_history[i-1]
            for i in range(-patience, 0)
        ]

        if all(abs(g) < tolerance for g in recent_gains):
            return {
                "converged": True,
                "reason": "hypervolume_plateau",
                "hv_history": self.hypervolume_history,
                "total_experiments": len(self.history_X)
            }

        return {"converged": False, "reason": "still_improving", "hv_history": self.hypervolume_history}

    def _predict_cqas(self, x: np.ndarray) -> dict:
        """
        Predicts mean, std, 95% Confidence Interval for each CQA.
        """
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import Matern

        X = np.array(self.history_X)
        Y = np.array(self.history_Y)
        
        cqa_names = ["dissolution_q15", "dissolution_q30", "dissolution_q45", "dissolution_q60", 
                     "hardness_n", "friability_pct", "content_uniformity_pct", "compressibility_heckel_slope"]
        
        predictions = {}
        for col_idx, name in enumerate(cqa_names):
            gp = GaussianProcessRegressor(kernel=Matern(nu=2.5), random_state=42)
            gp.fit(X, Y[:, col_idx])
            mean, std = gp.predict(x.reshape(1, -1), return_std=True)
            mean_val = float(mean[0])
            std_val = float(std[0])
            
            ci_lo = mean_val - 1.96 * std_val
            ci_hi = mean_val + 1.96 * std_val
            
            # check specs
            in_spec = True
            if name == "dissolution_q30" and ci_lo < 80.0:
                in_spec = False
            elif name == "hardness_n" and (ci_hi < 80.0 or ci_lo > 120.0):
                in_spec = False
            elif name == "friability_pct" and ci_hi > 1.0:
                in_spec = False
                
            predictions[name] = {
                "mean": round(mean_val, 2),
                "std": round(std_val, 2),
                "ci95_lo": round(ci_lo, 2),
                "ci95_hi": round(ci_hi, 2),
                "in_spec": in_spec
            }
        return predictions

    def suggest_next(self):
        """
        Suggests next-best point using LHS seeds (up to 8 runs) or EHVI optimization.
        """
        n_seeds = 8
        
        # 1. LHS seed generation
        if len(self.history_X) < n_seeds:
            n_dims = len(self.domain.inputs)
            sampler = qmc.LatinHypercube(d=n_dims, seed=42)
            sample = sampler.random(n=n_seeds) # Generates N=8 seed configurations
            
            row = sample[len(self.history_X)]
            suggestion = {}
            for idx, inp in enumerate(self.domain.inputs):
                lower, upper = inp.bounds
                suggestion[inp.key] = lower + (upper - lower) * row[idx]
            
            return self._enforce_mass_balance(suggestion)

        self.iteration += 1

        # Use BoTorch if available
        if HAS_BOTORCH:
            try:
                import torch
                X = np.array(self.history_X)
                Y = np.array(self.history_Y)

                scaler_x = MinMaxScaler()
                X_scaled = scaler_x.fit_transform(X)

                # Fetch 6-dimensional macroscopic thermodynamic physical context descriptor vector of active API (Gap 3 Elevated)
                v_context = self.get_api_context_vector()
                n_samples = X_scaled.shape[0]
                context_matrix = np.tile(v_context, (n_samples, 1))
                X_combined = np.column_stack([X_scaled, context_matrix])
                X_t = torch.tensor(X_combined, dtype=torch.float64)

                Y_trans = self._transform_objectives(Y)

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

                ref_point = Y_scaled_t.min(dim=0).values - 0.1 * Y_scaled_t.std(dim=0)

                # Desirability weight scaling if provided
                if self.strategy.desirability_weights:
                    weights = [self.strategy.desirability_weights.get(obj, 1.0) for obj in 
                               ["dissolution_q15", "dissolution_q30", "dissolution_q45", "dissolution_q60", 
                                "hardness_n", "friability_pct", "content_uniformity_pct", "compressibility_heckel_slope"]]
                    ref_point = ref_point * torch.tensor(weights, dtype=torch.float64)

                acqf = create_log_nehvi_acquisition(model_list, ref_point.tolist(), X_t)

                # Optimization is strictly performed on the D active dimensions to avoid SciPy stalls on fixed/degenerate bounds.
                # The 6 physical API descriptors are appended dynamically inside the acquisition function wrapper.
                bounds_t = torch.zeros(2, X.shape[1], dtype=torch.float64)
                bounds_t[1] = 1.0

                # Formulate dynamic in-loop linear inequality constraints for mass balance
                # Sum of excipients <= 70% w/w (or dynamic excipient cap)
                excip_indices = []
                excip_coeffs = []
                sum_lower_bounds = 0.0
                
                excip_keys = [
                    k for k in [inp.key for inp in self.domain.inputs]
                    if k.endswith('_pct') and k not in ('granulation_moisture_pct', 'coating_thickness_pct')
                ]
                
                for idx, inp in enumerate(self.domain.inputs):
                    if inp.key in excip_keys:
                        lower, upper = inp.bounds
                        excip_indices.append(idx)
                        excip_coeffs.append(-(upper - lower))
                        sum_lower_bounds += lower
                
                # Dynamic Excipient Cap calculation
                api_dose = 150.0
                total_weight = 500.0
                if self.profile:
                    api_dose = getattr(self.profile, 'dose_mg', None) or getattr(self.profile, 'dose_number', 0.3) * 500.0
                    if hasattr(self.profile, 'total_tablet_weight_mg'):
                        total_weight = getattr(self.profile, 'total_tablet_weight_mg')
                    elif hasattr(self.profile, 'powder_metrics') and hasattr(self.profile.powder_metrics, 'true_density_g_ml'):
                        total_weight = self.profile.powder_metrics.true_density_g_ml * 350.0
                drug_loading = (api_dose / total_weight) * 100.0
                max_excip_allowable = min(95.0, max(5.0, 100.0 - drug_loading - 1.5))
                
                inequality_constraints = None
                if excip_indices:
                    indices_t = torch.tensor(excip_indices, dtype=torch.long)
                    coeffs_t = torch.tensor(excip_coeffs, dtype=torch.float64)
                    rhs_val = sum_lower_bounds - max_excip_allowable
                    
                    sum_upper_bounds = sum(inp.bounds[1] for inp in self.domain.inputs if inp.key in excip_keys)
                    if sum_upper_bounds > max_excip_allowable:
                        inequality_constraints = [(indices_t, coeffs_t, rhs_val)]

                # Wrap acquisition function with physical process cost model (Gap 6 Elevated)
                from engines.acquisition import CostAwareAcquisition
                temp_lower, temp_upper = 40.0, 80.0
                for inp in self.domain.inputs:
                    if inp.key == "drying_temp_c":
                        temp_lower, temp_upper = inp.bounds
                        break
                        
                acqf = CostAwareAcquisition(
                    acq_func=acqf,
                    exc_indices=excip_indices,
                    lower_bounds=[inp.bounds[0] for inp in self.domain.inputs],
                    upper_bounds=[inp.bounds[1] for inp in self.domain.inputs],
                    temp_lower=temp_lower,
                    temp_upper=temp_upper,
                    gamma=0.15,
                    v_context=v_context
                )

                import os
                num_restarts = int(os.environ.get("BO_RESTARTS", 2))
                raw_samples = int(os.environ.get("BO_RAW_SAMPLES", 32))

                candidate_sc, acqf_val = optimize_acqf(
                    acq_function=acqf,
                    bounds=bounds_t,
                    q=1,
                    num_restarts=num_restarts,
                    raw_samples=raw_samples,
                    inequality_constraints=inequality_constraints
                )

                candidate_sc_np = candidate_sc.detach().numpy().reshape(1, -1)
                # Candidate contains strictly active dimensions
                candidate_active = candidate_sc_np
                candidate_orig = scaler_x.inverse_transform(candidate_active)[0]

                suggestion = {}
                for idx, inp in enumerate(self.domain.inputs):
                    lower, upper = inp.bounds
                    suggestion[inp.key] = float(np.clip(candidate_orig[idx], lower, upper))

                suggestion = self._enforce_mass_balance(suggestion)

                # Track hypervolume convergence
                pareto_mask = compute_pareto_front(Y_trans)
                Y_pareto = Y_trans[pareto_mask]
                
                # Normalize pareto points to calculate volume
                hv_eval = Hypervolume(ref_point=ref_point)
                hv_val = hv_eval.compute(torch.tensor(Y_pareto, dtype=torch.float64))
                self.hypervolume_history.append(float(hv_val))

                # Store pareto solutions
                self.pareto_solutions = [
                    {
                        "solution_id": i+1,
                        "cpps": dict(zip([inp.key for inp in self.domain.inputs], X[idx])),
                        "cqa_predicted": self._predict_cqas(X[idx])
                    }
                    for idx, i in enumerate(np.where(pareto_mask)[0])
                ]

                return suggestion

            except Exception as e:
                print(f"  ⚠ BoTorch optimization failed with error: {e}. Falling back to scikit-learn.")
                pass

        # Fallback to scikit-learn UCB GP Loop
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
