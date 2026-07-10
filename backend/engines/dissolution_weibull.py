import numpy as np
from scipy.optimize import curve_fit

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
    try:
        y = np.log(-np.log(1.0 - diss_fraction))
        x = np.log(times)
        slope, intercept = np.polyfit(x, y, 1)
        beta_init = max(0.1, slope)
        eta_init = np.exp(-intercept / beta_init)
    except Exception:
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
    except Exception:
        eta_fit, beta_fit = eta_init, beta_init
        
    # Calculate R-squared
    residuals = dissolution - weibull_model(times, eta_fit, beta_fit)
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((dissolution - np.mean(dissolution)) ** 2)
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
    
    return float(eta_fit), float(beta_fit), float(r_squared)
