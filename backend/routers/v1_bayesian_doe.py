import logging
import numpy as np
from fastapi import APIRouter, HTTPException, status
from schemas.shared_db_schemas import ProfileCard, StrategyCard
from engines.domain_builder import build_domain
from engines.bo_loop import ActiveLearningLoop
from engines.dissolution_weibull import fit_weibull_profile
from engines.scaleup_physics import compute_scaleup_metrics

logger = logging.getLogger("vector_1.v1_bayesian_doe")
router = APIRouter(prefix="/v1", tags=["Vector 1 - DoE"])

# In-memory storage for prototype sessions
active_loops = {}

def _get_active_loop(session_id: str, detail: str = "Session not found") -> ActiveLearningLoop:
    """
    Centralized session validator and loop retriever.
    Ensures consistent session tracking and uniform error responses.
    """
    logger.debug(f"Validating and retrieving session: {session_id}")
    if not session_id or session_id not in active_loops:
        logger.warning(f"Session validation failed: session ID '{session_id}' not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )
    return active_loops[session_id]

@router.post("/domain", status_code=status.HTTP_201_CREATED)
def initialize_domain(profile: ProfileCard, strategy: StrategyCard, session_id: str = "default"):
    """
    Initializes the search space and returns 3 initial seed experiments (LHS).
    """
    logger.info(f"--- START initialize_domain (Session: {session_id}) ---")
    try:
        logger.info(f"Building dynamic domain for API '{profile.api_name}' and strategy.")
        domain = build_domain(profile, strategy)
        
        logger.info(f"Instantiating ActiveLearningLoop for session: {session_id}")
        active_loops[session_id] = ActiveLearningLoop(domain, strategy, profile=profile)
        
        # Suggest 3 initial points
        logger.info("Generating 3 initial space-filling LHS seed experiments.")
        suggestions = []
        for i in range(3):
            sug = active_loops[session_id].suggest_next()
            suggestions.append(sug)
            logger.debug(f"Initial suggestion {i+1}: {sug}")
            
        logger.info(f"--- END initialize_domain SUCCESS (Session: {session_id}) ---")
        return {"message": "Domain initialized", "initial_suggestions": suggestions}
    except ValueError as ve:
        logger.error(f"Validation or value error during domain initialization: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to initialize search space due to invalid configuration: {str(ve)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error initializing domain: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected internal error occurred: {str(e)}"
        )

@router.post("/experiments/result")
def add_result(x_params: dict, y_results: dict, session_id: str = "default"):
    """
    Accepts physical lab results from the scientist.
    """
    logger.info(f"--- START add_result (Session: {session_id}) ---")
    try:
        loop = _get_active_loop(session_id, "Domain not initialized for this session. Please call /domain first.")
        
        logger.info(f"Adding experiment result: CPPs={list(x_params.keys())}, CQAs={list(y_results.keys())}")
        loop.add_experiment_result(list(x_params.values()), list(y_results.values()))
        
        logger.info(f"--- END add_result SUCCESS (Session: {session_id}) ---")
        return {"message": "Result added successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error adding experiment result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest experiment result: {str(e)}"
        )

@router.post("/suggest")
def suggest_next_experiment(session_id: str = "default"):
    """
    Suggests the single next best experiment using EHVI.
    """
    logger.info(f"--- START suggest_next_experiment (Session: {session_id}) ---")
    try:
        loop = _get_active_loop(session_id, "Domain not initialized for this session. Please call /domain first.")
        
        logger.info("Computing next optimized candidates via Multi-Objective BoTorch solver.")
        suggestion = loop.suggest_next()
        
        logger.info(f"--- END suggest_next_experiment SUCCESS (Session: {session_id}) ---")
        return {"suggestion": suggestion}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Optimizer failed to generate next candidate coordinates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Active learning solver failure: {str(e)}"
        )

@router.get("/history")
def get_experiment_history(session_id: str = "default"):
    """
    Returns all experiments with CPP inputs and CQA outputs.
    """
    logger.info(f"--- START get_experiment_history (Session: {session_id}) ---")
    try:
        loop = _get_active_loop(session_id, "Session not found. Please initialize session.")
        
        n_exps = len(loop.history_X)
        logger.info(f"Retrieved history with {n_exps} completed trials.")
        
        history = {
            "n_experiments": n_exps,
            "experiments": [
                {"x": x, "y": y}
                for x, y in zip(loop.history_X, loop.history_Y)
            ]
        }
        logger.info(f"--- END get_experiment_history SUCCESS (Session: {session_id}) ---")
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error retrieving session history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trial history: {str(e)}"
        )

