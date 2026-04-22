"""
FastAPI backend for HR Onboarding Dashboard.

Includes:
  - Google OAuth login (/auth/login/google, /auth/google/callback)
  - Candidate CRUD (/api/candidates/...)
  - Agent pipeline trigger (/api/run-agents, /api/run-status)
"""

import asyncio
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from bson import ObjectId

from config.settings import JWT_SECRET, GOOGLE_REDIRECT_URI
from db.connection import get_candidates_collection, get_db
from api.models import SelectCandidateRequest, BulkSelectRequest
from auth.oidc import oauth
from auth.utils import create_access_token

app = FastAPI(title="HR Onboarding Dashboard")

# ── Middleware ────────────────────────────────────────────
app.add_middleware(SessionMiddleware, secret_key=JWT_SECRET)

# ── Serve static frontend ────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── Agent run status (in-memory) ──────────────────────────
_run_status = {"state": "idle", "message": "", "started_at": None}


# ===========================================================
# AUTH ROUTES
# ===========================================================

@app.get("/")
def root():
    """Redirect to login page."""
    return FileResponse("static/login.html")


@app.get("/dashboard")
def dashboard():
    """Serve the dashboard (after login)."""
    return FileResponse("static/index.html")


@app.get("/auth/login/google")
async def google_login(request: Request):
    """Initiate Google OAuth2 login flow."""
    return await oauth.google.authorize_redirect(
        request,
        GOOGLE_REDIRECT_URI,
        access_type="offline",
        prompt="consent",
    )


@app.get("/auth/google/callback")
async def google_callback(request: Request):
    """Handle Google OAuth2 callback — store token and redirect to dashboard."""
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth Error: {str(e)}")

    user_info = token.get("userinfo", {})
    if not user_info.get("email"):
        raise HTTPException(status_code=400, detail="Could not get user email from Google")

    users_col = get_db()["users"]

    user_data = {
        "email": user_info["email"],
        "name": user_info.get("name", ""),
        "google_token": token,
        "last_login": datetime.now(timezone.utc),
    }

    existing = users_col.find_one({"email": user_info["email"]})
    if not existing:
        result = users_col.insert_one(user_data)
        user_id = str(result.inserted_id)
    else:
        user_id = str(existing["_id"])
        users_col.update_one({"_id": existing["_id"]}, {"$set": user_data})

    access_token = create_access_token(
        data={"sub": user_id, "email": user_info["email"]}
    )

    return RedirectResponse(url=f"/dashboard?token={access_token}")


# ===========================================================
# CANDIDATE ENDPOINTS
# ===========================================================

@app.get("/api/candidates")
def list_candidates():
    """List all shortlisted candidates."""
    col = get_candidates_collection()
    candidates = []
    for doc in col.find({"is_shortlisted": True}).sort("created_at", -1):
        doc["_id"] = str(doc["_id"])
        if isinstance(doc.get("created_at"), datetime):
            doc["created_at"] = doc["created_at"].isoformat()
        if isinstance(doc.get("updated_at"), datetime):
            doc["updated_at"] = doc["updated_at"].isoformat()
        candidates.append(doc)
    return {"candidates": candidates}


@app.get("/api/selected")
def list_selected():
    """List all selected candidates with full status info."""
    col = get_candidates_collection()
    candidates = []
    for doc in col.find({"is_selected": True}).sort("updated_at", -1):
        doc["_id"] = str(doc["_id"])
        if isinstance(doc.get("created_at"), datetime):
            doc["created_at"] = doc["created_at"].isoformat()
        if isinstance(doc.get("updated_at"), datetime):
            doc["updated_at"] = doc["updated_at"].isoformat()
        candidates.append(doc)
    return {"candidates": candidates}


