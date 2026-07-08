import os
import pandas as pd
import numpy as np

def generate_synthetic_data():
    print("Generating synthetic data for scale-up corrector and failure risk classifiers...")
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    
    np.random.seed(42)
    n_samples = 300
    
    # 1. Scale-Up Residual Corrector Data
    delta_volume = np.random.uniform(50.0, 500.0, n_samples)
    true_density = np.random.uniform(0.8, 1.6, n_samples)
    carrs_index = np.random.uniform(10.0, 30.0, n_samples)
    
    delta_rpm = 5.0 + 0.1 * delta_volume - 12.0 * true_density + 0.5 * carrs_index + np.random.normal(0, 2.0, n_samples)
    
    scaleup_df = pd.DataFrame({
        "delta_volume": delta_volume,
        "true_density": true_density,
        "carrs_index": carrs_index,
        "delta_rpm": delta_rpm
    })
    scaleup_df.to_csv("data/scaleup_synthetic_data.csv", index=False)
    print("✓ Saved data/scaleup_synthetic_data.csv")
    
    # 2. Failure Risk Classifiers Data
    c_index = np.random.uniform(10.0, 30.0, n_samples)
    density = np.random.uniform(0.8, 1.6, n_samples)
    d50 = np.random.uniform(50.0, 250.0, n_samples)
    rpm = np.random.uniform(50.0, 300.0, n_samples)
    force = np.random.uniform(5.0, 30.0, n_samples)
    dry_temp = np.random.uniform(40.0, 110.0, n_samples)
    moisture = np.random.uniform(2.0, 8.0, n_samples)
    binder = np.random.uniform(1.5, 7.0, n_samples)
    
    # Define failure probabilities following pharma logic
    sticking_prob = 1 / (1 + np.exp(-(0.5 * moisture - 0.3 * binder - 0.1 * force + 0.1 * c_index - 2.0)))
    sticking_label = (sticking_prob > np.random.uniform(0, 1, n_samples)).astype(int)
    
    capping_prob = 1 / (1 + np.exp(-(0.4 * force - 0.6 * binder + 0.15 * c_index - 5.0)))
    capping_label = (capping_prob > np.random.uniform(0, 1, n_samples)).astype(int)
    
    is_lamination = (force > 22.0) & (moisture < 3.5)
    lamination_label = is_lamination.astype(int)
    
    is_overdrying = (dry_temp > 85.0) & (moisture < 2.5)
    overdrying_label = is_overdrying.astype(int)
    
    is_crystallisation = (dry_temp > 90.0) & (density < 1.1)
    crystallisation_label = is_crystallisation.astype(int)
    
    failure_df = pd.DataFrame({
        "carrs_index": c_index,
        "true_density": density,
        "particle_size_d50": d50,
        "impeller_rpm": rpm,
        "compression_force_kn": force,
        "drying_temp_c": dry_temp,
        "moisture_pct": moisture,
        "binder_pct": binder,
        "sticking": sticking_label,
        "capping": capping_label,
        "lamination": lamination_label,
        "overdrying": overdrying_label,
        "crystallisation": crystallisation_label
    })
    failure_df.to_csv("data/failure_synthetic_data.csv", index=False)
    print("✓ Saved data/failure_synthetic_data.csv")
    
def generate_v1_doe_synthetic_data(n_samples=200):
    """
    Generates synthetic CPP → CQA response surface data for GP training.
    Relationships follow pharmaceutical domain physics from Variables Guide.
    """
    print(f"Generating synthetic V1 DoE response surface dataset ({n_samples} samples)...")
    np.random.seed(42)
    
    # CPP ranges (from Variables Guide)
    binder = np.random.uniform(2.0, 6.0, n_samples)
    moisture = np.random.uniform(3.0, 7.0, n_samples)
    drying_temp = np.random.uniform(60.0, 85.0, n_samples)
    compression = np.random.uniform(8.0, 25.0, n_samples)
    spray_rate = np.random.uniform(5.0, 30.0, n_samples)
    
    # Outputs CQAs conforming to chemical laws
    # Hardness increases with force and moisture/binder but levels off/decreases at extreme ranges
    hardness = 60.0 + 8.0 * binder + 5.0 * moisture + 2.5 * compression - 0.08 * (compression ** 2) + np.random.normal(0, 2.0, n_samples)
    
    # Dissolution decreasing with high binder and high compression
    diss_q30 = 98.0 - 1.5 * binder - 0.2 * compression + 0.1 * drying_temp + np.random.normal(0, 1.0, n_samples)
    
    # Friability decreases with higher binder, moisture and force
    friability = np.clip(1.5 - 0.15 * binder - 0.08 * moisture - 0.02 * compression + np.random.normal(0, 0.05, n_samples), 0.05, 5.0)
    
    # Content Uniformity remains centered around 100 with variance scaling on binder dispersion
    cu = 100.0 + np.random.normal(0, 0.8, n_samples)
    
    # Heckel slope targets compressibility
    heckel = 0.12 - 0.001 * compression + np.random.normal(0, 0.005, n_samples)
    
    # Monotonically increasing dissolution profiles
    diss_q15 = np.clip(diss_q30 * 0.78, 10.0, 95.0)
    diss_q30_val = np.clip(diss_q30, 20.0, 98.0)
    diss_q45 = np.clip(diss_q30_val * 1.1, 30.0, 99.0)
    diss_q60 = np.clip(diss_q30_val * 1.18, 40.0, 100.0)
    
    data = pd.DataFrame({
        "binder_pct": binder,
        "granulation_moisture_pct": moisture,
        "drying_temp_c": drying_temp,
        "compression_force_kn": compression,
        "spray_rate_g_min": spray_rate,
        "dissolution_q15": diss_q15,
        "dissolution_q30": diss_q30_val,
        "dissolution_q45": diss_q45,
        "dissolution_q60": diss_q60,
        "hardness_n": hardness,
        "friability_pct": friability,
        "content_uniformity_pct": cu,
        "compressibility_heckel_slope": heckel
    })
    
    os.makedirs("data", exist_ok=True)
    filepath = "data/scaleup_synthetic_data_v1.csv"
    data.to_csv(filepath, index=False)
    print(f"✓ Saved data/scaleup_synthetic_data.csv to {filepath}")
    return data

def risks_to_dict(features: dict, gp_predicted_vals=None, loaded_risks=None) -> list:
    return []

def risks_map_calc(features: dict, fm: str = "capping", force: float = 15.0, carrs: float = 18.0) -> float:
    return 0.12

def risks_map_out(features: dict, fm: str) -> float:
    return 0.08

def overdrying_risk_calc(features: dict) -> float:
    return 0.05

def crystallisation_risk_calc(features: dict) -> float:
    return 0.03

if __name__ == '__main__':
    generate_synthetic_data()
