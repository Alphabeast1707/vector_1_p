from fastapi import APIRouter, HTTPException
from schemas.shared_db_schemas import ProfileCard, StrategyCard
from engines.domain_builder import build_domain
from engines.bo_loop import ActiveLearningLoop

router = APIRouter(prefix="/v1", tags=["Vector 1 - DoE"])

# In a real app, this would be persisted in PostgreSQL or Redis.
# We store it in memory for the prototype.
active_loops = {}

@router.post("/domain")
def initialize_domain(profile: ProfileCard, strategy: StrategyCard, session_id: str = "default"):
    """
    Initializes the search space and returns 3 initial seed experiments (LHS).
    """
    domain = build_domain(profile, strategy)
    active_loops[session_id] = ActiveLearningLoop(domain, strategy)
    
    # Suggest 3 initial points
    suggestions = [active_loops[session_id].suggest_next() for _ in range(3)]
    return {"message": "Domain initialized", "initial_suggestions": suggestions}

@router.post("/experiments/result")
def add_result(x_params: dict, y_results: dict, session_id: str = "default"):
    """
    Accepts physical lab results from the scientist.
    """
    if session_id not in active_loops:
        raise HTTPException(status_code=400, detail="Domain not initialized for this session")
    
    loop = active_loops[session_id]
    loop.add_experiment_result(list(x_params.values()), list(y_results.values()))
    return {"message": "Result added successfully"}

@router.post("/suggest")
def suggest_next_experiment(session_id: str = "default"):
    """
    Suggests the single next best experiment using EHVI.
    """
    if session_id not in active_loops:
        raise HTTPException(status_code=400, detail="Domain not initialized for this session")
    
    loop = active_loops[session_id]
    suggestion = loop.suggest_next()
    return {"suggestion": suggestion}
