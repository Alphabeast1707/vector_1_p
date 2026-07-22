from pydantic import BaseModel, Field

class IonizationFractions(BaseModel):
    """5 pH environments × 5 sub-metrics = 25 params"""
    ph_1_2: dict = Field(default_factory=dict)    # {pka_nearest, f_neutral, f_acidic, f_basic, f_zwitterion}
    ph_5_5: dict = Field(default_factory=dict)
    ph_6_5: dict = Field(default_factory=dict)
    ph_6_8: dict = Field(default_factory=dict)
    ph_7_4: dict = Field(default_factory=dict)
