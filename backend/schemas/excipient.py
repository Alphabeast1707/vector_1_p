from pydantic import BaseModel
from typing import Optional

class Excipient(BaseModel):
    name: str
    role: str                               # "binder", "filler", "lubricant", etc.
    concentration_min_pct: float
    concentration_max_pct: float
    # --- NEW: Team Beta excipient characterization (25 params) ---
    hsp_dispersive: Optional[float] = 18.0
    hsp_polar: Optional[float] = 6.0
    hsp_hydrogen: Optional[float] = 8.0
    hsp_total: Optional[float] = 20.0
    aqueous_solubility_mg_ml: Optional[float] = 10.0
    excipient_tg_c: Optional[float] = 120.0
    excipient_mw_kda: Optional[float] = 50.0
    excipient_hydrophilicity: Optional[float] = 0.5
    chi_parameter: Optional[float] = 0.2    # Flory-Huggins
    compatibility_score: Optional[float] = 0.85
    moisture_stability: Optional[float] = 0.9
    polymorphic_risk: Optional[float] = 0.1
    is_most_compatible: Optional[bool] = True
    shap_impact: Optional[float] = 0.05
