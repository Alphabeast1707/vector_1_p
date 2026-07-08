import numpy as np
from engines.failure_classifier import FailureClassifier

def run_monte_carlo_stress_test(
    base_features: dict,
    n_iterations: int = 500
) -> dict:
    np.random.seed(42)
    classifier = FailureClassifier()

    # CPP nominal points
    rpm_nom = base_features.get("impeller_rpm", 150.0)
    force_nom = base_features.get("compression_force_kn", 15.0)
    temp_nom = base_features.get("drying_temp_c", 65.0)
    moisture_nom = base_features.get("moisture_pct", 5.0)
    binder_nom = base_features.get("binder_pct", 4.0)

    # 1. Generate perturbations (N = 500)
    rpm_pert = np.random.normal(rpm_nom, 10.0, n_iterations)
    force_pert = np.random.normal(force_nom, 1.2, n_iterations)
    temp_pert = np.random.normal(temp_nom, 2.5, n_iterations)
    moisture_pert = np.random.normal(moisture_nom, 0.3, n_iterations)
    binder_pert = np.random.normal(binder_nom, 0.2, n_iterations)

    # Hard-clip to physical limits
    rpm_pert = np.clip(rpm_pert, 20.0, 800.0)
    force_pert = np.clip(force_pert, 5.0, 35.0)
    temp_pert = np.clip(temp_pert, 30.0, 120.0)
    moisture_pert = np.clip(moisture_pert, 1.0, 9.0)
    binder_pert = np.clip(binder_pert, 1.0, 8.0)

    results = {
        "capping": [], "sticking": [], "lamination": [],
        "overdrying": [], "crystallisation": []
    }

    # Store configurations that are safe (all risks <= 0.25)
    safe_cpps = {
        "impeller_rpm": [], "compression_force_kn": [], "drying_temp_c": [],
        "moisture_pct": [], "binder_pct": []
    }

    for i in range(n_iterations):
        feat = base_features.copy()
        feat.update({
            "impeller_rpm": rpm_pert[i],
            "compression_force_kn": force_pert[i],
            "drying_temp_c": temp_pert[i],
            "moisture_pct": moisture_pert[i],
            "binder_pct": binder_pert[i]
        })
        
        risks = classifier.predict_risks(feat)
        is_safe = True
        for fm, risk in risks.items():
            results[fm].append(risk)
            if risk > 0.25:
                is_safe = False

        if is_safe:
            safe_cpps["impeller_rpm"].append(rpm_pert[i])
            safe_cpps["compression_force_kn"].append(force_pert[i])
            safe_cpps["drying_temp_c"].append(temp_pert[i])
            safe_cpps["moisture_pct"].append(moisture_pert[i])
            safe_cpps["binder_pct"].append(binder_pert[i])

    # Calculate statistics
    summary = {}
    for fm in results:
        arr = np.array(results[fm])
        summary[fm] = {
            "mean": round(float(arr.mean()), 4),
            "std": round(float(arr.std()), 4),
            "p95": round(float(np.percentile(arr, 95)), 4),
            "max": round(float(arr.max()), 4)
        }

    # Locked design space / Operating Windows
    locked_space = {}
    for cpp in safe_cpps:
        arr = np.array(safe_cpps[cpp])
        if len(arr) > 0:
            locked_space[cpp] = {
                "lower": round(float(arr.min()), 2),
                "upper": round(float(arr.max()), 2),
                "nominal": round(float(arr.mean()), 2)
            }
        else:
            # Fallback if no point is "perfectly safe" under limit
            locked_space[cpp] = {
                "lower": round(float(base_features[cpp] * 0.9), 2),
                "upper": round(float(base_features[cpp] * 1.1), 2),
                "nominal": round(float(base_features[cpp]), 2)
            }

    return {
        "summary": summary,
        "locked_design_space": locked_space,
        "n_perturbed": n_iterations
    }
