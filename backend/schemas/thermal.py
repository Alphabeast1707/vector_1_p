from pydantic import BaseModel
from typing import Optional

class ThermalLimits(BaseModel):
    glass_transition_temp_c: float
    decomposition_temp_c: float
    melting_point_c: Optional[float] = 150.0
    polymorph_conversion_temp: Optional[float] = None
