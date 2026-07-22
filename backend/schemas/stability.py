from pydantic import BaseModel, Field
from typing import List
from constants import (
    DEFAULT_STABILITY_SCORE, DEFAULT_STABILITY_CATEGORY,
    DEFAULT_PRIMARY_RISK_MODE, DEFAULT_SECONDARY_RISK_MODE
)

class StabilityProfile(BaseModel):
    """5 params"""
    stability_score: float = DEFAULT_STABILITY_SCORE
    stability_category: str = DEFAULT_STABILITY_CATEGORY
    primary_risk_mode: str = DEFAULT_PRIMARY_RISK_MODE
    secondary_risk_mode: str = DEFAULT_SECONDARY_RISK_MODE
    main_risk_drivers: List[str] = Field(default_factory=list)
