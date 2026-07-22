from pydantic import BaseModel
from constants import (
    DEFAULT_LOG_S_INTRINSIC, DEFAULT_LOG_S_PH_1_2, DEFAULT_LOG_S_PH_5_5,
    DEFAULT_LOG_S_PH_6_5, DEFAULT_LOG_S_PH_6_8, DEFAULT_LOG_S_PH_7_4
)

class SolubilityProfile(BaseModel):
    """6 params"""
    log_s_intrinsic: float = DEFAULT_LOG_S_INTRINSIC
    log_s_ph_1_2: float = DEFAULT_LOG_S_PH_1_2
    log_s_ph_5_5: float = DEFAULT_LOG_S_PH_5_5
    log_s_ph_6_5: float = DEFAULT_LOG_S_PH_6_5
    log_s_ph_6_8: float = DEFAULT_LOG_S_PH_6_8
    log_s_ph_7_4: float = DEFAULT_LOG_S_PH_7_4
