from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from schemas.shared_db_schemas import ProfileCard, ScaleupCommercialParams
from engines.hybrid_twin import run_scaleup_calculation

router = APIRouter(prefix="/v2", tags=["Vector 2 - Scale-Up"])

class ScaleupRequest(BaseModel):
    profile: ProfileCard
    lab_params: dict
    lab_machine_id: str = "lab_granulator_10L"
    comm_machine_id: str = "commercial_granulator_300L"

class ScaleupResponse(BaseModel):
    commercial_params: ScaleupCommercialParams
    reynolds_number: float
    reynolds_warning: bool
    scaling_law_used: str
    scaleup_confidence: str

@router.post("/scaleup", response_model=ScaleupResponse)
def scaleup_endpoint(req: ScaleupRequest):
    """
    Computes scaled-up commercial manufacturing process parameters using
    mechanistic Froude scaling coupled with a pre-trained ML residual corrector layer.
    """
    try:
        density = req.profile.powder_metrics.true_density_g_ml
        carrs = req.profile.powder_metrics.carrs_index
        
        calc = run_scaleup_calculation(
            api_name=req.profile.api_name,
            true_density_g_ml=density,
            carrs_index=carrs,
            lab_params=req.lab_params,
            lab_machine_id=req.lab_machine_id,
            comm_machine_id=req.comm_machine_id
        )
        
        comm_params = ScaleupCommercialParams(
            impeller_rpm=calc["impeller_rpm"],
            compression_force_kn=calc["compression_force_kn"],
            drying_temp_c=calc["drying_temp_c"],
            inlet_air_humidity_pct_rh=calc["inlet_air_humidity_pct_rh"],
            dwell_time_ms=calc["dwell_time_ms"],
            batch_size_kg=calc["batch_size_kg"],
            spray_rate_g_min=calc["spray_rate_g_min"]
        )
        
        return ScaleupResponse(
            commercial_params=comm_params,
            reynolds_number=calc["reynolds_number"],
            reynolds_warning=calc["reynolds_warning"],
            scaling_law_used=calc["scaling_law_used"],
            scaleup_confidence=calc["scaleup_confidence"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scaleup calculation error: {str(e)}")
