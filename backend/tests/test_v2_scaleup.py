import pytest
from fastapi.testclient import TestClient
from main import app
from schemas.shared_db_schemas import ProfileCard, ThermalLimits, PowderMetrics

client = TestClient(app)

def test_v2_scaleup_endpoint():
    # 1. Setup Request Payload Matching the Schema
    payload = {
        "profile": {
            "api_name": "Paracetamol",
            "thermal_limits": {
                "glass_transition_temp_c": 75.0,
                "decomposition_temp_c": 180.0,
                "melting_point_c": 150.0
            },
            "powder_metrics": {
                "carrs_index": 22.0,
                "hausner_ratio": 1.2,
                "true_density_g_ml": 1.4,
                "particle_size_d50_um": 120.0
            }
        },
        "lab_params": {
            "impeller_rpm": 400.0,
            "compression_force_kn": 12.0,
            "drying_temp_c": 50.0,
            "spray_rate_g_min": 15.0
        },
        "lab_machine_id": "lab_granulator_10L",
        "comm_machine_id": "commercial_granulator_300L"
    }

    # 2. Call the Scale-Up API Router Endpoint
    response = client.post("/v2/scaleup", json=payload)
    
    # 3. Assert Response Validity and Mathematical Correctness
    assert response.status_code == 200
    data = response.json()
    
    assert "commercial_params" in data
    assert "reynolds_number" in data
    assert "reynolds_warning" in data
    assert "scaling_law_used" in data
    assert "scaleup_confidence" in data
    
    comm_params = data["commercial_params"]
    assert comm_params["impeller_rpm"] > 0
    assert comm_params["compression_force_kn"] > 0
    assert comm_params["drying_temp_c"] == 50.0 # drying temp should carry over directly
    assert comm_params["batch_size_kg"] == 150.0 # 300L bowl volume * 50% fill ratio = 150 kg
    assert comm_params["spray_rate_g_min"] == 450.0 # 15 g/min * (300L / 10L) = 450 g/min
