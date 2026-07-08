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

@router.get("/history")
def get_experiment_history(session_id: str = "default"):
    """
    Returns all experiments with CPP inputs and CQA outputs.
    """
    if session_id not in active_loops:
        raise HTTPException(status_code=400, detail="Session not found")
    loop = active_loops[session_id]
    return {
        "n_experiments": len(loop.history_X),
        "experiments": [
            {"x": x, "y": y}
            for x, y in zip(loop.history_X, loop.history_Y)
        ]
    }

@router.get("/pareto")
def get_pareto_front(session_id: str = "default"):
    """
    Returns current Pareto-optimal solutions with CQA predictions.
    """
    if session_id not in active_loops:
        raise HTTPException(status_code=400, detail="Session not found")
    loop = active_loops[session_id]
    return {
        "n_pareto": len(loop.pareto_solutions),
        "pareto_solutions": loop.pareto_solutions,
        "hypervolume_history": loop.hypervolume_history
    }

@router.get("/convergence")
def check_convergence_status(session_id: str = "default"):
    """
    Checks whether the optimization loop has converged.
    """
    if session_id not in active_loops:
        raise HTTPException(status_code=400, detail="Session not found")
    loop = active_loops[session_id]
    return loop.check_convergence()

@router.get("/summary")
def get_session_summary(session_id: str = "default"):
    """
    Returns complete Phase 1 summary for export to Team Delta.
    """
    if session_id not in active_loops:
        raise HTTPException(status_code=400, detail="Session not found")
    loop = active_loops[session_id]
    convergence = loop.check_convergence()
    return {
        "schema_version": "1.0",
        "api_name": loop.domain.api_name if hasattr(loop.domain, 'api_name') else "unknown",
        "n_seed_experiments": loop.seed_count,
        "n_total_experiments": len(loop.history_X),
        "n_pareto_solutions": len(loop.pareto_solutions),
        "loo_cv_r2": loop.compute_loo_cv_r2(),
        "converged": convergence["converged"]
    }
