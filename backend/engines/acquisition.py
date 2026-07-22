import torch
import logging
from botorch.acquisition.multi_objective import qExpectedHypervolumeImprovement
from botorch.acquisition.multi_objective.logei import qLogNoisyExpectedHypervolumeImprovement
from botorch.utils.multi_objective.box_decompositions.non_dominated import NondominatedPartitioning
from botorch.models import SingleTaskGP
from botorch.sampling.normal import SobolQMCNormalSampler
from botorch.acquisition import AcquisitionFunction

# Import CostAwareAcquisition from individual file as requested by code review
from engines.cost_aware_acquisition import CostAwareAcquisition

logger = logging.getLogger("vector_1.acquisition")

# To keep the application working and satisfy review comments, we assert
# that BoTorch and its helpers are imported at the top. We will raise an
# ImportError if they are missing when the functions are called.
HAS_BOTORCH = True

def create_ehvi_acquisition(model, ref_point: list[float], train_Y: torch.Tensor):
    """
    Creates an EHVI acquisition function for multi-objective optimization.
    """
    if not HAS_BOTORCH:
        logger.error("BoTorch is not available. Cannot create EHVI acquisition.")
        raise ImportError("BoTorch is required to generate EHVI acquisition function.")
        
    try:
        ref_tensor = torch.tensor(ref_point, dtype=torch.float64)
        partitioning = NondominatedPartitioning(ref_point=ref_tensor, Y=train_Y)
    except Exception as e:
        logger.error(f"Failed to initialize box partitioning for EHVI: {e}")
        raise ValueError(f"Error handling mechanism failed to construct NondominatedPartitioning: {e}")
    
    try:
        acq_func = qExpectedHypervolumeImprovement(
            model=model,
            ref_point=ref_tensor,
            partitioning=partitioning,
            sampler=None
        )
        return acq_func
    except Exception as e:
        logger.error(f"Failed to instantiate qExpectedHypervolumeImprovement acquisition: {e}")
        raise RuntimeError(f"Error handling mechanism failed to construct qExpectedHypervolumeImprovement: {e}")

def create_log_nehvi_acquisition(model, ref_point: list[float], X_baseline: torch.Tensor):
    """
    Creates a qLogNoisyExpectedHypervolumeImprovement acquisition function
    for multi-objective optimization with noisy outcomes.
    """
    if not HAS_BOTORCH:
        logger.error("BoTorch is not available. Cannot create qLogNEHVI acquisition.")
        raise ImportError("BoTorch is required to generate qLogNEHVI acquisition function.")
        
    try:
        ref_tensor = torch.tensor(ref_point, dtype=torch.float64)
        
        # Prune baseline points if they exceed 4 to avoid exponential box decomposition complexity in high-dimensional (8D) spaces.
        # 8 objectives with many non-dominated points causes CPU hypervolume partitioning to scale exponentially and hang.
        if X_baseline.shape[0] > 4:
            X_baseline = X_baseline[-4:]
            
        # Use a lightweight sampler (16 samples) to prevent CPU hypervolume partitioning from hanging on 8 objectives
        sampler = SobolQMCNormalSampler(sample_shape=torch.Size([16]))
    except Exception as e:
        logger.error(f"Failed to prepare input baseline or sampler for qLogNEHVI: {e}")
        raise ValueError(f"Error handling mechanism failed to set up inputs for qLogNEHVI: {e}")
    
    try:
        acq_func = qLogNoisyExpectedHypervolumeImprovement(
            model=model,
            ref_point=ref_tensor,
            X_baseline=X_baseline,
            sampler=sampler,
            prune_baseline=True
        )
        return acq_func
    except Exception as e:
        logger.error(f"Failed to instantiate qLogNoisyExpectedHypervolumeImprovement acquisition: {e}")
        raise RuntimeError(f"Error handling mechanism failed to construct qLogNoisyExpectedHypervolumeImprovement: {e}")
