from pydantic import BaseModel, Field
from typing import List
from constants import (
    DEFAULT_MOLECULAR_WEIGHT, DEFAULT_LOG_P, DEFAULT_LOG_D_PH_6_5,
    DEFAULT_LOG_D_PH_6_8, DEFAULT_LOG_D_PH_7_4, DEFAULT_TPSA,
    DEFAULT_HBD, DEFAULT_HBA, DEFAULT_ROTATABLE_BONDS, DEFAULT_RING_COUNT,
    DEFAULT_MW_DESCRIPTOR, DEFAULT_FSP3
)

class CorePhysicochemical(BaseModel):
    """17 params"""
    molecular_weight: float = DEFAULT_MOLECULAR_WEIGHT
    log_p: float = DEFAULT_LOG_P
    log_d_ph_6_5: float = DEFAULT_LOG_D_PH_6_5
    log_d_ph_6_8: float = DEFAULT_LOG_D_PH_6_8
    log_d_ph_7_4: float = DEFAULT_LOG_D_PH_7_4
    pka_list: List[float] = Field(default_factory=list)
    polyprotic: bool = False
    amphoteric: bool = False
    zwitterionic: bool = False
    charge_ph_7_4: float = 0.0
    tpsa: float = DEFAULT_TPSA
    hbd: int = DEFAULT_HBD
    hba: int = DEFAULT_HBA
    rotatable_bonds: int = DEFAULT_ROTATABLE_BONDS
    ring_count: int = DEFAULT_RING_COUNT
    mw_descriptor: str = DEFAULT_MW_DESCRIPTOR
    fsp3: float = DEFAULT_FSP3
