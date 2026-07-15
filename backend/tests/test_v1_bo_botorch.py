import pytest
import numpy as np
from schemas.shared_db_schemas import ProfileCard, StrategyCard, ThermalLimits, PowderMetrics, Excipient, CQATargets
from engines.domain_builder import build_domain
from engines.bo_loop import ActiveLearningLoop

def test_botorch_active_learning_loop():
    print("test_botorch_active_learning_loop started")
    # 1. Setup mock data
    profile = ProfileCard(
        api_name="TestAPI",
        thermal_limits=ThermalLimits(glass_transition_temp_c=75.0, decomposition_temp_c=180.0),
        powder_metrics=PowderMetrics(carrs_index=22.0, hausner_ratio=1.2, true_density_g_ml=1.4, particle_size_d50_um=120.0)
    )
    
    strategy = StrategyCard(
        excipients=[
            Excipient(name="Lactose", role="filler", concentration_min_pct=10.0, concentration_max_pct=45.0),
            Excipient(name="MCC", role="binder", concentration_min_pct=15.0, concentration_max_pct=50.0),
            Excipient(name="MagStearate", role="lubricant", concentration_min_pct=0.5, concentration_max_pct=2.0)
        ],
        cqa_targets=CQATargets(
            dissolution_q30_min_pct=85.0,
            hardness_min_kp=6.0,
            hardness_max_kp=12.0,
            friability_max_pct=0.8,
            content_uniformity_min_pct=95.0,
            content_uniformity_max_pct=105.0,
            heckel_slope_min=0.08,
            heckel_slope_max=0.15
        )
    )
    
    print("Domain and loop built")
    domain = build_domain(profile, strategy)
    loop = ActiveLearningLoop(domain, strategy)
    
    # 2. Test seeds (first 3 suggest_next calls)
    print("Generating seeds...")
    seeds = [loop.suggest_next() for _ in range(3)]
    print("Seeds generated")
    for seed in seeds:
        assert isinstance(seed, dict)
        assert "binder_pct" in seed
        assert "Lactose_pct" in seed
        assert "MCC_pct" in seed
        assert "MagStearate_pct" in seed
        
        # Verify bounds constraint
        assert 2.0 <= seed["binder_pct"] <= 6.0
        assert 10.0 <= seed["Lactose_pct"] <= 45.0
        
        # Verify mass-balance
        excip_sum = seed["binder_pct"] + seed["Lactose_pct"] + seed["MCC_pct"] + seed["MagStearate_pct"]
        assert excip_sum <= 70.001
        
    # 3. Add 4 mock results to trigger the GP fitting & optimization
    print("Adding mock experiments...")
    n_inputs = len(domain.inputs)
    n_outputs = len(domain.outputs)
    
    for i in range(4):
        # random inputs within bounds
        x = [float(np.random.uniform(inp.bounds[0], inp.bounds[1])) for inp in domain.inputs]
        # random outputs
        y = [
            float(np.random.uniform(60.0, 95.0)), # q15
            float(np.random.uniform(70.0, 98.0)), # q30
            float(np.random.uniform(80.0, 100.0)), # q45
            float(np.random.uniform(85.0, 100.0)), # q60
            float(np.random.uniform(70.0, 110.0)), # hardness
            float(np.random.uniform(0.1, 1.2)), # friability
            float(np.random.uniform(96.0, 104.0)), # CU
            float(np.random.uniform(0.09, 0.14)) # heckel
        ]
        loop.add_experiment_result(x, y)
    print("Mock experiments added.")
        
    # 4. Suggest next via BoTorch optimization
    print("Suggesting next config via BoTorch...")
    suggestion = loop.suggest_next()
    print("Suggestion generated successfully:", suggestion)
    assert isinstance(suggestion, dict)
    
    # Check all parameters are in suggestion
    for inp in domain.inputs:
        assert inp.key in suggestion
        lower, upper = inp.bounds
        assert lower - 1e-6 <= suggestion[inp.key] <= upper + 1e-6
        
    # Check mass-balance
    excip_sum = suggestion["binder_pct"] + suggestion["Lactose_pct"] + suggestion["MCC_pct"] + suggestion["MagStearate_pct"]
    assert excip_sum <= 70.001

if __name__ == "__main__":
    test_botorch_active_learning_loop()
    print("Test passed successfully!")