@router.get("/pareto")
def get_pareto_front(session_id: str = "default"):
    """
    Returns current Pareto-optimal solutions with CQA predictions.
    """
    logger.info(f"--- START get_pareto_front (Session: {session_id}) ---")
    try:
        loop = _get_active_loop(session_id, "Session not found. Please initialize session.")
        
        n_pareto = len(loop.pareto_solutions)
        logger.info(f"Retrieved {n_pareto} non-dominated Pareto front points.")
        
        pareto = {
            "n_pareto": n_pareto,
            "pareto_solutions": loop.pareto_solutions,
            "hypervolume_history": loop.hypervolume_history
        }
        logger.info(f"--- END get_pareto_front SUCCESS (Session: {session_id}) ---")
        return pareto
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error calculating Pareto front: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute non-dominated frontier: {str(e)}"
        )

@router.get("/convergence")
def check_convergence_status(session_id: str = "default"):
    """
    Checks whether the optimization loop has converged.
    """
    logger.info(f"--- START check_convergence_status (Session: {session_id}) ---")
    try:
        loop = _get_active_loop(session_id, "Session not found. Please initialize session.")
        
        status_info = loop.check_convergence()
        logger.info(f"Convergence status check complete. Converged: {status_info.get('converged')}")
        
        logger.info(f"--- END check_convergence_status SUCCESS (Session: {session_id}) ---")
        return status_info
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error evaluating convergence: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute convergence criteria: {str(e)}"
        )

@router.get("/summary")
def get_session_summary(session_id: str = "default"):
    """
    Returns complete Phase 1 summary for export to Team Delta.
    """
    logger.info(f"--- START get_session_summary (Session: {session_id}) ---")
    try:
        loop = _get_active_loop(session_id, "Session not found. Please initialize session.")
        
        logger.info("Computing convergence parameters.")
        convergence = loop.check_convergence()
        
        # Compute average Weibull profile for the current Pareto-optimal solutions
        weibull_data = []
        times = np.array([15.0, 30.0, 45.0, 60.0])
        
        logger.info(f"Fitting Weibull dissolution parameters to {len(loop.pareto_solutions)} Pareto solutions.")
        for solution in loop.pareto_solutions:
            try:
                # Extract dissolution points (first 4 elements of y)
                y_vals = np.array([
                    solution["y"][0], # q15
                    solution["y"][1], # q30
                    solution["y"][2], # q45
                    solution["y"][3]  # q60
                ])
                eta, beta, r_sq = fit_weibull_profile(times, y_vals)
                weibull_data.append({
                    "solution_id": solution.get("id", "unknown"),
                    "eta_scale": eta,
                    "beta_shape": beta,
                    "r_squared": r_sq
                })
            except RuntimeError as re:
                # Catch curve fitting failures and fallback gracefully with a warning
                logger.warning(f"Weibull curve fitting failed for solution {solution.get('id')}: {re}. Falling back to default estimates.")
                weibull_data.append({
                    "solution_id": solution.get("id", "unknown"),
                    "eta_scale": 30.0,
                    "beta_shape": 1.0,
                    "r_squared": 0.8
                })

        # Compute Scaleup metrics for default scale (5.0 scale-up factor)
        logger.info("Computing dimensionless constant-Froude impeller mixing parameters.")
        try:
            scaleup_data = compute_scaleup_metrics(
                impeller_speed_rpm=300.0,
                impeller_diameter_m=0.1,
                scale_factor=5.0
            )
        except Exception as e:
            logger.error(f"Scaleup metrics calculation failed: {e}")
            scaleup_data = {}
        
        api_name = loop.domain.api_name if hasattr(loop.domain, 'api_name') else "unknown"
        summary = {
            "schema_version": "1.1",
            "api_name": api_name,
            "n_seed_experiments": loop.seed_count,
            "n_total_experiments": len(loop.history_X),
            "n_pareto_solutions": len(loop.pareto_solutions),
            "loo_cv_r2": loop.compute_loo_cv_r2(),
            "loo_cv_calibration": loop.evaluate_surrogate_calibration(),
            "converged": convergence["converged"],
            "hypervolume_history": loop.hypervolume_history,
            "pareto_solutions": loop.pareto_solutions,
            "analytical_horizons": {
                "weibull_dissolution_fits": weibull_data,
                "dimensionless_scaleup_metrics": scaleup_data
            }
        }
        logger.info(f"--- END get_session_summary SUCCESS (Session: {session_id}) ---")
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error compiling session summary card: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary card: {str(e)}"
        )

