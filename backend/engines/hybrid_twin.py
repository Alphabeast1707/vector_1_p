from engines.scaling_laws import scale_by_froude, scale_by_tip_speed, calculate_reynolds
from engines.equipment_db import get_equipment_spec
from engines.residual_corrector import ResidualCorrector

def run_scaleup_calculation(
    api_name: str,
    true_density_g_ml: float,
    carrs_index: float,
    lab_params: dict,
    lab_machine_id: str,
    comm_machine_id: str
) -> dict:
    spec_lab = get_equipment_spec(lab_machine_id)
    spec_comm = get_equipment_spec(comm_machine_id)

    v_lab = spec_lab["bowl_volume_l"]
    v_comm = spec_comm["bowl_volume_l"]
    d_lab = spec_lab["impeller_diameter_m"]
    d_comm = spec_comm["impeller_diameter_m"]

    rpm_lab = lab_params.get("impeller_rpm", 400.0)
    force_lab = lab_params.get("compression_force_kn", 12.0)
    temp_lab = lab_params.get("drying_temp_c", 50.0)
    spray_lab = lab_params.get("spray_rate_g_min", 15.0)

    # 1. Determine scaling law based on geometric similarity or default to Froude-similarity
    # Typically, scale by Froude to maintain equivalent liquid distribution unless tip speed is requested
    scale_strategy = "froude"
    rpm_comm_mechanistic = scale_by_froude(rpm_lab, d_lab, d_comm)

    # Calculate alternative tip speed RPM
    rpm_tip_speed = scale_by_tip_speed(rpm_lab, d_lab, d_comm)

    # 2. Add hybrid residual corrector machine-learning layer
    corrector = ResidualCorrector()
    delta_vol = v_comm - v_lab
    delta_rpm = corrector.predict_correction(delta_vol, true_density_g_ml, carrs_index)

    rpm_comm_final = min(spec_comm["max_rpm"], max(20.0, rpm_comm_mechanistic + delta_rpm))

    # 3. Perform turbulence (Reynolds) validation
    re_comm = calculate_reynolds(true_density_g_ml, rpm_comm_final, d_comm)
    re_warning = re_comm < 10000.0

    # 4. Calculate derived process parameters
    # Dwell time (ms) in die: inversely proportional to rpm + offset
    dwell_time = 15.0 + 300.0 / (rpm_comm_final / 60.0 + 1e-9)
    # Batch size (kg) based on volume (50% packing density fill ratio)
    batch_size = v_comm * 0.5
    # Spray rate (g/min) scale factor based on volumetric flow
    spray_rate = spray_lab * (v_comm / v_lab)

    return {
        "impeller_rpm": round(rpm_comm_final, 2),
        "compression_force_kn": round(force_lab * 1.15, 2), # standard 15% increase for industrial press scale-up
        "drying_temp_c": round(temp_lab, 2),
        "inlet_air_humidity_pct_rh": 40.0, # default standard room humidity setpoint
        "dwell_time_ms": round(dwell_time, 2),
        "batch_size_kg": round(batch_size, 2),
        "spray_rate_g_min": round(spray_rate, 2),
        "reynolds_number": round(re_comm, 2),
        "reynolds_warning": re_warning,
        "scaling_law_used": scale_strategy,
        "scaleup_confidence": "hybrid_corrected" if corrector.model is not None else "mechanistic_only"
    }
