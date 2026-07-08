import os
import pickle
import numpy as np

ENGINES_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(ENGINES_DIR)
MODEL_PATH = os.path.join(BACKEND_DIR, "models", "v3_failure_classifier.pkl")

class FailureClassifier:
    def __init__(self):
        self.models = None
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, "rb") as f:
                self.models = pickle.load(f)
        else:
            print(f"Warning: Failure classifiers model not found at {MODEL_PATH}")

    def predict_risks(self, features: dict) -> dict:
        # Features keys:
        # [carrs_index, true_density, particle_size_d50, impeller_rpm, compression_force_kn, drying_temp_c, moisture_pct, binder_pct]
        feature_order = [
            "carrs_index", "true_density", "particle_size_d50",
            "impeller_rpm", "compression_force_kn", "drying_temp_c",
            "moisture_pct", "binder_pct"
        ]
        X = np.array([[features[k] for k in feature_order]])

        risks = {}
        failure_modes = ["capping", "sticking", "lamination", "overdrying", "crystallisation"]
        
        for fm in failure_modes:
            if self.models is not None and fm in self.models:
                # Get prediction probability of class 1
                prob = float(self.models[fm].predict_proba(X)[0][1])
            else:
                # Heuristic fallbacks if model not loaded
                prob = 0.1
                if fm == "sticking" and features["moisture_pct"] > 6.0:
                    prob = 0.35
                elif fm == "capping" and features["compression_force_kn"] > 18.0:
                    prob = 0.45
            risks[fm] = round(prob, 4)
            
        return risks
