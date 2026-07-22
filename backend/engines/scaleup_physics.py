import math
from pydantic import BaseModel

class ScaleupMetrics(BaseModel):
    """
    Combines the physical scale-up calculations and the output object structure
    using Froude scaling (Fr_lab = Fr_pilot) as standard.
    """
    impeller_speed_rpm: float
    impeller_diameter_m: float
    scale_factor: float

    @property
    def omega_lab(self) -> float:
        return (self.impeller_speed_rpm * 2.0 * math.pi) / 60.0

    @property
    def radius_lab(self) -> float:
        return self.impeller_diameter_m / 2.0

    @property
    def froude_number_lab(self) -> float:
        g = 9.81  # m/s^2
        return (self.omega_lab ** 2 * self.radius_lab) / g

    @property
    def tip_speed_lab_m_s(self) -> float:
        return self.omega_lab * self.radius_lab

    @property
    def target_pilot_speed_rpm(self) -> float:
        return self.impeller_speed_rpm * (1.0 / math.sqrt(self.scale_factor))

    @property
    def scale_up_froude_match_ratio(self) -> float:
        return 1.0  # 1:1 Froude scaling target

    def to_dict(self) -> dict:
        """Returns the calculated metrics as a dictionary for router output."""
        return {
            "froude_number_lab": self.froude_number_lab,
            "tip_speed_lab_m_s": self.tip_speed_lab_m_s,
            "target_pilot_speed_rpm": self.target_pilot_speed_rpm,
            "scale_up_froude_match_ratio": self.scale_up_froude_match_ratio
        }

def compute_scaleup_metrics(impeller_speed_rpm: float, impeller_diameter_m: float, scale_factor: float) -> dict:
    """
    Legacy wrapper function to maintain backwards compatibility with routers.
    """
    metrics = ScaleupMetrics(
        impeller_speed_rpm=impeller_speed_rpm,
        impeller_diameter_m=impeller_diameter_m,
        scale_factor=scale_factor
    )
    return metrics.to_dict()
