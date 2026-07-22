from pydantic import BaseModel, Field
from typing import List, Optional
from schemas.excipient import Excipient

class CQATargets(BaseModel):
    dissolution_q30_min_pct: float
    hardness_min_kp: float
    hardness_max_kp: float
    friability_max_pct: float
    content_uniformity_min_pct: float = 95.0
    content_uniformity_max_pct: float = 105.0
    heckel_slope_min: float = 0.08
    heckel_slope_max: float = 0.15

class StrategyCard(BaseModel):
    excipients: List[Excipient]
    cqa_targets: CQATargets
    # --- NEW EXCIPIENT PIPELINE OPTIONS ---
    formulation_technique: str = "wet_granulation"
    alternative_techniques: List[str] = Field(default_factory=list)
    desirability_weights: Optional[dict] = None   # per-CQA weighting for EHVI
    formulation_strategy: str = ""
