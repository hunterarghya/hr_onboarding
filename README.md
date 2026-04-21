# HR Onboarding — Multi-Agent Workflow

Automated HR onboarding system built with **Google ADK**, **FastAPI**, **MongoDB**, and plain **HTML/JS**.

## Architecture

```
ParallelAgent (root)
├── Pipeline 1: Resume Screening     (SequentialAgent → 4 LlmAgents)
├── Pipeline 2: Offer Letter          (SequentialAgent → 2 LlmAgents)
└── Pipeline 3: Document Collection   (SequentialAgent → 3 LlmAgents)
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy and fill environment variables
cp .env.example .env

# 3. Start MongoDB (must be running)
# 4. Start the FastAPI dashboard
python run.py

# 5. Run the ADK agents (separate terminal)
adk run hr_onboarding
# or use the ADK web UI:
adk web hr_onboarding
```

## Project Structure

```
hr/
├── .env.example            # Environment variable template
├── requirements.txt        # Python dependencies
├── run.py                  # FastAPI entry point
├── config/                 # Settings and job descriptions
├── db/                     # MongoDB connection and schema docs
├── templates/              # Offer / appointment letter templates
├── tools/                  # ADK FunctionTool wrappers
├── pipelines/              # 3 SequentialAgent pipeline definitions
├── hr_onboarding/          # ADK agent entry point (root_agent)
├── api/                    # FastAPI backend
└── static/                 # HTML/JS frontend
```
