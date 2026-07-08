EQUIPMENT_DATABASE = {
    "lab_granulator_10L": {
        "id": "lab_granulator_10L",
        "name": "Lab Scale High-Shear Granulator (10L)",
        "bowl_volume_l": 10.0,
        "impeller_diameter_m": 0.25,
        "max_rpm": 800.0
    },
    "commercial_granulator_300L": {
        "id": "commercial_granulator_300L",
        "name": "Commercial Production Granulator (300L)",
        "bowl_volume_l": 300.0,
        "impeller_diameter_m": 0.85,
        "max_rpm": 200.0
    }
}

def get_equipment_spec(equipment_id: str) -> dict:
    if equipment_id in EQUIPMENT_DATABASE:
        return EQUIPMENT_DATABASE[equipment_id]
    # Default fallback
    if "lab" in equipment_id.lower():
        return EQUIPMENT_DATABASE["lab_granulator_10L"]
    return EQUIPMENT_DATABASE["commercial_granulator_300L"]
