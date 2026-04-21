"""
Pipeline 1 — Resume Screening

Flow: Read inbox → Parse PDF → Match against JD → Shortlist to MongoDB
"""

from google.adk.agents import LlmAgent, SequentialAgent
from config.settings import LLM_MODEL
from config.job_descriptions import JOB_DESCRIPTIONS, ACTIVE_ROLE
from tools.gmail_tools import gmail_search_tool
from tools.pdf_tools import parse_pdf_tool
from tools.mongo_tools import save_candidate_tool


# ── Step 1a: Read inbox for application emails ────────────
inbox_reader_agent = LlmAgent(
    name="inbox_reader_agent",
    model=LLM_MODEL,
    description="Reads Gmail inbox for new job application emails with resume attachments.",
    instruction="""You are an inbox reader agent. Your job is to search the Gmail inbox
for new job application emails.

Use the gmail_search tool with the query: 'subject:Application has:attachment newer_than:7d'

For each email found, extract and report:
- sender (email address)
- subject
- snippet
- attachments (the filepath to the downloaded PDF)

Pass all of this data forward so the next agent can parse the resumes.
If no new applications are found, report that clearly.""",
    tools=[gmail_search_tool],
)


# ── Step 1b: Parse the resume PDF ─────────────────────────
resume_parser_agent = LlmAgent(
    name="resume_parser_agent",
    model=LLM_MODEL,
    description="Parses resume PDF attachments to extract text content.",
    instruction="""You are a resume parser agent. You receive email data from the
previous agent that includes PDF attachment filepaths.

For each resume PDF attachment, use the parse_pdf tool with the attachment's
filepath string to extract the text content.

For each candidate, compile:
- candidate_email: the sender's email
- candidate_name: extracted from the resume text or email
- resume_text: the full parsed text

Pass this information forward for matching.""",
    tools=[parse_pdf_tool],
)


# ── Step 1c: Match resume against job description ─────────
resume_matcher_agent = LlmAgent(
    name="resume_matcher_agent",
    model=LLM_MODEL,
    description="Scores how well a parsed resume matches the job description.",
    instruction=f"""You are a resume matching agent. You receive parsed resume text
and candidate details from the previous agent.

Compare each resume against this JOB DESCRIPTION:

---
{JOB_DESCRIPTIONS[ACTIVE_ROLE]}
---

Score the match from 0 to 10 based on:
- Relevant skills match (4 points): backend frameworks, API dev, databases
- Experience level match (3 points): years, seniority, project complexity
- Education match (2 points): B.Tech/B.E. or equivalent
- Overall fit (1 point): communication, culture fit signals

For each candidate, output:
- candidate_name
- candidate_email
- match_score (integer 0-10)
- brief justification (2-3 sentences)

Only forward candidates with score >= 5 to the next agent.
Clearly state which candidates are shortlisted and which are rejected.""",
    tools=[],  # Pure LLM reasoning — no tools needed
)


# ── Step 1d: Save shortlisted candidates to MongoDB ───────
candidate_shortlister_agent = LlmAgent(
    name="candidate_shortlister_agent",
    model=LLM_MODEL,
    description="Saves shortlisted candidates (score >= 5) to MongoDB.",
    instruction=f"""You are the shortlister agent. You receive candidate match results
from the previous agent.

For each candidate with a match_score >= 5, use the save_candidate_to_mongo tool
to store them in the database with these exact parameters:
- name: the candidate's full name
- email: the candidate's email address
- position_applied: "{ACTIVE_ROLE}"
- match_score: their score (as a float)

Skip candidates with score < 5 and list them as rejected.
Report a summary: how many shortlisted vs rejected.""",
    tools=[save_candidate_tool],
)


# ── Pipeline assembly ─────────────────────────────────────
resume_screening_pipeline = SequentialAgent(
    name="resume_screening_pipeline",
    description="Screens resumes from inbox: read → parse → match → shortlist.",
    sub_agents=[
        inbox_reader_agent,
        resume_parser_agent,
        resume_matcher_agent,
        candidate_shortlister_agent,
    ],
)
