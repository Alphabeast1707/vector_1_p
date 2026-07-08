import pytest
import json
import os
import numpy as np
from schemas.shared_db_schemas import ProfileCard, StrategyCard, ThermalLimits, PowderMetrics, Excipient, CQATargets
from engines.domain_builder import build_domain
from engines.bo_loop import ActiveLearningLoop

def test_phase1_data_integration():
    # 1. Load the phase1_output.json data
    json_path = "/home/harshit/vector_1/phase1/phase1_output.json"
    assert os.path.exists(json_path), f"File not found: {json_path}"
    
    with open(json_path, "r") as f:
        phase1_data = json.load(f)
        
    assert phase1_data["api_name"] == "Paracetamol"
    assert "pareto_solutions" in phase1_data
    
    solutions = phase1_data["pareto_solutions"]
    assert len(solutions) > 0
    
    # 2. Reconstruct the ProfileCard dynamically
    profile = ProfileCard(
        api_name=phase1_data["api_name"],
        thermal_limits=ThermalLimits(
            glass_transition_temp_c=75.0, # fallback
            decomposition_temp_c=247.7 # from paracetamol decomp onset
        ),
        powder_metrics=PowderMetrics(
            carrs_index=23.9, # Carr Index
            hausner_ratio=1.2,
            true_density_g_ml=1.3,
            particle_size_d50_um=50.0
        )
    )
    
    # Extract excipients from the first Pareto solution
    first_sol = solutions[0]["cpps"]
    excipient_list = []
    
    # Dynamic excipient detection
    for key in first_sol.keys():
        if key.endswith("_pct") and key not in ("Granulation_Moisture_pct", "coating_thickness_pct", "binder_pct"):
            # Clean name for Excipient schema
            exc_name = key[:-4].replace("_", " ")
            excipient_list.append(
                Excipient(
                    name=exc_name,
                    role="filler",
                    concentration_min_pct=5.0,
                    concentration_max_pct=60.0
                )
            )
            
    strategy = StrategyCard(
        excipients=excipient_list,
        cqa_targets=CQATargets(
            dissolution_q30_min_pct=float(phase1_data.get("cqa_specifications", {}).get("dissolution_30min_pct", 85.0)),
            hardness_min_kp=6.0,
            hardness_max_kp=12.0,
            friability_max_pct=1.0,
            content_uniformity_min_pct=95.0,
            content_uniformity_max_pct=105.0,
            heckel_slope_min=0.08,
            heckel_slope_max=0.15
        )
    )
    
    domain = build_domain(profile, strategy)
    loop = ActiveLearningLoop(domain, strategy)
    
    # 3. Feed Pareto solutions as historical experiments to active learning loop
    # We map keys from phase1 cpps/cqas to domain inputs/outputs
    for sol in solutions:
        cpps = sol["cpps"]
        cqas = sol["cqa_predicted"]
        
        # Populate input X vector in the order of domain.inputs
        x_vals = []
        for inp in domain.inputs:
            # Map dynamic process keys
            if inp.key == "granulation_moisture_pct":
                x_vals.append(float(cpps.get("Granulation_Moisture_pct", 5.0)))
            elif inp.key == "drying_temp_c":
                x_vals.append(float(cpps.get("Drying_Temperature_C", 60.0)))
            elif inp.key == "compression_force_kn":
                x_vals.append(float(cpps.get("Compression_Force_kN", 12.0)))
            elif inp.key == "spray_rate_g_min":
                x_vals.append(float(cpps.get("Blade_Speed_rpm", 300.0) * 0.05)) # proxy mapping
            elif inp.key == "binder_pct":
                x_vals.append(float(cpps.get("HPC_LF_pct", 4.0))) # binder proxy
            else:
                # Dynamic excipient match
                cpp_key = inp.key
                matched = False
                for k in cpps.keys():
                    if k.replace("_", " ").lower() == cpp_key.replace("_", " ").lower():
                        x_vals.append(float(cpps[k]))
                        matched = True
                        break
                if not matched:
                    x_vals.append(10.0) # default fallback
                    
        # Populate output Y vector in the order of domain.outputs
        # outputs: dissolution_q15/q30/q45/q60, hardness_n, friability_pct, content_uniformity_pct, heckel_slope
        diss_q30 = float(cqas.get("Dissolution_30min_pct", {}).get("mean", 85.0))
        y_vals = [
            diss_q30 - 8.0, # q15 proxy
            diss_q30,       # q30
            diss_q30 + 3.0, # q45 proxy
            diss_q30 + 5.0, # q60 proxy
            float(cqas.get("Hardness_N", {}).get("mean", 100.0)),
            float(cqas.get("Friability_pct", {}).get("mean", 0.5)),
            100.0 - float(cqas.get("Uniformity_RSD_pct", {}).get("mean", 2.0)), # convert RSD to CU midpoint dev proxy
            0.12 # heckel slope fallback
        ]
        
        loop.add_experiment_result(x_vals, y_vals)
        
    # 4. Trigger next best suggestion (fits BoTorch model using the loaded dataset)
    suggestion = loop.suggest_next()
    assert isinstance(suggestion, dict)
    
    # Check all parameters are in suggestion
    for inp in domain.inputs:
        assert inp.key in suggestion
        lower, upper = inp.bounds
        assert lower - 1e-6 <= suggestion[inp.key] <= upper + 1e-6
        
    # Check mass-balance
    excip_keys = [
        k for k in suggestion.keys() 
        if k.endswith('_pct') and k not in ('granulation_moisture_pct', 'coating_thickness_pct')
    ]
    excip_sum = sum(suggestion[k] for k in excip_keys)
    assert excip_sum <= 70.001

if __name__ == "__main__":
    print("Running test_phase1_data_integration...")
    test_phase1_data_integration()
    print("Test passed successfully!")
