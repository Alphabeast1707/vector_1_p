from pydantic import BaseModel
from constants import (
    DEFAULT_POLYMORPHIC_RISK_SCORE, DEFAULT_POLYMORPHIC_RISK_TIER,
    DEFAULT_CRYSTALLISATION_DIFFICULTY, DEFAULT_AMORPHOUS_PROPENSITY,
    DEFAULT_RECRYSTALLISATION_RISK, DEFAULT_HYGROSCOPICITY_CLASS,
    DEFAULT_HYGROSCOPICITY_AUC, DEFAULT_HYDRATE_FORMATION_RISK,
    DEFAULT_THERMAL_DEGRADATION_RISK
)

class SolidStateRisk(BaseModel):
    """9 params"""
    polymorphic_risk_score: float = DEFAULT_POLYMORPHIC_RISK_SCORE
    polymorphic_risk_tier: str = DEFAULT_POLYMORPHIC_RISK_TIER          # "low", "medium", "high"
    crystallisation_difficulty: float = DEFAULT_CRYSTALLISATION_DIFFICULTY
    amorphous_propensity: float = DEFAULT_AMORPHOUS_PROPENSITY
    recrystallisation_risk: float = DEFAULT_RECRYSTALLISATION_RISK
    hygroscopicity_class: str = DEFAULT_HYGROSCOPICITY_CLASS
    hygroscopicity_auc: float = DEFAULT_HYGROSCOPICITY_AUC
    hydrate_formation_risk: float = DEFAULT_HYDRATE_FORMATION_RISK
    thermal_degradation_risk: float = DEFAULT_THERMAL_DEGRADATION_RISK
