from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal, Dict
from datetime import datetime

# ==========================================
# SUB-MODELS FOR EXPANDED 71 PARAMETERS (TEAM ALPHA)
# ==========================================

class IonizationFractions(BaseModel):
    """5 pH environments × 5 sub-metrics = 25 params"""
    ph_1_2: dict = Field(default_factory=dict)    # {pka_nearest, f_neutral, f_acidic, f_basic, f_zwitterion}
    ph_5_5: dict = Field(default_factory=dict)
    ph_6_5: dict = Field(default_factory=dict)
    ph_6_8: dict = Field(default_factory=dict)
    ph_7_4: dict = Field(default_factory=dict)

class SolubilityProfile(BaseModel):
    """6 params"""
    log_s_intrinsic: float = -3.5
    log_s_ph_1_2: float = -3.2
    log_s_ph_5_5: float = -3.4
    log_s_ph_6_5: float = -3.5
    log_s_ph_6_8: float = -3.6
    log_s_ph_7_4: float = -3.8

class PermeabilityProfile(BaseModel):
    """3 params"""
    log_pe: float = -5.0
    caco2_papp: float = 12.5
    pampa_pe: float = 8.4

class SolidStateRisk(BaseModel):
    """9 params"""
    polymorphic_risk_score: float = 0.2
    polymorphic_risk_tier: str = "low"          # "low", "medium", "high"
    crystallisation_difficulty: float = 0.3
    amorphous_propensity: float = 0.1
    recrystallisation_risk: float = 0.15
    hygroscopicity_class: str = "moderately_hygroscopic"
    hygroscopicity_auc: float = 0.45
    hydrate_formation_risk: float = 0.1
    thermal_degradation_risk: float = 0.05

class StabilityProfile(BaseModel):
    """5 params"""
    stability_score: float = 0.95
    stability_category: str = "stable"
    primary_risk_mode: str = "none"
    secondary_risk_mode: str = "none"
    main_risk_drivers: List[str] = Field(default_factory=list)

class CorePhysicochemical(BaseModel):
    """17 params"""
    molecular_weight: float = 300.0
    log_p: float = 2.5
    log_d_ph_6_5: float = 2.1
    log_d_ph_6_8: float = 2.0
    log_d_ph_7_4: float = 1.8
    pka_list: List[float] = Field(default_factory=list)
    polyprotic: bool = False
    amphoteric: bool = False
    zwitterionic: bool = False
    charge_ph_7_4: float = 0.0
    tpsa: float = 75.0
    hbd: int = 2
    hba: int = 4
    rotatable_bonds: int = 5
    ring_count: int = 2
    mw_descriptor: str = "medium"
    fsp3: float = 0.45

# ==========================================
# MODULE 1 INPUT (ProfileCard)
# ==========================================

class ThermalLimits(BaseModel):
    glass_transition_temp_c: float
    decomposition_temp_c: float
    melting_point_c: Optional[float] = 150.0
    polymorph_conversion_temp: Optional[float] = 82.0

class PowderMetrics(BaseModel):
    carrs_index: float
    hausner_ratio: float
    true_density_g_ml: float
    particle_size_d50_um: float

class ProfileCard(BaseModel):
    api_name: str
    canonical_smiles: str = ""               # Structural identity (1 param)
    bcs_class: str = "II"                    # Biopharm classification (1 param)
    dose_number: float = 1.0                 # Dose (1 param)
    thermal_limits: ThermalLimits            # Tg, Decomp Onset + Melting Point (3 params)
    powder_metrics: PowderMetrics            # 4 params
    core_physicochemical: Optional[CorePhysicochemical] = None    # 17 params
    ionization_fractions: Optional[IonizationFractions] = None    # 25 params
    solubility: Optional[SolubilityProfile] = None                # 6 params
    permeability: Optional[PermeabilityProfile] = None            # 3 params
    solid_state_risk: Optional[SolidStateRisk] = None             # 9 params
    stability: Optional[StabilityProfile] = None                  # 5 params

# ==========================================
# MODULE 2 INPUT (StrategyCard)
# ==========================================

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
