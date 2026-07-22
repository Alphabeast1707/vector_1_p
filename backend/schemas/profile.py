from pydantic import BaseModel
from typing import Optional
from schemas.ionization import IonizationFractions
from schemas.solubility import SolubilityProfile
from schemas.permeability import PermeabilityProfile
from schemas.solid_state import SolidStateRisk
from schemas.stability import StabilityProfile
from schemas.physicochemical import CorePhysicochemical
from schemas.thermal import ThermalLimits
from schemas.powder import PowderMetrics

class ProfileCard(BaseModel):
    api_name: str
    canonical_smiles: str = ""               # Structural identity (1 param)
    bcs_class: str = "II"                    # Biopharm classification (1 param)
    dose_number: float = 1.0                 # Dose (1 param)
    thermal_limits: ThermalLimits            # Tg, Decomp Onset + Melting Point (3 params)
    powder_metrics: PowderMetrics            # 4 params
    core_physicochemical: Optional[CorePhysicochemical] = None    # 17 params
    ionization_fractions: Optional[IonizationFractions] = None    # 25 params
    solubility: Optional[SolubilityProfile] = None                # 6 params
    permeability: Optional[PermeabilityProfile] = None            # 3 params
    solid_state_risk: Optional[SolidStateRisk] = None             # 9 params
    stability: Optional[StabilityProfile] = None                  # 5 params
