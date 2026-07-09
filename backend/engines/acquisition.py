import torch
try:
    from botorch.acquisition.multi_objective import qExpectedHypervolumeImprovement
    from botorch.acquisition.multi_objective.logei import qLogNoisyExpectedHypervolumeImprovement
    from botorch.utils.multi_objective.box_decompositions.non_dominated import NondominatedPartitioning
    from botorch.models import SingleTaskGP
    HAS_BOTORCH = True
except ImportError:
    HAS_BOTORCH = False

def create_ehvi_acquisition(model, ref_point: list[float], train_Y: torch.Tensor):
    """
    Creates an EHVI acquisition function for multi-objective optimization.
    """
    if not HAS_BOTORCH:
        return None
        
    ref_tensor = torch.tensor(ref_point, dtype=torch.float64)
    partitioning = NondominatedPartitioning(ref_point=ref_tensor, Y=train_Y)
    
    acq_func = qExpectedHypervolumeImprovement(
        model=model,
        ref_point=ref_tensor,
        partitioning=partitioning,
        sampler=None
    )
    return acq_func

def create_log_nehvi_acquisition(model, ref_point: list[float], X_baseline: torch.Tensor):
    """
    Creates a qLogNoisyExpectedHypervolumeImprovement acquisition function
    for multi-objective optimization with noisy outcomes.
    """
    if not HAS_BOTORCH:
        return None
        
    ref_tensor = torch.tensor(ref_point, dtype=torch.float64)
    
    # Prune baseline points if they exceed 4 to avoid exponential box decomposition complexity in high-dimensional (8D) spaces.
    # 8 objectives with many non-dominated points causes CPU hypervolume partitioning to scale exponentially and hang.
    if X_baseline.shape[0] > 4:
        X_baseline = X_baseline[-4:]
    
    acq_func = qLogNoisyExpectedHypervolumeImprovement(
        model=model,
        ref_point=ref_tensor,
        X_baseline=X_baseline,
        prune_baseline=True
    )
    return acq_func

if HAS_BOTORCH:
    from botorch.acquisition import AcquisitionFunction
    
    class CostAwareAcquisition(AcquisitionFunction):
        def __init__(self, acq_func, exc_indices: list[int], lower_bounds: list[float], upper_bounds: list[float], temp_lower: float = 40.0, temp_upper: float = 80.0, gamma: float = 0.15):
            super().__init__(acq_func.model)
            self.acq_func = acq_func
            self.exc_indices = exc_indices
            self.lower_bounds = lower_bounds
            self.upper_bounds = upper_bounds
            self.temp_lower = temp_lower
            self.temp_upper = temp_upper
            self.gamma = gamma
            
        def forward(self, X: torch.Tensor) -> torch.Tensor:
            # X shape: (..., q, D) -- typically (b, 1, D) for q=1
            base_val = self.acq_func(X)
            
            # Compute physical process cost at candidate coordinates
            # Drying temp is index 2 of Critical Process Parameters
            temp_scaled = X[..., 0, 2]
            temp_orig = self.temp_lower + (self.temp_upper - self.temp_lower) * temp_scaled
            
            # Process time cost: lower temperature takes exponentially longer to dry
            drying_cost = torch.exp((100.0 - temp_orig) / 35.0)
            
            # API consumption cost: higher excipient sum implies lower drug loading (cheaper experiment)
            excip_sum = torch.zeros_like(temp_scaled)
            for idx in self.exc_indices:
                l, u = self.lower_bounds[idx], self.upper_bounds[idx]
                excip_sum += l + (u - l) * X[..., 0, idx]
                
            api_frac = (100.0 - excip_sum) / 100.0
            api_cost = api_frac * 15.0  # API material is 15x more expensive than fillers
            
            total_cost = 1.0 + 0.1 * drying_cost + 0.5 * api_cost
            cost_penalty = torch.pow(total_cost, self.gamma)
            
            return base_val / cost_penalty

