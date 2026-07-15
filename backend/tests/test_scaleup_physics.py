import pytest
from engines.scaleup_physics import compute_scaleup_metrics

def test_scaleup_dimensionless_numbers():
    # Test lab scale calculations
    scale_factor = 5.0 # scaling up from lab (1kg) to pilot (5kg)
    metrics = compute_scaleup_metrics(
        impeller_speed_rpm=300.0,
        impeller_diameter_m=0.1,
        scale_factor=scale_factor
    )
    
    # Fr = (omega^2 * R) / g
    # omega = 300 * 2pi / 60 = 31.4159 rad/s
    # R = 0.05 m
    # Fr = (31.4159^2 * 0.05) / 9.81 = 5.034
    assert pytest.approx(metrics["froude_number_lab"], abs=1e-2) == 5.03
    
    # Scaleup speed under constant Froude scaling: N_pilot = N_lab * (1 / scale_factor)^0.5
    assert pytest.approx(metrics["target_pilot_speed_rpm"], abs=1e-1) == 134.16
