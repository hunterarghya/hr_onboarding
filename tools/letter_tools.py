"""
Letter generation tools — fill templates to produce offer / appointment letters.

Fully implemented — reads from templates/ directory.
"""

import os
from datetime import datetime
from google.adk.tools import FunctionTool

_TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")


def generate_offer_letter(
    name: str,
    position: str,
    salary: float,
) -> dict:
    """Generate an offer letter by filling the template with candidate details.

    Args:
        name: Full name of the candidate.
        position: Position being offered.
        salary: Annual salary in INR.

    Returns:
        Dictionary with the generated offer letter text.
    """
    template_path = os.path.join(_TEMPLATES_DIR, "offer_letter.txt")
    with open(template_path, "r") as f:
        template = f.read()

    letter = template.format(
        date=datetime.now().strftime("%d %B %Y"),
        name=name,
        position=position,
        salary=f"{salary:,.0f}",
    )
    return {"letter": letter}


def generate_appointment_letter(
    name: str,
    position: str,
    salary: float,
    joining_date: str = "To be communicated",
) -> dict:
    """Generate an appointment letter by filling the template with candidate details.

    Args:
        name: Full name of the candidate.
        position: Position being offered.
        salary: Annual salary in INR.
        joining_date: Date of joining (e.g. '1 June 2026').

    Returns:
        Dictionary with the generated appointment letter text.
    """
    template_path = os.path.join(_TEMPLATES_DIR, "appointment_letter.txt")
    with open(template_path, "r") as f:
        template = f.read()

    letter = template.format(
        date=datetime.now().strftime("%d %B %Y"),
        name=name,
        position=position,
        salary=f"{salary:,.0f}",
        joining_date=joining_date,
    )
    return {"letter": letter}


# ── ADK FunctionTool wrappers ─────────────────────────────
generate_offer_letter_tool = FunctionTool(func=generate_offer_letter)
generate_appointment_letter_tool = FunctionTool(func=generate_appointment_letter)
