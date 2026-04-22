"""
HR Onboarding — Root Agent

This is the ADK entry point. It assembles three parallel pipelines:
  1. Resume Screening
  2. Offer Letter Generation
  3. Document Collection & Appointment Letter

Run with:
  adk run  hr_onboarding
  adk web  hr_onboarding
"""

from google.adk.agents import SequentialAgent

from pipelines.resume_screening import resume_screening_pipeline
from pipelines.offer_letter import offer_letter_pipeline
from pipelines.document_collection import document_collection_pipeline


# ── Root agent — runs all 3 pipelines sequentially ────────
root_agent = SequentialAgent(
    name="hr_onboarding_orchestrator",
    description=(
        "Top-level HR onboarding orchestrator. "
        "Runs resume screening, offer letter generation, and "
        "document collection pipelines in sequence to avoid rate limits."
    ),
    sub_agents=[
        resume_screening_pipeline,
    ],
)
