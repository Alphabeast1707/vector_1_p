import torch
import logging
from botorch.acquisition import AcquisitionFunction

logger = logging.getLogger("vector_1.cost_aware_acquisition")

class CostAwareAcquisition(AcquisitionFunction):
    """
    Cost-Aware Acquisition Function that weights base acquisition values
    by drying temperature processing costs and API material usage.
    """
    def __init__(
        self,
        acq_func,
        exc_indices: list[int],
        lower_bounds: list[float],
        upper_bounds: list[float],
        temp_lower: float = 40.0,
        temp_upper: float = 80.0,
        gamma: float = 0.15,
        v_context: list[float] | None = None
    ):
        super().__init__(acq_func.model)
        self.acq_func = acq_func
        self.exc_indices = exc_indices
        self.lower_bounds = lower_bounds
        self.upper_bounds = upper_bounds
        self.temp_lower = temp_lower
        self.temp_upper = temp_upper
        self.gamma = gamma
        self.v_context = v_context
        
    def forward(self, X: torch.Tensor) -> torch.Tensor:
        # X shape: (..., q, D) -- typically (b, 1, D) for q=1
        
        # Intercept and append physical context columns if provided, avoiding degenerate/fixed bounds during acquisition optimization
        if self.v_context is not None:
            try:
                context_tensor = torch.tensor(self.v_context, dtype=X.dtype, device=X.device)
                batch_shape = X.shape[:-2]
                q_dim = X.shape[-2]
                context_expanded = context_tensor.view(1, 1, -1).expand(*batch_shape, q_dim, len(self.v_context))
                X_combined = torch.cat([X, context_expanded], dim=-1)
            except Exception as e:
                logger.error(f"Failed to concatenate context columns in CostAwareAcquisition: {e}")
                X_combined = X
        else:
            X_combined = X

        try:
            base_val = self.acq_func(X_combined)
        except Exception as e:
            logger.error(f"Evaluation of base acquisition function failed: {e}")
            raise RuntimeError(f"Base acquisition function evaluation error: {e}")
        
        # Compute physical process cost at candidate coordinates
        # Drying temp is index 2 of Critical Process Parameters
        try:
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
        except Exception as e:
            logger.warning(f"Cost calculation failed: {e}. Returning unpenalized base value.")
            return base_val
