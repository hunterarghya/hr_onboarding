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
from tools.imagekit_tools import upload_to_imagekit_tool


# ── Step 1a: Read inbox for application emails ────────────
inbox_reader = LlmAgent(
    name="inbox_reader",
    model=LLM_MODEL,
    description="Reads Gmail inbox for new job application emails with resume attachments.",
    instruction="""You are an inbox reader agent. Your job is to search the Gmail inbox
for new job application emails.

Use the gmail_search tool with the query: 'subject:Application has:attachment newer_than:7d' and explicitly specify max_results=2 to save tokens.

For each email found, extract and report:
- sender (email address)
- subject
- snippet
- attachments (the filepath to the downloaded PDF)

Output all of this data clearly in your final response in plain text.
If no new applications are found, report "NO_NEW_APPLICATIONS" and STOP.
IMPORTANT: Do NOT invent, hallucinate, or use example names. ONLY report real data from the tools.
IMPORTANT: Do NOT output any XML tags (like <function>). Do NOT attempt to call the next agent as a tool.
If no new applications are found, report that clearly.""",
    tools=[gmail_search_tool],
)


# ── Step 1b: Parse the resume PDF ─────────────────────────
resume_parser = LlmAgent(
    name="resume_parser",
    model=LLM_MODEL,
    description="Parses resume PDF attachments to extract text content.",
    instruction="""You are a resume parser agent. You receive email data from the
previous agent that includes PDF attachment filepaths.

For each resume PDF attachment, use the parse_pdf tool with the attachment's
filepath string to extract the text content.

If the previous agent reported "NO_NEW_APPLICATIONS", then report "NO_CANDIDATES_TO_PARSE" and STOP.

For each candidate, compile:
- candidate_email: the sender's email
- candidate_name: extracted from the resume text or email
- resume_text: the full parsed text
- resume_filepath: the original filepath from the previous agent

Output this compiled information clearly in your final response in plain text.
IMPORTANT: Do NOT invent candidates. Only process the filepaths provided by the previous agent.
IMPORTANT: Do NOT output any XML tags (like <function>). Do NOT attempt to call any unlisted tools.""",
    tools=[parse_pdf_tool],
)


# ── Step 1c: Match resume against job description ─────────
resume_matcher = LlmAgent(
    name="resume_matcher",
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

If the previous agent reported "NO_CANDIDATES_TO_PARSE", then report "NO_MATCHES_TO_SCORE" and STOP.

For each candidate, output:
- candidate_name
- candidate_email
- match_score (integer 0-10)
- brief justification (2-3 sentences)
- resume_filepath (pass it along unchanged)

Only include candidates with score >= 5 in your output for the next agent.
Clearly state which candidates are shortlisted and which are rejected.
IMPORTANT: Do NOT invent candidates. If you have no input, output "NO_MATCHES_TO_SCORE".
IMPORTANT: Do NOT output any XML tags (like <function>). Respond in plain text.""",
    tools=[],  # Pure LLM reasoning — no tools needed
)


# ── Step 1d: Save shortlisted candidates to MongoDB ───────
candidate_shortlister = LlmAgent(
    name="candidate_shortlister",
    model=LLM_MODEL,
    description="Saves shortlisted candidates (score >= 5) to MongoDB.",
    instruction=f"""You are the shortlister agent. You receive candidate match results
from the previous agent.

If the previous agent reported "NO_MATCHES_TO_SCORE" or provided no candidates, then report "DONE" and STOP.

For each candidate with a match_score >= 5, do these 2 steps:
1. Use the upload_to_imagekit tool to upload their PDF:
   - filepath: their resume_filepath
   - file_name: resume_<candidate_name>.pdf
2. Use the save_candidate_to_mongo tool:
   - name: candidate name
   - email: candidate email
   - position_applied: "{ACTIVE_ROLE}"
   - match_score: score
   - resume_url: the URL from the imagekit tool

Skip candidates with score < 5.
Report a summary: how many shortlisted vs rejected.
IMPORTANT: Do NOT invent candidates. Do NOT save example data like 'John Doe'.
IMPORTANT: Do NOT output any XML tags (like <function>). Respond in plain text.""",
    tools=[save_candidate_tool, upload_to_imagekit_tool],
)


# ── Pipeline assembly ─────────────────────────────────────
resume_screening_pipeline = SequentialAgent(
    name="resume_screening_pipeline",
    description="Screens resumes from inbox: read → parse → match → shortlist.",
    sub_agents=[
        inbox_reader,
        resume_parser,
        resume_matcher,
        candidate_shortlister,
    ],
)
