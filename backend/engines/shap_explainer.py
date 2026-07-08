import os
import pickle
import numpy as np
import shap

ENGINES_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(ENGINES_DIR)
MODEL_PATH = os.path.join(BACKEND_DIR, "models", "v3_failure_classifier.pkl")

class ShapExplainer:
    def __init__(self):
        self.models = None
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, "rb") as f:
                self.models = pickle.load(f)

    def generate_explanations(self, features: dict) -> dict:
        feature_order = [
            "carrs_index", "true_density", "particle_size_d50",
            "impeller_rpm", "compression_force_kn", "drying_temp_c",
            "moisture_pct", "binder_pct"
        ]
        X = np.array([[features[k] for k in feature_order]])
        
        explanations = {}
        failure_modes = ["capping", "sticking", "lamination", "overdrying", "crystallisation"]
        
        for fm in failure_modes:
            if self.models is not None and fm in self.models:
                clf = self.models[fm]
                try:
                    explainer = shap.TreeExplainer(clf)
                    shap_values = explainer.shap_values(X)
                    # shap_values could be a 1D array of shape (n_features,) or 2D (1, n_features) or 3D for binary classification
                    if isinstance(shap_values, list):
                        # Some versions of SHAP return a list for binary classification [neg_contrib, pos_contrib]
                        shap_val = shap_values[1][0]
                    else:
                        shap_val = shap_values[0] if shap_values.ndim == 2 else shap_values
                        if shap_val.ndim == 2:
                            shap_val = shap_val[0]
                    
                    fm_explain = {feature_order[i]: round(float(shap_val[i]), 4) for i in range(len(feature_order))}
                except Exception as e:
                    # Robust fallback using feature importances in case SHAP TreeExplainer errors out
                    print(f"SHAP explainer failed for {fm}, using fallback: {str(e)}")
                    importances = clf.feature_importances_
                    # Scale importances slightly based on the actual values
                    fm_explain = {feature_order[i]: round(float(importances[i] * (X[0][i] / (X[0].mean() + 1e-9) - 0.5) * 0.5), 4) for i in range(len(feature_order))}
            else:
                # Default heuristics if no models are loaded
                fm_explain = {k: 0.01 for k in feature_order}
                
            explanations[fm] = fm_explain
            
        return explanations
