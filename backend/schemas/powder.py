from pydantic import BaseModel

class PowderMetrics(BaseModel):
    carrs_index: float
    hausner_ratio: float
    true_density_g_ml: float
    particle_size_d50_um: float
