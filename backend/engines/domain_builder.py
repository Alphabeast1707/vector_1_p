import logging
from bofire.data_models.domain.api import Domain, Inputs, Outputs
from bofire.data_models.features.api import ContinuousInput, ContinuousOutput

from schemas.shared_db_schemas import ProfileCard, StrategyCard
from constants import (
    BOUNDS_BINDER, MOISTURE_MIN_DEFAULT, MOISTURE_MAX_DEFAULT,
    BOUNDS_COMPRESSION, BOUNDS_SPRAY_RATE, BOUNDS_BATCH_SCALE_KG,
    BOUNDS_IMPELLER_SPEED_RPM, BOUNDS_BLADE_SPEED_RPM, BOUNDS_SCALE_FACTOR
)

logger = logging.getLogger("vector_1.domain_builder")

def build_domain(profile: ProfileCard, strategy: StrategyCard) -> Domain:
    """
    Builds the mathematical search space for the Bayesian DoE dynamically.
    Constrains parameters based on API thermal limits, polymorphic risk, and excipient hydrophilicity.
    """
    logger.info("Initializing dynamic domain builder search space.")
    
    try:
        # 1. Binder % Bounds (Fixed range)
        bounds_binder = BOUNDS_BINDER

        # 2. Granulation Moisture Bounds Setup
        moisture_min = MOISTURE_MIN_DEFAULT
        moisture_max = MOISTURE_MAX_DEFAULT

        # 3. Drying Temperature Bounds Setup
        decomp = profile.thermal_limits.decomposition_temp_c
        upper_temp = min(100.0, decomp - 15.0)

        if profile.solid_state_risk and profile.solid_state_risk.polymorphic_risk_tier == "high":
            # Assume transition limit from custom field or glass transition temp as fallback
            conversion_temp = getattr(profile.thermal_limits, "polymorph_conversion_temp", None) or profile.thermal_limits.glass_transition_temp_c
            upper_temp = min(upper_temp, conversion_temp - 7.0)

        # Consolidated excipient-dependent bounds checking
        for exc in strategy.excipients:
            if exc.moisture_stability is not None and exc.moisture_stability < 0.5:
                moisture_max = min(moisture_max, 5.5)  # Tighten upper bound
            if exc.excipient_hydrophilicity is not None and exc.excipient_hydrophilicity > 0.8:
                moisture_min = max(moisture_min, 4.0)  # Raise lower bound
            if exc.excipient_tg_c is not None:
                upper_temp = min(upper_temp, exc.excipient_tg_c - 5.0)

        lower_temp = max(40.0, upper_temp - 45.0)  # at least 40°C, at most 45°C operating span

        # 4. Compression Force Bounds (Expanded from 8-22 to 8-25 kN)
        bounds_compression = BOUNDS_COMPRESSION

        # Compile the 5 Critical Process Parameters (CPPs)
        process_inputs = [
            ContinuousInput(key="binder_pct", bounds=bounds_binder),
            ContinuousInput(key="granulation_moisture_pct", bounds=(moisture_min, moisture_max)),
            ContinuousInput(key="drying_temp_c", bounds=(lower_temp, upper_temp)),
            ContinuousInput(key="compression_force_kn", bounds=bounds_compression),
            ContinuousInput(key="spray_rate_g_min", bounds=BOUNDS_SPRAY_RATE),
        ]

        # Additional production scale CPPs from Phase 1 Notebook
        production_inputs = [
            ContinuousInput(key="Batch_Scale_kg", bounds=BOUNDS_BATCH_SCALE_KG),
            ContinuousInput(key="Impeller_Speed_rpm", bounds=BOUNDS_IMPELLER_SPEED_RPM),
            ContinuousInput(key="Blade_Speed_rpm", bounds=BOUNDS_BLADE_SPEED_RPM),
            ContinuousInput(key="Scale_Factor", bounds=BOUNDS_SCALE_FACTOR),
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

        logger.info("Successfully constructed domain inputs and outputs.")
        return Domain(
            inputs=Inputs(features=process_inputs + production_inputs + excipient_inputs),
            outputs=Outputs(features=cqa_outputs)
        )
        
    except Exception as e:
        logger.error(f"Failed to build dynamic domain: {e}")
        raise ValueError(f"Error handling mechanism failed to build dynamic search domain: {e}")
