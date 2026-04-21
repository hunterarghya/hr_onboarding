"""
Candidate document schema reference.

This is NOT enforced by MongoDB — it's here for documentation
and for Pydantic model alignment.

Collection: candidates
{
    "_id":                     ObjectId   (auto),
    "name":                    str,
    "email":                   str,
    "phone":                   str        (optional),
    "position_applied":        str,
    "match_score":             float      (0-10, from LLM matcher),
    "is_shortlisted":          bool       (True if score >= 8),
    "is_selected":             bool       (set True via PATCH after interview),
    "salary_offered":          float      (set via PATCH after interview),
    "offer_letter_sent":       bool       (Pipeline 2 sets after drafting),
    "documents_submitted":     bool       (Pipeline 3 sets after receiving PAN),
    "document_url":            str        (ImageKit URL for stored document),
    "appointment_letter_sent": bool       (Pipeline 3 sets after drafting),
    "created_at":              datetime,
    "updated_at":              datetime,
}
"""
