from rootcause.config import REQUIRED_VARIABLES

CLARIFICATION_QUESTIONS = {
    "soil_organic_carbon": "What is the soil organic carbon level, roughly (as a percent, or 'low' / 'medium' / 'high')?",
    "rainfall_level": "What is the approximate annual rainfall in your region (in mm), or would you describe the climate as arid, semi-arid, sub-humid, or humid?",
    "land_use": "What is the current land use — for example monoculture crop, diversified crop rotation, agroforestry, or pasture?",
}


def missing_required_variables(known_variables: dict) -> list[str]:
    return [v for v in REQUIRED_VARIABLES if known_variables.get(v) is None]


def build_clarification_question(missing: list[str]) -> str:
    questions = [CLARIFICATION_QUESTIONS[v] for v in missing if v in CLARIFICATION_QUESTIONS]
    return " ".join(questions)
