import torch
from botorch.models import SingleTaskGP
from gpytorch.kernels import MaternKernel, ScaleKernel

def create_gp_model(train_X: torch.Tensor, train_Y: torch.Tensor) -> SingleTaskGP:
    """
    Initializes a Gaussian Process (GP) surrogate model using a Matérn 5/2 kernel.
    """
    # Use the robustly pre-configured default SingleTaskGP from BoTorch
    # which uses a ScaleKernel wrapping a MaternKernel (nu=2.5) with automatic ARD and proper priors.
    model = SingleTaskGP(train_X, train_Y)
    return model
