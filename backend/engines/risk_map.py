from schemas.shared_db_schemas import ProfileCard

def generate_risk_uncertainty_map(
    profile: ProfileCard,
    pareto_solutions: list[dict],
    mc_results: dict | None = None
) -> dict:
    """
    Generates the Phase 1 Risk/Uncertainty Map referenced in Step 5.
    
    Zones:
    - ROBUST: All CQAs in-spec with tight Confidence Intervals (CI), no failure risks > 15% (green zone).
    - TRANSITIONAL: CQAs in-spec but wide CI or yellow failure risks.
    - FRAGILE: CQAs borderline or red failure risks.
    
    Uses solid-state risk data (polymorphic risk, hygroscopicity, stability)
    from ProfileCard to contextualize zones.
    """
    zones = {}
    
    # Extract baseline thermal and solid-state safety risks from Team Alpha's ProfileCard
    polymorph_risk = "low"
    if profile.solid_state_risk:
        polymorph_risk = profile.solid_state_risk.polymorphic_risk_tier
        
    hygroscopicity = "low"
    if profile.solid_state_risk:
        hygroscopicity = profile.solid_state_risk.hygroscopicity_class

    for solution in pareto_solutions:
        sol_id = solution.get("solution_id", 1)
        cqas = solution.get("cqa_predicted", {})
        
        all_in_spec = True
        max_ci_width = 0.0
        
        for name, pred in cqas.items():
            if not pred.get("in_spec", True):
                all_in_spec = False
            ci_lo = pred.get("ci95_lo", 0.0)
            ci_hi = pred.get("ci95_hi", 0.0)
            max_ci_width = max(max_ci_width, abs(ci_hi - ci_lo))

        # Check Monte Carlo parameters if provided
        mc_risk_level = "GREEN"
        if mc_results and "summary" in mc_results:
            for fm, stats in mc_results["summary"].items():
                if stats.get("p95", 0.0) > 0.40:
                    mc_risk_level = "RED"
                elif stats.get("p95", 0.0) > 0.15 and mc_risk_level != "RED":
                    mc_risk_level = "YELLOW"

        # Classification Zone Rule Engine
        if all_in_spec and max_ci_width < 10.0 and mc_risk_level == "GREEN":
            zone = "ROBUST"
            description = "Formulation window is stable with tight variance. Ideal candidate for commercialization."
        elif all_in_spec and mc_risk_level != "RED":
            zone = "TRANSITIONAL"
            description = "Design coordinates are safe, but exhibit moderate process sensitivity. Review compression limits."
        else:
            zone = "FRAGILE"
            description = "High failure likelihood or wide prediction margins under shear. Reformulation is suggested."

        # Add context from solid-state chemistry risk drivers
        chemistry_caveats = []
        if polymorph_risk == "high":
            chemistry_caveats.append("High polymorph transition risk detected. Drying temperatures should be kept below conversion threshold.")
        if "highly" in hygroscopicity.lower() or "moderately" in hygroscopicity.lower():
            chemistry_caveats.append("Active drug has high ambient moisture sensitivity. Control relative humidity in fluid bed process.")

        zones[str(sol_id)] = {
            "zone": zone,
            "max_ci_width": round(max_ci_width, 2),
            "all_in_spec": all_in_spec,
            "mc_risk_level": mc_risk_level,
            "description": description,
            "chemistry_caveats": chemistry_caveats
        }

    return zones