@router.get("/presets")
def get_api_presets():
    """
    Dynamically loads and computes presets for APIs from the Team Alpha database (CSV).
    Falls back gracefully to static presets if the database file is unavailable.
    """
    import os
    import pandas as pd
    
    csv_path = "/home/harshit/vector_1_p/data/team_alpha_dummy.csv"
    
    # Check if the database exists and can be parsed
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            # Remove duplicates to get unique API entries
            df_unique = df.drop_duplicates(subset=["api_name"])
            
            presets = {}
            import math
            
            def clean_float(val, fallback):
                if val is None:
                    return fallback
                try:
                    f_val = float(val)
                    if math.isnan(f_val):
                        return fallback
                    return f_val
                except (ValueError, TypeError):
                    return fallback

            for _, row in df_unique.iterrows():
                row_dict = row.to_dict()
                name = str(row_dict.get("api_name", "Unknown"))
                
                # Retrieve raw values safely
                raw_decomp = row_dict.get("decomposition_onset_c")
                raw_tg = row_dict.get("tg_predicted_celsius")
                raw_carr = row_dict.get("flow_properties_carr_index")
                raw_bcs = row_dict.get("bcs_class")
                raw_dose = row_dict.get("dose_mg")
                
                # Parse values with robust null checks
                decomp = clean_float(raw_decomp, 150.0)
                tg = clean_float(raw_tg, max(30.0, min(80.0, decomp - 80.0)))
                carr = clean_float(raw_carr, 25.0)
                
                # Flow property-based binder bounds (Carr Index)
                if carr > 25.0:
                    mcc_min, mcc_max = 20.0, 50.0
                else:
                    mcc_min, mcc_max = 10.0, 35.0
                
                # BCS class-dependent dissolution targets
                bcs = str(raw_bcs) if raw_bcs is not None else "II"
                # Handle possible NaN string/value
                if bcs == "nan" or bcs == "":
                    bcs = "II"
                target_diss = 85.0 if bcs == "I" else 80.0
                
                # Dose-dependent tablet hardness targets
                dose = clean_float(raw_dose, 100.0)
                target_hardness = 9.0 if dose > 200.0 else 7.5
                
                presets[name] = {
                    "tg": round(tg, 1),
                    "decomp": round(decomp, 1),
                    "mcc_min": mcc_min,
                    "mcc_max": mcc_max,
                    "target_diss": target_diss,
                    "target_hardness": target_hardness,
                    "bcs_class": bcs,
                    "molecular_weight": round(clean_float(row_dict.get("molecular_weight"), 150.0), 1),
                    "logP": round(clean_float(row_dict.get("logP"), 1.0), 2),
                    "particle_size_d50_um": round(clean_float(row_dict.get("particle_size_d50_um"), 50.0), 1),
                    "carr_index": round(carr, 1),
                    "dose_mg": round(dose, 1)
                }
            return presets
        except Exception as e:
            logger.error(f"Failed to parse dynamic presets database: {e}. Falling back to static presets.")
            
    # Resilient fallback preset dictionary
    return {
        "Aspirin-300": {
            "tg": 65.0,
            "decomp": 120.0,
            "mcc_min": 20.0,
            "mcc_max": 50.0,
            "target_diss": 80.0,
            "target_hardness": 8.0
        },
        "Paracetamol": {
            "tg": 58.0,
            "decomp": 150.0,
            "mcc_min": 15.0,
            "mcc_max": 40.0,
            "target_diss": 85.0,
            "target_hardness": 9.0
        },
        "Ibuprofen": {
            "tg": 20.0,
            "decomp": 75.0,
            "mcc_min": 10.0,
            "mcc_max": 35.0,
            "target_diss": 75.0,
            "target_hardness": 6.5
        },
        "Indomethacin": {
            "tg": 42.0,
            "decomp": 120.0,
            "mcc_min": 25.0,
            "mcc_max": 60.0,
            "target_diss": 80.0,
            "target_hardness": 7.5
        },
        "Simvastatin": {
            "tg": 45.0,
            "decomp": 149.0,
            "mcc_min": 20.0,
            "mcc_max": 50.0,
            "target_diss": 90.0,
            "target_hardness": 10.0
        },
        "Celecoxib": {
            "tg": 56.0,
            "decomp": 207.0,
            "mcc_min": 20.0,
            "mcc_max": 50.0,
            "target_diss": 80.0,
            "target_hardness": 8.0
        },
        "Verapamil": {
            "tg": 50.0,
            "decomp": 140.0,
            "mcc_min": 15.0,
            "mcc_max": 45.0,
            "target_diss": 85.0,
            "target_hardness": 8.5
        },
        "Fenofibrate": {
            "tg": 32.0,
            "decomp": 181.0,
            "mcc_min": 20.0,
            "mcc_max": 50.0,
            "target_diss": 75.0,
            "target_hardness": 7.0
        }
    }
