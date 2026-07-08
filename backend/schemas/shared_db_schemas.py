from pydantic import BaseModel
from typing import List
from datetime import datetime

# ==========================================
# MODULE 1 INPUT (ProfileCard)
# ==========================================
class ThermalLimits(BaseModel):
    glass_transition_temp_c: float
    decomposition_temp_c: float

class PowderMetrics(BaseModel):
    carrs_index: float
    hausner_ratio: float
    true_density_g_ml: float
    particle_size_d50_um: float

class ProfileCard(BaseModel):
    api_name: str
    thermal_limits: ThermalLimits
    powder_metrics: PowderMetrics

# ==========================================
# MODULE 2 INPUT (StrategyCard)
# ==========================================
class Excipient(BaseModel):
    name: str
    role: str
    concentration_min_pct: float
    concentration_max_pct: float

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

# ==========================================
# MODULE 3 OUTPUT (ProcessDevelopmentCard)
# ==========================================
class DissolutionProfile(BaseModel):
    q15_pct: float
    q30_pct: float
    q45_pct: float
    q60_pct: float
    highest_dissolution_driver: str

class PredictedCQAMetrics(BaseModel):
    hardness_n: float
    friability_pct: float
    content_uniformity_pct: float
    compressibility_heckel_slope: float
    dissolution_profile: DissolutionProfile

class ScaleupCommercialParams(BaseModel):
    impeller_rpm: float
    compression_force_kn: float
    drying_temp_c: float
    inlet_air_humidity_pct_rh: float
    dwell_time_ms: float
    batch_size_kg: float
    spray_rate_g_min: float

class AuditFailureRisks(BaseModel):
    capping: float
    sticking: float
    lamination: float
    overdrying_risk: float
    crystallisation_risk: float

class ProcessDevelopmentCard(BaseModel):
    drug_id: str
    api_name: str
    version: str
    created_at: datetime
    pipeline_status: str

    # Vector 1
    optimal_formulation: dict
    lab_process_params: dict
    experiments_used: int
    predicted_cqa: PredictedCQAMetrics

    # Vector 2
    commercial_params: ScaleupCommercialParams
    scaling_law_used: str
    scaleup_confidence: str

    # Vector 3
    failure_risks: AuditFailureRisks
    risk_levels: dict
    locked_design_space: dict
    shap_explanations: dict
    proceed_recommendation: str

