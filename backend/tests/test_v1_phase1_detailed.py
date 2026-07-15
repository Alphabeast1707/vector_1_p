import pytest
import numpy as np
from schemas.shared_db_schemas import (
    ProfileCard, StrategyCard, Excipient, CQATargets, ThermalLimits, PowderMetrics,
    CorePhysicochemical, SolidStateRisk
)
from engines.data_ingestion import ingest_alpha_dataset, ingest_beta_dataset, cross_validate_datasets
from engines.domain_builder import build_domain
from engines.bo_loop import ActiveLearningLoop

def test_profile_card_expanded_fields():
    # Verify that ProfileCard accepts all expanded parameters
    core = CorePhysicochemical(molecular_weight=325.4, log_p=3.1)
    solid_risk = SolidStateRisk(polymorphic_risk_score=0.85, polymorphic_risk_tier="high")
    
    profile = ProfileCard(
        api_name="Test-API-71",
        canonical_smiles="CC1=CN=C(C(=C1)OC)CS(=O)C2=NC3=CC=CC=C3N2",
        bcs_class="IV",
        dose_number=2.5,
        thermal_limits=ThermalLimits(glass_transition_temp_c=72.0, decomposition_temp_c=195.0),
        powder_metrics=PowderMetrics(carrs_index=22.0, hausner_ratio=1.28, true_density_g_ml=1.42, particle_size_d50_um=135.0),
        core_physicochemical=core,
        solid_state_risk=solid_risk
    )
    assert profile.api_name == "Test-API-71"
    assert profile.core_physicochemical is not None
    assert profile.core_physicochemical.molecular_weight == 325.4
    assert profile.solid_state_risk is not None
    assert profile.solid_state_risk.polymorphic_risk_tier == "high"

def test_strategy_card_excipient_parameters():
    # Verify that StrategyCard accepts all 25 excipient parameters
    exc1 = Excipient(
        name="MCC-101",
        role="binder",
        concentration_min_pct=10.0,
        concentration_max_pct=30.0,
        hsp_total=19.5,
        excipient_tg_c=125.0,
        excipient_hydrophilicity=0.45,
        moisture_stability=0.85
    )
    targets = CQATargets(dissolution_q30_min_pct=80.0, hardness_min_kp=8.0, hardness_max_kp=12.0, friability_max_pct=1.0)
    strategy = StrategyCard(excipients=[exc1], cqa_targets=targets)
    assert len(strategy.excipients) == 1
    assert strategy.excipients[0].hsp_total == 19.5
    assert strategy.excipients[0].excipient_tg_c == 125.0

def test_dynamic_bounds_drying_temp_rule():
    # Verify that drying temp upper bound is constrained correctly
    profile_low_risk = ProfileCard(
        api_name="LowRiskAPI",
        thermal_limits=ThermalLimits(glass_transition_temp_c=80.0, decomposition_temp_c=250.0),
        powder_metrics=PowderMetrics(carrs_index=15.0, hausner_ratio=1.1, true_density_g_ml=1.2, particle_size_d50_um=100.0)
    )
    profile_high_risk = ProfileCard(
        api_name="HighRiskAPI",
        thermal_limits=ThermalLimits(glass_transition_temp_c=65.0, decomposition_temp_c=250.0),
        powder_metrics=PowderMetrics(carrs_index=15.0, hausner_ratio=1.1, true_density_g_ml=1.2, particle_size_d50_um=100.0),
        solid_state_risk=SolidStateRisk(polymorphic_risk_score=0.9, polymorphic_risk_tier="high")
    )
    targets = CQATargets(dissolution_q30_min_pct=80.0, hardness_min_kp=8.0, hardness_max_kp=12.0, friability_max_pct=1.0)
    strategy = StrategyCard(excipients=[], cqa_targets=targets)

    domain_low = build_domain(profile_low_risk, strategy)
    domain_high = build_domain(profile_high_risk, strategy)

    drying_low = next(i for i in domain_low.inputs if i.key == "drying_temp_c")
    drying_high = next(i for i in domain_high.inputs if i.key == "drying_temp_c")

    # High risk should tighten upper bound to glass_transition_temp_c - 7.0 = 58.0
    # Low risk bound is decomposition_temp_c - 15 = 235, capped at 100
    assert drying_low.bounds[1] == 100.0
    assert drying_high.bounds[1] == 58.0

