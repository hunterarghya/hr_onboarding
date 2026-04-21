"""
Entry point — run the FastAPI server.

Usage:
    python run.py

This starts the HR dashboard at http://localhost:8000
The ADK agents are run separately via:
    adk run  hr_onboarding
    adk web  hr_onboarding
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
