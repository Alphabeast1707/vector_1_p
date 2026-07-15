import torch
from botorch.models import SingleTaskGP
from gpytorch.kernels import MaternKernel, ScaleKernel

def create_gp_model(train_X: torch.Tensor, train_Y: torch.Tensor) -> SingleTaskGP:
    """
    Initializes a Gaussian Process (GP) surrogate model using a Product covariance kernel:
    K(X, X') = K_active(X_active, X'_active) * K_static(X_static, X'_static)
    where active dimensions represent process/formulation parameters and static dimensions
    represent thermodynamic/physical API descriptors.
    """
    # Heuristically separate active dimensions from static descriptors using variance
    variances = train_X.var(dim=0)
    # A column is static if its variance is extremely small (e.g., < 1e-6)
    static_mask = variances < 1e-6
    static_indices = torch.where(static_mask)[0].tolist()
    active_indices = torch.where(~static_mask)[0].tolist()
    
    if len(static_indices) > 0 and len(active_indices) > 0:
        # Product kernel for transfer learning / physical context integration
        active_kernel = MaternKernel(nu=2.5, active_dims=torch.tensor(active_indices, dtype=torch.long))
        static_kernel = MaternKernel(nu=2.5, active_dims=torch.tensor(static_indices, dtype=torch.long))
        covar_module = ScaleKernel(active_kernel * static_kernel)
        model = SingleTaskGP(train_X, train_Y, covar_module=covar_module)
    else:
        # Fallback to standard high-performance ScaleKernel(MaternKernel) with ARD
        model = SingleTaskGP(train_X, train_Y)
        
    return model

