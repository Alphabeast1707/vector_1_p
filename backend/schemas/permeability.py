from pydantic import BaseModel
from constants import DEFAULT_LOG_PE, DEFAULT_CACO2_PAPP, DEFAULT_PAMPA_PE

class PermeabilityProfile(BaseModel):
    """3 params"""
    log_pe: float = DEFAULT_LOG_PE
    caco2_papp: float = DEFAULT_CACO2_PAPP
    pampa_pe: float = DEFAULT_PAMPA_PE
