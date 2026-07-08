import os
import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
import xgboost as xgb

def train_models():
    print("Training models for EnFormis Module 3...")
    os.makedirs("models", exist_ok=True)
    
    # 1. Train scale-up residual corrector
    print("Training Scale-up Residual Corrector (RandomForest)...")
    scaleup_df = pd.read_csv("data/scaleup_synthetic_data.csv")
    X_su = scaleup_df[["delta_volume", "true_density", "carrs_index"]]
    y_su = scaleup_df["delta_rpm"]
    
    corrector = RandomForestRegressor(n_estimators=50, random_state=42)
    corrector.fit(X_su, y_su)
    
    corrector_path = "models/v2_residual_corrector.pkl"
    with open(corrector_path, "wb") as f:
        pickle.dump(corrector, f)
    print(f"✓ Trained and saved scale-up corrector to {corrector_path}")
    
    # 2. Train 5 XGBoost classifiers
    print("Training Failure Classifiers (5 XGBoost models)...")
    failure_df = pd.read_csv("data/failure_synthetic_data.csv")
    
    feature_cols = [
        "carrs_index", "true_density", "particle_size_d50",
        "impeller_rpm", "compression_force_kn", "drying_temp_c",
        "moisture_pct", "binder_pct"
    ]
    X_fail = failure_df[feature_cols]
    
    failure_modes = ["capping", "sticking", "lamination", "overdrying", "crystallisation"]
    classifiers = {}
    
    for fm in failure_modes:
        print(f"  Training XGBoost for {fm}...")
        y_fm = failure_df[fm]
        
        # Use simple parameters for fast and robust training
        clf = xgb.XGBClassifier(
            n_estimators=30,
            max_depth=3,
            learning_rate=0.1,
            random_state=42,
            eval_metric="logloss"
        )
        clf.fit(X_fail, y_fm)
        classifiers[fm] = clf
        
    classifiers_path = "models/v3_failure_classifier.pkl"
    with open(classifiers_path, "wb") as f:
        pickle.dump(classifiers, f)
    print(f"✓ Trained and saved 5 XGBoost failure classifiers to {classifiers_path}")
    print("Model training completed successfully!")

if __name__ == '__main__':
    train_models()
