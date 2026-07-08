import math

def calculate_froude(rpm: float, diameter_m: float) -> float:
    # Fr = N^2 * D / g where N is rps (revolutions per second)
    rps = rpm / 60.0
    g = 9.81
    return (rps ** 2) * diameter_m / g

def calculate_reynolds(density_g_ml: float, rpm: float, diameter_m: float, viscosity_pas: float = 0.1) -> float:
    # Re = rho * N * D^2 / mu
    # Convert density from g/ml to kg/m3 (1 g/ml = 1000 kg/m3)
    rho = density_g_ml * 1000.0
    rps = rpm / 60.0
    return rho * rps * (diameter_m ** 2) / viscosity_pas

def scale_by_froude(rpm_lab: float, diameter_lab: float, diameter_comm: float) -> float:
    # N2 = N1 * sqrt(D_lab / D_comm)
    return rpm_lab * math.sqrt(diameter_lab / diameter_comm)

def scale_by_tip_speed(rpm_lab: float, diameter_lab: float, diameter_comm: float) -> float:
    # N2 = N1 * (D_lab / D_comm)
    return rpm_lab * (diameter_lab / diameter_comm)
