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
    # Inputs: delta_volume (L), true_density (g/ml), carrs_index
    # Target: delta_rpm (deviation from mechanistic scale-up)
    delta_volume = np.random.uniform(50.0, 500.0, n_samples)
    true_density = np.random.uniform(0.8, 1.6, n_samples)
    carrs_index = np.random.uniform(10.0, 30.0, n_samples)
    
    # True relationship: higher density and higher carrs_index requires slightly higher RPM adjustment
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
    # Inputs:
    # - carrs_index (10 to 30)
    # - true_density (0.8 to 1.6)
    # - particle_size_d50 (50 to 250 um)
    # - impeller_rpm (50 to 300)
    # - compression_force_kn (5 to 30)
    # - drying_temp_c (40 to 110)
    # - moisture_pct (2.0 to 8.0)
    # - binder_pct (1.5 to 7.0)
    c_index = np.random.uniform(10.0, 30.0, n_samples)
    density = np.random.uniform(0.8, 1.6, n_samples)
    d50 = np.random.uniform(50.0, 250.0, n_samples)
    rpm = np.random.uniform(50.0, 300.0, n_samples)
    force = np.random.uniform(5.0, 30.0, n_samples)
    dry_temp = np.random.uniform(40.0, 110.0, n_samples)
    moisture = np.random.uniform(2.0, 8.0, n_samples)
    binder = np.random.uniform(1.5, 7.0, n_samples)
    
    # Define failure probabilities following pharma logic
    # Sticking risk increases with high moisture and low binder or low force
    sticking_prob = 1 / (1 + np.exp(-(0.5 * moisture - 0.3 * binder - 0.1 * force + 0.1 * c_index - 2.0)))
    sticking_label = (sticking_prob > np.random.uniform(0, 1, n_samples)).astype(int)
    
    # Capping risk increases with high compression force, low binder, and high carrs_index
    capping_prob = 1 / (1 + np.exp(-(0.4 * force - 0.6 * binder + 0.15 * c_index - 5.0)))
    capping_label = (capping_prob > np.random.uniform(0, 1, n_samples)).astype(int)
    
    # Lamination risk increases with extremely high force and low moisture
    lamination_prob = 1 / (1 + np.exp(-(0.5 * force - 0.8 * moisture - 4.0)))
    lamination_label = (lamination_prob > np.random.uniform(0, 1, n_samples)).astype(int)
    
    # Overdrying risk increases with high drying temp and low moisture
    overdrying_prob = 1 / (1 + np.exp(-(0.15 * dry_temp - 0.8 * moisture - 5.0)))
    overdrying_label = (overdrying_prob > np.random.uniform(0, 1, n_samples)).astype(int)
    
    # Crystallisation risk increases with high drying temp and low true_density
    crystallisation_prob = 1 / (1 + np.exp(-(0.12 * dry_temp - 2.5 * density - 2.0)))
    crystallisation_label = (crystallisation_prob > np.random.uniform(0, 1, n_samples)).astype(int)
    
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
    print("Synthetic data generation finished successfully!")

if __name__ == '__main__':
    generate_synthetic_data()
