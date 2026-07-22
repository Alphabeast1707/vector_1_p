# Constants for EnFormis Vector 1 - Bayesian Active Learning and DoE
# Consolidated into a single source of truth as requested by code review

# 1. Physical and Chemical Default Values (Profile Card / Team Alpha)
DEFAULT_LOG_S_INTRINSIC = -3.5
DEFAULT_LOG_S_PH_1_2 = -3.2
DEFAULT_LOG_S_PH_5_5 = -3.4
DEFAULT_LOG_S_PH_6_5 = -3.5
DEFAULT_LOG_S_PH_6_8 = -3.6
DEFAULT_LOG_S_PH_7_4 = -3.8

DEFAULT_LOG_PE = -5.0
DEFAULT_CACO2_PAPP = 12.5
DEFAULT_PAMPA_PE = 8.4

DEFAULT_POLYMORPHIC_RISK_SCORE = 0.2
DEFAULT_POLYMORPHIC_RISK_TIER = "low"
DEFAULT_CRYSTALLISATION_DIFFICULTY = 0.3
DEFAULT_AMORPHOUS_PROPENSITY = 0.1
DEFAULT_RECRYSTALLISATION_RISK = 0.15
DEFAULT_HYGROSCOPICITY_CLASS = "moderately_hygroscopic"
DEFAULT_HYGROSCOPICITY_AUC = 0.45
DEFAULT_HYDRATE_FORMATION_RISK = 0.1
DEFAULT_THERMAL_DEGRADATION_RISK = 0.05

DEFAULT_STABILITY_SCORE = 0.95
DEFAULT_STABILITY_CATEGORY = "stable"
DEFAULT_PRIMARY_RISK_MODE = "none"
DEFAULT_SECONDARY_RISK_MODE = "none"

DEFAULT_MOLECULAR_WEIGHT = 300.0
DEFAULT_LOG_P = 2.5
DEFAULT_LOG_D_PH_6_5 = 2.1
DEFAULT_LOG_D_PH_6_8 = 2.0
DEFAULT_LOG_D_PH_7_4 = 1.8
DEFAULT_TPSA = 75.0
DEFAULT_HBD = 2
DEFAULT_HBA = 4
DEFAULT_ROTATABLE_BONDS = 5
DEFAULT_RING_COUNT = 2
DEFAULT_MW_DESCRIPTOR = "medium"
DEFAULT_FSP3 = 0.45

# 2. Formulation Strategy and Search Space Bounds (Domain Builder / Team Beta)
BOUNDS_BINDER = (2.0, 6.0)
MOISTURE_MIN_DEFAULT = 3.0
MOISTURE_MAX_DEFAULT = 7.0
BOUNDS_COMPRESSION = (8.0, 25.0)
BOUNDS_SPRAY_RATE = (5.0, 30.0)

# 3. Scale-Up and Production Constraints
BOUNDS_BATCH_SCALE_KG = (1.0, 100.0)
BOUNDS_IMPELLER_SPEED_RPM = (150.0, 500.0)
BOUNDS_BLADE_SPEED_RPM = (150.0, 500.0)
BOUNDS_SCALE_FACTOR = (1.0, 20.0)

# 4. Standard Hardcoded Excipient Datasets (Beta Dataset Fallbacks)
DEFAULT_BETA_EXCIPIENTS = [
    {
        "name": "MCC-Avicel",
        "role": "binder",
        "concentration_min_pct": 15.0,
        "concentration_max_pct": 45.0,
        "hsp_dispersive": 18.0,
        "hsp_polar": 6.0,
        "hsp_hydrogen": 8.0,
        "hsp_total": 20.0,
        "aqueous_solubility_mg_ml": 10.0,
        "excipient_tg_c": 140.0,
        "excipient_mw_kda": 50.0,
        "excipient_hydrophilicity": 0.35,
        "chi_parameter": 0.2,
        "moisture_stability": 0.9
    },
    {
        "name": "Lactose",
        "role": "filler",
        "concentration_min_pct": 20.0,
        "concentration_max_pct": 50.0,
        "hsp_dispersive": 16.0,
        "hsp_polar": 12.0,
        "hsp_hydrogen": 14.0,
        "hsp_total": 25.0,
        "aqueous_solubility_mg_ml": 200.0,
        "excipient_tg_c": 101.0,
        "excipient_mw_kda": 0.342,
        "excipient_hydrophilicity": 0.6,
        "chi_parameter": 0.15,
        "moisture_stability": 0.8
    }
]

DEFAULT_BETA_PROCESS_PARAMS = {
    "granulation_liquid_pct": 12.5,
    "impeller_speed_rpm": 350.0,
    "granulation_time_min": 15.0,
    "drying_temp_c": 55.0
}