@app.get("/api/candidates/{candidate_id}")
def get_candidate(candidate_id: str):
    """Get a single candidate by ID."""
    col = get_candidates_collection()
    try:
        doc = col.find_one({"_id": ObjectId(candidate_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid candidate ID")
    if not doc:
        raise HTTPException(status_code=404, detail="Candidate not found")
    doc["_id"] = str(doc["_id"])
    if isinstance(doc.get("created_at"), datetime):
        doc["created_at"] = doc["created_at"].isoformat()
    if isinstance(doc.get("updated_at"), datetime):
        doc["updated_at"] = doc["updated_at"].isoformat()
    return doc


@app.patch("/api/candidates/{candidate_id}/select")
def select_candidate(candidate_id: str, body: SelectCandidateRequest):
    """Mark a single candidate as selected + set salary."""
    col = get_candidates_collection()
    try:
        oid = ObjectId(candidate_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid candidate ID")
    result = col.update_one(
        {"_id": oid},
        {"$set": {
            "is_selected": True,
            "salary_offered": body.salary_offered,
            "updated_at": datetime.now(timezone.utc),
        }},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {"status": "selected", "candidate_id": candidate_id}


@app.post("/api/candidates/bulk-select")
def bulk_select_candidates(body: BulkSelectRequest):
    """Mark multiple candidates as selected after interview."""
    col = get_candidates_collection()
    updated = 0
    for sel in body.selections:
        cid = sel.get("candidate_id", "")
        salary = sel.get("salary_offered", 0)
        if not cid or not salary:
            continue
        try:
            result = col.update_one(
                {"_id": ObjectId(cid)},
                {"$set": {
                    "is_selected": True,
                    "salary_offered": float(salary),
                    "updated_at": datetime.now(timezone.utc),
                }},
            )
            updated += result.modified_count
        except Exception:
            continue
    return {"status": "done", "updated_count": updated}


# ===========================================================
# AGENT PIPELINE RUNNER
# ===========================================================

async def _execute_pipeline():
    """Run the ADK HR onboarding pipeline."""
    global _run_status
    try:
        _run_status = {
            "state": "running",
            "message": "Pipelines are running...",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai.types import Content, Part
        from hr_onboarding.agent import root_agent

        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="hr_onboarding",
            session_service=session_service,
        )

        session = await session_service.create_session(
            app_name="hr_onboarding",
            user_id="hr_admin",
        )

        content = Content(
            role="user",
            parts=[Part(text="Check inbox for resumes and shortlist candidates.")],
        )

        final_text = ""
        async for event in runner.run_async(
            user_id="hr_admin",
            session_id=session.id,
            new_message=content,
        ):
            print(f"DEBUG: Pipeline Event: {event}")
            if event.is_final_response() and event.content and event.content.parts:
                final_text = event.content.parts[0].text
                print(f"DEBUG: Pipeline Final Response: {final_text}")

        _run_status = {
            "state": "completed",
            "message": final_text or "All pipelines completed.",
            "started_at": _run_status["started_at"],
        }

    except Exception as e:
        import traceback
        import sys
        
        # ExceptionGroups hide the real error in str(e), so we format the full traceback
        error_msg = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        print(f"PIPELINE CRASH:\n{error_msg}", file=sys.stderr)
        
        _run_status = {
            "state": "failed",
            "message": f"Pipeline crashed. Check terminal logs for full traceback.\nSummary: {str(e)}",
            "started_at": _run_status.get("started_at"),
        }


@app.post("/api/run-agents")
async def run_agents(background_tasks: BackgroundTasks):
    """Trigger all 3 ADK pipelines in the background."""
    global _run_status
    if _run_status["state"] == "running":
        raise HTTPException(status_code=409, detail="Pipelines already running")

    _run_status = {
        "state": "running",
        "message": "Starting pipelines...",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    # Run in a background task
    loop = asyncio.get_event_loop()
    loop.create_task(_execute_pipeline())

    return {"status": "triggered"}


@app.get("/api/run-status")
def get_run_status():
    """Check the current pipeline run status."""
    return _run_status
