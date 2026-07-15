import pytest
import numpy as np
from engines.dissolution_weibull import fit_weibull_profile

def test_weibull_exact_fit():
    # True parameters: scale (eta) = 30.0 mins, shape (beta) = 1.2
    # Dissolution fraction F(t) = 100 * (1 - exp(-(t/eta)^beta))
    times = np.array([15.0, 30.0, 45.0, 60.0])
    true_eta = 30.0
    true_beta = 1.2
    dissolution_values = 100.0 * (1.0 - np.exp(-((times / true_eta) ** true_beta)))
    
    eta, beta, r_squared = fit_weibull_profile(times, dissolution_values)
    
    assert pytest.approx(eta, abs=1e-2) == true_eta
    assert pytest.approx(beta, abs=1e-2) == true_beta
    assert r_squared > 0.99
