"""
Pipeline 1 — Resume Screening (Optimized Version)

Flow: Read inbox → Match (LLM) → Finalize (Python)
"""

from google.adk.agents import LlmAgent, SequentialAgent
from config.settings import LLM_MODEL
from config.job_descriptions import JOB_DESCRIPTIONS, ACTIVE_ROLE
from tools.gmail_tools import gmail_search_tool
from tools.pdf_tools import parse_pdf_tool
from tools.pipeline_tools import finalize_shortlist_tool


STRICT_OFFLINE_INSTRUCTION = "CRITICAL: Use ONLY provided tools. Do NOT hallucinate data."


# ── Step 1: Read inbox ────────────
inbox_reader = LlmAgent(
    name="inbox_reader",
    model=LLM_MODEL,
    description="Reads Gmail inbox.",
    instruction="""CRITICAL: You have ONLY ONE tool: 'gmail_search'. 
DO NOT attempt to use any other tool (like 'brute_force_search' or 'web_search').
If you need to find resumes, you MUST call gmail_search(query='has:attachment newer_than:7d', max_results=2).
After calling it, list the results. If none, say "NO_NEW_APPLICATIONS".""",
    tools=[gmail_search_tool],
)


# ── Step 2: Match & Finalize ─────────
resume_matcher = LlmAgent(
    name="resume_matcher",
    model=LLM_MODEL,
    description="Scores resumes and triggers final save.",
    instruction=STRICT_OFFLINE_INSTRUCTION + f"""
IMPORTANT: You ONLY have 'parse_pdf' and 'finalize_shortlist' tools. You do NOT have 'gmail_search'.
If the previous agent said "NO_NEW_APPLICATIONS", say "STOP" and end.

1. Call parse_pdf for EVERY candidate filepath provided.
2. Compare to this JD: {JOB_DESCRIPTIONS[ACTIVE_ROLE]}
3. If score >= 5, call finalize_shortlist(candidates=[...]).
4. After calling tools, say "DONE".""",
    tools=[parse_pdf_tool, finalize_shortlist_tool],
)


# ── Pipeline assembly ─────────────────────────────────────
resume_screening_pipeline = SequentialAgent(
    name="resume_screening_pipeline",
    description="Screens resumes: read → match → save (Python).",
    sub_agents=[
        inbox_reader,
        resume_matcher,
    ],
)
