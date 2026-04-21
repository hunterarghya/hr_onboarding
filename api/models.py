"""Pydantic models for API request / response validation."""

from pydantic import BaseModel, Field
from typing import Optional, List


class CandidateOut(BaseModel):
    """Response model for candidate data."""
    id: str = Field(..., alias="_id")
    name: str
    email: str
    phone: str = ""
    position_applied: str
    match_score: float
    is_shortlisted: bool
    is_selected: bool
    salary_offered: float
    offer_letter_sent: bool
    documents_submitted: bool
    document_url: str = ""
    appointment_letter_sent: bool

    class Config:
        populate_by_name = True


class SelectCandidateRequest(BaseModel):
    """Request body for marking a candidate as selected with salary."""
    salary_offered: float = Field(..., gt=0, description="Annual salary in INR")


class BulkSelectRequest(BaseModel):
    """Request body for selecting multiple candidates at once."""
    selections: List[dict] = Field(
        ...,
        description="List of {candidate_id, salary_offered} dicts",
    )
