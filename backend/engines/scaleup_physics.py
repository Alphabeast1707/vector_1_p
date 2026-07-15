import math

def compute_scaleup_metrics(impeller_speed_rpm: float, impeller_diameter_m: float, scale_factor: float) -> dict:
    """
    Computes dimensionless mixing metrics to scale-up granulator process parameters.
    Uses classical Froude scaling (Fr_lab = Fr_pilot) as standard.
    """
    g = 9.81 # m/s^2
    omega_lab = (impeller_speed_rpm * 2 * math.pi) / 60.0
    radius_lab = impeller_diameter_m / 2.0
    
    # Froude number (dimensionless ratio of inertial to gravitational forces)
    froude_lab = (omega_lab ** 2 * radius_lab) / g
    
    # Tip speed (m/s)
    tip_speed_lab = omega_lab * radius_lab
    
    # Target Pilot Impeller Speed (RPM) under constant Froude scaling
    target_pilot_speed = impeller_speed_rpm * (1.0 / math.sqrt(scale_factor))
    
    return {
        "froude_number_lab": froude_lab,
        "tip_speed_lab_m_s": tip_speed_lab,
        "target_pilot_speed_rpm": target_pilot_speed,
        "scale_up_froude_match_ratio": 1.0 # 1:1 Froude scaling target
    }
