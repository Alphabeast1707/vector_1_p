import os
import pickle
import numpy as np

# Resolve path dynamically
ENGINES_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(ENGINES_DIR)
MODEL_PATH = os.path.join(BACKEND_DIR, "models", "v2_residual_corrector.pkl")

class ResidualCorrector:
    def __init__(self):
        self.model = None
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, "rb") as f:
                self.model = pickle.load(f)
        else:
            print(f"Warning: Residual corrector model not found at {MODEL_PATH}")

    def predict_correction(self, delta_volume_l: float, true_density_g_ml: float, carrs_index: float) -> float:
        if self.model is None:
            # Simple fallback heuristic
            return 5.0 + 0.1 * delta_volume_l - 12.0 * true_density_g_ml + 0.5 * carrs_index
        
        X = np.array([[delta_volume_l, true_density_g_ml, carrs_index]])
        return float(self.model.predict(X)[0])
