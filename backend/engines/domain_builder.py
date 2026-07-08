# Fallback mock classes if bofire fails to install due to system dependencies
try:
    from bofire.data_models.domain.api import Domain
    from bofire.data_models.features.api import ContinuousInput, ContinuousOutput
except ImportError:
    class ContinuousInput:
        def __init__(self, key, bounds):
            self.key = key
            self.bounds = bounds
            
    class ContinuousOutput:
        def __init__(self, key):
            self.key = key
            
    class Domain:
        def __init__(self, inputs, outputs):
            self.inputs = inputs
            self.outputs = outputs

from schemas.shared_db_schemas import ProfileCard, StrategyCard

def build_domain(profile: ProfileCard, strategy: StrategyCard) -> Domain:
    """
    Builds the mathematical search space for the Bayesian DoE dynamically.
    Constrains parameters based on API thermal limits, polymorphic risk, and excipient hydrophilicity.
    """
    
    # 1. Binder % Bounds (Fixed range)
    bounds_binder = (2.0, 6.0)

    # 2. Granulation Moisture Bounds
    moisture_min = 3.0
    moisture_max = 7.0

    for exc in strategy.excipients:
        if exc.moisture_stability is not None and exc.moisture_stability < 0.5:
            moisture_max = min(moisture_max, 5.5)  # Tighten upper bound
        if exc.excipient_hydrophilicity is not None and exc.excipient_hydrophilicity > 0.8:
            moisture_min = max(moisture_min, 4.0)  # Raise lower bound

    # 3. Drying Temperature Bounds (Most complex)
    decomp = profile.thermal_limits.decomposition_temp_c
    upper_temp = min(100.0, decomp - 15.0)

    if profile.solid_state_risk and profile.solid_state_risk.polymorphic_risk_tier == "high":
        # Tighten further based on glass transition conversion
        upper_temp = min(upper_temp, profile.thermal_limits.glass_transition_temp_c - 7.0)

    for exc in strategy.excipients:
        if exc.excipient_tg_c is not None:
            upper_temp = min(upper_temp, exc.excipient_tg_c - 5.0)

    lower_temp = max(40.0, upper_temp - 45.0)  # at least 40°C, at most 45°C operating span

    # 4. Compression Force Bounds (Expanded from 8-22 to 8-25 kN)
    bounds_compression = (8.0, 25.0)

    # Compile the 5 Critical Process Parameters (CPPs)
    process_inputs = [
        ContinuousInput(key="binder_pct", bounds=bounds_binder),
        ContinuousInput(key="granulation_moisture_pct", bounds=(moisture_min, moisture_max)),
        ContinuousInput(key="drying_temp_c", bounds=(lower_temp, upper_temp)),
        ContinuousInput(key="compression_force_kn", bounds=bounds_compression),
        ContinuousInput(key="spray_rate_g_min", bounds=(5.0, 30.0)),
    ]

    # Additional production scale CPPs from Phase 1 Notebook
    production_inputs = [
        ContinuousInput(key="Batch_Scale_kg", bounds=(1.0, 100.0)),
        ContinuousInput(key="Impeller_Speed_rpm", bounds=(150.0, 500.0)),
        ContinuousInput(key="Blade_Speed_rpm", bounds=(150.0, 500.0)),
        ContinuousInput(key="Scale_Factor", bounds=(1.0, 20.0)),
    ]

    # Excipient concentration inputs dynamically built from StrategyCard excipients
    excipient_inputs = [
        ContinuousInput(
            key=f"{exc.name}_pct",
            bounds=(exc.concentration_min_pct, exc.concentration_max_pct)
        )
        for exc in strategy.excipients
    ]

    # 8 Multi-objective CQA targets
    cqa_outputs = [
        ContinuousOutput(key="dissolution_q15"),
        ContinuousOutput(key="dissolution_q30"),
        ContinuousOutput(key="dissolution_q45"),
        ContinuousOutput(key="dissolution_q60"),
        ContinuousOutput(key="hardness_n"),
        ContinuousOutput(key="friability_pct"),
        ContinuousOutput(key="content_uniformity_pct"),
        ContinuousOutput(key="compressibility_heckel_slope"),
    ]

    # Return consolidated dynamic search domain
    return Domain(inputs=process_inputs + production_inputs + excipient_inputs, outputs=cqa_outputs)