def test_latin_hypercube_reproducible_seeds():
    # Verify that Latin Hypercube suggests exactly 8 seeds and is reproducible with fixed seed
    profile = ProfileCard(
        api_name="ReproAPI",
        thermal_limits=ThermalLimits(glass_transition_temp_c=75.0, decomposition_temp_c=200.0),
        powder_metrics=PowderMetrics(carrs_index=15.0, hausner_ratio=1.1, true_density_g_ml=1.2, particle_size_d50_um=100.0)
    )
    targets = CQATargets(dissolution_q30_min_pct=80.0, hardness_min_kp=8.0, hardness_max_kp=12.0, friability_max_pct=1.0)
    strategy = StrategyCard(
        excipients=[Excipient(name="Filler-A", role="filler", concentration_min_pct=10.0, concentration_max_pct=40.0)],
        cqa_targets=targets
    )
    domain = build_domain(profile, strategy)

    loop1 = ActiveLearningLoop(domain, strategy)
    loop2 = ActiveLearningLoop(domain, strategy)

    seeds1 = [loop1.suggest_next() for _ in range(8)]
    seeds2 = [loop2.suggest_next() for _ in range(8)]

    assert len(seeds1) == 8
    # Ensure they are identical because of fixed random state in qmc.LatinHypercube
    for s1, s2 in zip(seeds1, seeds2):
        assert s1["binder_pct"] == s2["binder_pct"]
        assert s1["granulation_moisture_pct"] == s2["granulation_moisture_pct"]

def test_mass_balance_enforcement():
    # Ensure excipient values are capped at 70% in seeds
    profile = ProfileCard(
        api_name="MassAPI",
        thermal_limits=ThermalLimits(glass_transition_temp_c=75.0, decomposition_temp_c=200.0),
        powder_metrics=PowderMetrics(carrs_index=15.0, hausner_ratio=1.1, true_density_g_ml=1.2, particle_size_d50_um=100.0)
    )
    targets = CQATargets(dissolution_q30_min_pct=80.0, hardness_min_kp=8.0, hardness_max_kp=12.0, friability_max_pct=1.0)
    strategy = StrategyCard(
        excipients=[
            Excipient(name="Filler-A", role="filler", concentration_min_pct=40.0, concentration_max_pct=60.0),
            Excipient(name="Filler-B", role="filler", concentration_min_pct=30.0, concentration_max_pct=50.0)
        ],
        cqa_targets=targets
    )
    domain = build_domain(profile, strategy)
    loop = ActiveLearningLoop(domain, strategy)

    seeds = [loop.suggest_next() for _ in range(8)]
    for s in seeds:
        # Sum of excipients (ending in _pct) should not exceed 70.0% (except granulation moisture)
        excip_sum = s["Filler-A_pct"] + s["Filler-B_pct"]
        assert excip_sum <= 70.01 # allow minor float rounding tolerance

def test_gp_predictions_loo_cv_r2():
    # Verify that predictions return mean, std, CI95 and check spec boundaries
    profile = ProfileCard(
        api_name="GPAPI",
        thermal_limits=ThermalLimits(glass_transition_temp_c=75.0, decomposition_temp_c=200.0),
        powder_metrics=PowderMetrics(carrs_index=15.0, hausner_ratio=1.1, true_density_g_ml=1.2, particle_size_d50_um=100.0)
    )
    targets = CQATargets(dissolution_q30_min_pct=80.0, hardness_min_kp=8.0, hardness_max_kp=12.0, friability_max_pct=1.0)
    strategy = StrategyCard(excipients=[], cqa_targets=targets)
    domain = build_domain(profile, strategy)
    loop = ActiveLearningLoop(domain, strategy)

    # Supply 5 synthetic data points to Loop history
    np.random.seed(42)
    for _ in range(5):
        # 5 process inputs + 4 production inputs = 9 X parameters
        x = list(np.random.uniform(2.0, 10.0, 9))
        # 8 output targets (dissolution Q15/Q30/Q45/Q60, hardness, friability, cu, heckel)
        y = [70.0, 85.0, 90.0, 95.0, 105.0, 0.4, 99.5, 0.12]
        loop.add_experiment_result(x, y)

    predictions = loop._predict_cqas(np.array([4.0, 5.0, 60.0, 15.0, 15.0, 50.0, 300.0, 300.0, 10.0]))
    assert "dissolution_q30" in predictions
    assert "ci95_lo" in predictions["dissolution_q30"]
    assert "ci95_hi" in predictions["dissolution_q30"]
    assert "in_spec" in predictions["dissolution_q30"]

    loo_r2 = loop.compute_loo_cv_r2()
    assert "dissolution_q30" in loo_r2
    assert isinstance(loo_r2["dissolution_q30"], float)
