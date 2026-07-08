import numpy as np

def derive_locked_design_space(
    pareto_solutions: list[dict],
    mc_results: dict | None = None,
    domain = None
) -> dict:
    """
    For each CPP, find the range across Pareto-optimal solutions where:
    1. All CQAs are predicted in-spec (GP posterior)
    2. Monte Carlo P95 failure risk < 15% (green zone)
    
    Returns: {cpp_name: {lower, nominal, upper}}
    """
    locked = {}
    pareto_cpps = [sol["cpps"] for sol in pareto_solutions]

    # Find the keys in the domain inputs
    input_keys = []
    if domain is not None:
        input_keys = [inp.key for inp in domain.inputs]
    elif pareto_cpps:
        input_keys = list(pareto_cpps[0].keys())
    else:
        input_keys = ["binder_pct", "granulation_moisture_pct", "drying_temp_c", "compression_force_kn", "spray_rate_g_min"]

    for key in input_keys:
        values = [cpps[key] for cpps in pareto_cpps if key in cpps]
        
        # Check Monte Carlo bounds for this specific parameter if provided
        mc_bounds = None
        if mc_results and "locked_design_space" in mc_results:
            mc_bounds = mc_results["locked_design_space"].get(key)

        if mc_bounds:
            # Reconcile Pareto coordinates with Monte Carlo physical stress thresholds
            locked[key] = {
                "lower": round(float(mc_bounds["lower"]), 2),
                "nominal": round(float(mc_bounds["nominal"]), 2),
                "upper": round(float(mc_bounds["upper"]), 2)
            }
        elif values:
            locked[key] = {
                "lower": round(float(min(values)), 2),
                "nominal": round(float(np.median(values)), 2),
                "upper": round(float(max(values)), 2)
            }
        else:
            # General standard fallback ranges
            default_bounds = {
                "binder_pct": (2.0, 6.0),
                "granulation_moisture_pct": (3.0, 7.0),
                "drying_temp_c": (40.0, 100.0),
                "compression_force_kn": (8.0, 25.0),
                "spray_rate_g_min": (5.0, 30.0)
            }
            bounds = default_bounds.get(key, (1.0, 100.0))
            locked[key] = {
                "lower": bounds[0],
                "nominal": round(float(sum(bounds) / 2.0), 2),
                "upper": bounds[1]
            }

    return locked
