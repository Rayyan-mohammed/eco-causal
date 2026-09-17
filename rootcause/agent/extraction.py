from typing import Optional

from pydantic import BaseModel, Field

from rootcause.llm import parse_structured


class ExtractedInput(BaseModel):
    soil_organic_carbon: Optional[float] = Field(
        None, description="Percent soil organic carbon, if stated or reasonably estimable."
    )
    rainfall_level: Optional[float] = Field(
        None,
        description=(
            "Annual rainfall in millimeters. If the user gives a qualitative climate description "
            "instead of a number (e.g. 'semi-arid', 'very dry', 'humid'), infer a reasonable band "
            "midpoint (arid ~150, semi-arid ~450, sub-humid ~800, humid ~1500)."
        ),
    )
    soil_ph: Optional[float] = None
    soil_salinity: Optional[float] = Field(None, description="Soil salinity in dS/m, if mentioned.")
    land_use: Optional[str] = Field(
        None, description="Land use description, e.g. 'monoculture wheat', 'agroforestry', 'pasture'."
    )
    crop: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    concern: Optional[str] = Field(
        None, description="The environmental concern or question the user raised, in a few words."
    )


INPUT_EXTRACTION_SYSTEM = (
    "You extract structured environmental variables from a user's message for an agricultural and "
    "biodiversity advisory system. Only fill fields the user actually stated or clearly implied. "
    "Leave a field null if it is not mentioned or cannot be reasonably inferred. Do not invent precise "
    "numbers beyond a reasonable band midpoint for vague qualitative statements."
)


def extract_input_variables(user_text: str) -> ExtractedInput:
    return parse_structured(
        messages=[{"role": "user", "content": user_text}],
        output_model=ExtractedInput,
        system=INPUT_EXTRACTION_SYSTEM,
    )


class CausalLink(BaseModel):
    cause: str = Field(description="Variable id from the causal map catalog, e.g. 'soil_organic_carbon'.")
    effect: str = Field(description="Variable id from the causal map catalog, e.g. 'soil_microbial_diversity'.")


class ExtractedClaim(BaseModel):
    chain: list[CausalLink] = Field(
        default_factory=list,
        description="The ordered chain of cause -> effect steps implied by the recommendation, using only catalog variable ids.",
    )


def build_extraction_system(node_catalog: list[dict]) -> str:
    catalog_lines = "\n".join(f"- {n['id']}: {n['label']} ({n['domain']})" for n in node_catalog)
    return (
        "You convert a free-text environmental recommendation into a structured causal chain.\n"
        "Use ONLY the following variable ids, exactly as spelled, choosing the closest match for each concept mentioned:\n"
        f"{catalog_lines}\n\n"
        "Break the recommendation into a chain of consecutive cause -> effect steps that reflects the "
        "multi-variable reasoning implied by the text. If the recommendation only makes a single-step "
        "claim, return a chain of length one. If no catalog variable matches a step, omit that step "
        "rather than inventing an id."
    )


def extract_causal_chain(recommendation_text: str, node_catalog: list[dict]) -> ExtractedClaim:
    return parse_structured(
        messages=[{"role": "user", "content": recommendation_text}],
        output_model=ExtractedClaim,
        system=build_extraction_system(node_catalog),
    )
