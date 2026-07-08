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
    Builds the mathematical search space for the Bayesian DoE.
    Constrains parameters based on API thermal limits and excipient ranges.
    """
    
    # Drying temp bounds based on Tg to support freeze/vacuum drying for low-Tg APIs (e.g. amorphous aspirin)
    max_drying = profile.thermal_limits.glass_transition_temp_c - 10.0
    min_drying = min(40.0, max_drying - 15.0)
    
    process_inputs = [
        ContinuousInput(key="binder_pct", bounds=(2.0, 6.0)),
        ContinuousInput(key="granulation_moisture_pct", bounds=(3.0, 7.0)),
        ContinuousInput(key="drying_temp_c", bounds=(min_drying, max_drying)),
        ContinuousInput(key="compression_force_kn", bounds=(8.0, 22.0)),
        ContinuousInput(key="spray_rate_g_min", bounds=(5.0, 30.0)),
    ]

    # Excipient concentration inputs dynamically built from M2 StrategyCard
    excipient_inputs = [
        ContinuousInput(
            key=f"{exc.name}_pct",
            bounds=(exc.concentration_min_pct, exc.concentration_max_pct)
        )
        for exc in strategy.excipients
    ]

    # Multi-objective CQA targets (5 CQAs total: Dissolution curve, Hardness, Friability, CU, Compressibility)
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

    return Domain(inputs=process_inputs + excipient_inputs, outputs=cqa_outputs)

