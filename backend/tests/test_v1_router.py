import pytest
from schemas.shared_db_schemas import ProfileCard, StrategyCard, ThermalLimits, PowderMetrics, Excipient, CQATargets
from routers.v1_bayesian_doe import initialize_domain, add_result, suggest_next_experiment, get_session_summary, active_loops

def test_v1_bayesian_doe_handlers():
    # 1. Setup request payload cards
    profile = ProfileCard(
        api_name="Paracetamol",
        thermal_limits=ThermalLimits(
            glass_transition_temp_c=75.0,
            decomposition_temp_c=180.0
        ),
        powder_metrics=PowderMetrics(
            carrs_index=22.0,
            hausner_ratio=1.2,
            true_density_g_ml=1.4,
            particle_size_d50_um=120.0
        )
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
    
    session_id = "test_router_session"
    
    # 2. Call initialize_domain handler
    init_res = initialize_domain(profile, strategy, session_id=session_id)
    assert init_res["message"] == "Domain initialized"
    assert "initial_suggestions" in init_res
    assert len(init_res["initial_suggestions"]) == 3
    
    # 3. Call add_result handler 4 times
    x_params = {
        "binder_pct": 4.0,
        "granulation_moisture_pct": 5.0,
        "drying_temp_c": 50.0,
        "compression_force_kn": 12.0,
        "spray_rate_g_min": 15.0,
        "Lactose_pct": 20.0,
        "MCC_pct": 30.0,
        "MagStearate_pct": 1.0
    }
    y_results = {
        "dissolution_q15": 70.0,
        "dissolution_q30": 82.0,
        "dissolution_q45": 90.0,
        "dissolution_q60": 95.0,
        "hardness_n": 95.0,
        "friability_pct": 0.5,
        "content_uniformity_pct": 98.0,
        "compressibility_heckel_slope": 0.12
    }
    
    for _ in range(4):
        res_res = add_result(x_params, y_results, session_id=session_id)
        assert res_res["message"] == "Result added successfully"
        
    # 4. Call suggest_next_experiment handler
    sug_res = suggest_next_experiment(session_id=session_id)
    assert "suggestion" in sug_res
    suggestion = sug_res["suggestion"]
    assert "binder_pct" in suggestion
    assert "granulation_moisture_pct" in suggestion
    assert "Lactose_pct" in suggestion
    
    # 5. Call get_session_summary and verify the schema version is 1.1 and horizons block exists
    summary_res = get_session_summary(session_id=session_id)
    assert summary_res["schema_version"] == "1.1"
    assert "analytical_horizons" in summary_res
    horizons = summary_res["analytical_horizons"]
    assert "weibull_dissolution_fits" in horizons
    assert "dimensionless_scaleup_metrics" in horizons
    
    # Verify scale-up calculations
    scaleup = horizons["dimensionless_scaleup_metrics"]
    assert "froude_number_lab" in scaleup
    assert "target_pilot_speed_rpm" in scaleup
    
    # Clean up
    active_loops.pop(session_id, None)
