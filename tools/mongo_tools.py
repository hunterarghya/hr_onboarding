"""
MongoDB tools — CRUD operations on the candidates collection.

These are fully implemented (no placeholders needed).
"""

from datetime import datetime, timezone
from bson import ObjectId
from google.adk.tools import FunctionTool
from db.connection import get_candidates_collection


def save_candidate_to_mongo(
    name: str,
    email: str,
    position_applied: str,
    match_score: float,
    phone: str = "",
    resume_url: str = "",
) -> dict:
    """Save a shortlisted candidate to the MongoDB candidates collection.

    Args:
        name: Full name of the candidate.
        email: Email address of the candidate.
        position_applied: The role the candidate applied for.
        match_score: Resume-to-JD match score (0-10).
        phone: Phone number (optional).
        resume_url: Link to the uploaded resume PDF (optional).

    Returns:
        Dictionary with the inserted candidate ID and status.
    """
    col = get_candidates_collection()
    doc = {
        "name": name,
        "email": email,
        "phone": phone,
        "position_applied": position_applied,
        "match_score": match_score,
        "is_shortlisted": True,
        "is_selected": False,
        "salary_offered": 0,
        "offer_letter_sent": False,
        "documents_submitted": False,
        "document_url": "",
        "resume_url": resume_url,
        "appointment_letter_sent": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    result = col.insert_one(doc)
    return {"status": "saved", "candidate_id": str(result.inserted_id)}


def fetch_selected_candidates() -> dict:
    """Fetch candidates who have been selected after interview but haven't received an offer letter yet.

    Returns:
        Dictionary with key "candidates" containing a list of candidate dicts.
    """
    col = get_candidates_collection()
    cursor = col.find({"is_selected": True, "offer_letter_sent": False})
    candidates = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        if "created_at" in doc:
            doc["created_at"] = doc["created_at"].isoformat()
        if "updated_at" in doc:
            doc["updated_at"] = doc["updated_at"].isoformat()
        candidates.append(doc)
    return {"candidates": candidates}


def update_candidate_in_mongo(candidate_id: str, update_fields: dict) -> dict:
    """Update specific fields of a candidate document in MongoDB.

    Args:
        candidate_id: The MongoDB ObjectId of the candidate (as string).
        update_fields: Dictionary of fields to update
                       (e.g. {"offer_letter_sent": true}).

    Returns:
        Dictionary with update status.
    """
    if not candidate_id:
        return {"error": "candidate_id is empty"}
        
    col = get_candidates_collection()
    update_fields["updated_at"] = datetime.now(timezone.utc)
    
    try:
        oid = ObjectId(candidate_id)
    except Exception as e:
        return {"error": f"Invalid ObjectId: {e}"}
        
    result = col.update_one(
        {"_id": oid},
        {"$set": update_fields},
    )
    return {
        "status": "updated" if result.modified_count > 0 else "no_change",
        "modified_count": result.modified_count,
    }


def fetch_candidates_awaiting_documents() -> dict:
    """Fetch candidates who received an offer letter but haven't submitted documents yet.

    Returns:
        Dictionary with key "candidates" containing a list of candidate dicts.
    """
    col = get_candidates_collection()
    cursor = col.find({
        "is_selected": True,
        "offer_letter_sent": True,
        "documents_submitted": False,
    })
    candidates = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        if "created_at" in doc:
            doc["created_at"] = doc["created_at"].isoformat()
        if "updated_at" in doc:
            doc["updated_at"] = doc["updated_at"].isoformat()
        candidates.append(doc)
    return {"candidates": candidates}


# ── ADK FunctionTool wrappers ─────────────────────────────
save_candidate_tool = FunctionTool(func=save_candidate_to_mongo)
fetch_selected_tool = FunctionTool(func=fetch_selected_candidates)
update_candidate_tool = FunctionTool(func=update_candidate_in_mongo)
fetch_awaiting_docs_tool = FunctionTool(func=fetch_candidates_awaiting_documents)
