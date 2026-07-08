import pytest
from schemas.shared_db_schemas import ProfileCard, StrategyCard, ThermalLimits, PowderMetrics, Excipient, CQATargets
from engines.domain_builder import build_domain

def test_domain_builder_thermal_constraints():
    # Mock data from Module 1
    profile = ProfileCard(
        api_name="TestAPI",
        thermal_limits=ThermalLimits(glass_transition_temp_c=65.0, decomposition_temp_c=120.0),
        powder_metrics=PowderMetrics(carrs_index=28.0, hausner_ratio=1.3, true_density_g_ml=1.5, particle_size_d50_um=150.0)
    )
    
    # Mock data from Module 2
    strategy = StrategyCard(
        excipients=[
            Excipient(name="MCC", role="binder", concentration_min_pct=20.0, concentration_max_pct=50.0),
            Excipient(name="MagStearate", role="lubricant", concentration_min_pct=0.5, concentration_max_pct=2.0)
        ],
        cqa_targets=CQATargets(
            dissolution_q30_min_pct=80.0,
            hardness_min_kp=8.0,
            hardness_max_kp=12.0,
            friability_max_pct=1.0
        )
    )
    
    domain = build_domain(profile, strategy)
    
    # Verify drying temp is constrained to Tg - 10
    drying_temp_input = next(i for i in domain.inputs if i.key == "drying_temp_c")
    assert drying_temp_input.bounds == (40.0, 55.0) # 65.0 - 10
    
    # Verify excipient dynamically added
    mcc_input = next(i for i in domain.inputs if i.key == "MCC_pct")
    assert mcc_input.bounds == (20.0, 50.0)
    
    assert len(domain.inputs) == 7 # 5 process + 2 excipients
    assert len(domain.outputs) == 8 # 8 CQAs

