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
