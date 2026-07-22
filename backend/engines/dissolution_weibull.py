import logging
import numpy as np
from scipy.optimize import curve_fit

logger = logging.getLogger("vector_1.dissolution_weibull")

def weibull_model(t, eta, beta):
    """Weibull cumulative dissolution equation: F(t) = 100 * (1 - exp(-(t/eta)^beta))"""
    return 100.0 * (1.0 - np.exp(-((t / eta) ** beta)))

def fit_weibull_profile(times: np.ndarray, dissolution: np.ndarray) -> tuple[float, float, float]:
    """
    Fits multi-point dissolution data to the Weibull equation using non-linear least squares.
    Returns:
        eta (scale parameter, mins)
        beta (shape parameter, dimensionless)
        r_squared (goodness of fit)
    """
    # Safeguard inputs
    times = np.asfarray(times)
    dissolution = np.asfarray(dissolution)
    
    # Clip dissolution to prevent log-domain errors during least squares initialization
    diss_fraction = np.clip(dissolution / 100.0, 0.001, 0.999)
    
    # Initial guess using linearized log-log conversion: ln(-ln(1 - F)) = beta * ln(t) - beta * ln(eta)
    # The try-except is mandatory here because:
    # 1. Zero values in times will cause np.log(times) division-by-zero (inf).
    # 2. Complete dissolution values of 1.0 (or clipped fraction >= 1.0) cause np.log(-np.log(0)) nan errors.
    # 3. Noisy lab data can have non-monotonic slopes causing polyfit to raise RankWarnings or fail.
    try:
        y = np.log(-np.log(1.0 - diss_fraction))
        x = np.log(times)
        slope, intercept = np.polyfit(x, y, 1)
        beta_init = max(0.1, slope)
        eta_init = np.exp(-intercept / beta_init)
    except Exception as e:
        logger.exception(f"Linearized initialization of Weibull curve parameters failed: {e}. Falling back to default values.")
        beta_init = 1.0
        eta_init = 30.0

    # Non-linear curve fitting for high precision
    try:
        popt, pcov = curve_fit(
            weibull_model, times, dissolution, 
            p0=[eta_init, beta_init], 
            bounds=((1.0, 0.1), (180.0, 5.0))
        )
        eta_fit, beta_fit = popt
    except Exception as e:
        logger.error(f"Non-linear Weibull curve fitting failed: {e}")
        # Log exception and propagate to other layers as requested by code review
        raise RuntimeError(f"Non-linear Weibull curve fitting failed due to numerical instability: {e}")
        
    # Calculate R-squared
    try:
        residuals = dissolution - weibull_model(times, eta_fit, beta_fit)
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((dissolution - np.mean(dissolution)) ** 2)
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
    except Exception as e:
        logger.warning(f"Failed to calculate R-squared goodness-of-fit metric: {e}. Defaulting to 1.0.")
        r_squared = 1.0
    
    return float(eta_fit), float(beta_fit), float(r_squared)
