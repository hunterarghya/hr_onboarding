"""
Pipeline 3 — Document Collection & Appointment Letter

Flow: Read inbox for docs → Parse & upload to ImageKit → Draft appointment letters
"""

from google.adk.agents import LlmAgent, SequentialAgent
from config.settings import LLM_MODEL
from tools.gmail_tools import gmail_search_tool, gmail_draft_tool
from tools.pdf_tools import parse_pdf_tool
from tools.imagekit_tools import upload_to_imagekit_tool
from tools.mongo_tools import fetch_awaiting_docs_tool, update_candidate_tool
from tools.letter_tools import generate_appointment_letter_tool


# ── Step 3a: Search inbox for submitted documents ─────────
document_inbox_reader = LlmAgent(
    name="document_inbox_reader",
    model=LLM_MODEL,
    description="Searches Gmail for document submissions from selected candidates.",
    instruction="""You are a document inbox reader agent. Do these steps:

1. Use the fetch_candidates_awaiting_documents tool to get all candidates
   who received offer letters but haven't submitted documents yet.
   
2. For EACH candidate in that list, use the gmail_search tool to search for
   emails from their email address with PDF attachments:
   Query: 'from:<candidate_email> has:attachment filename:pdf'
   Explicitly specify max_results=2 to save tokens.

3. Report which candidates have sent documents (include their _id, email,
   and the attachment filepath) and which are still pending.

If no candidates are awaiting documents, report that and stop.
IMPORTANT: Do NOT output any XML tags (like <function>). Respond in plain text.""",
    tools=[gmail_search_tool, fetch_awaiting_docs_tool],
)


# ── Step 3b: Parse documents and upload to ImageKit ───────
document_processor = LlmAgent(
    name="document_processor",
    model=LLM_MODEL,
    description="Parses submitted PDFs and uploads them to ImageKit for storage.",
    instruction="""You are a document processor agent. For each candidate who sent
a document (from the previous agent's results), do these 3 steps:

1. Use the parse_pdf tool with the attachment filepath to verify
   the PDF has content.

2. Use the upload_to_imagekit tool to store the PDF:
   - filepath: the attachment's filepath
   - file_name: "pan_<candidate_name_lowercase_underscored>.pdf"

3. Use the update_candidate_in_mongo tool to update the candidate:
   - candidate_id: their _id string
   - update_fields: JSON object with "documents_submitted" as true and "document_url" as the ImageKit URL

Report which documents were processed and stored.
IMPORTANT: Do NOT output any XML tags (like <function>). Respond in plain text.""",
    tools=[parse_pdf_tool, upload_to_imagekit_tool, update_candidate_tool],
)


# ── Step 3c: Draft appointment letters ────────────────────
appointment_letter_drafter = LlmAgent(
    name="appointment_letter_drafter",
    model=LLM_MODEL,
    description="Generates appointment letters and drafts them as Gmail emails.",
    instruction="""You are an appointment letter drafter agent. For each candidate
whose documents were just processed, do these 3 steps:

1. Use the generate_appointment_letter tool with:
   - name: candidate's name
   - position: candidate's position_applied
   - salary: candidate's salary_offered

2. Use the gmail_draft tool to create a draft email:
   - to: candidate's email
   - subject: "Appointment Letter — [position] at Our Company"
   - body: the generated appointment letter text

3. Use the update_candidate_in_mongo tool:
   - candidate_id: their _id string
   - update_fields: JSON object with key "appointment_letter_sent" set to true

Report how many appointment letters were drafted.
IMPORTANT: Do NOT output any XML tags (like <function>). Respond in plain text.""",
    tools=[generate_appointment_letter_tool, gmail_draft_tool, update_candidate_tool],
)


# ── Pipeline assembly ─────────────────────────────────────
document_collection_pipeline = SequentialAgent(
    name="document_collection_pipeline",
    description="Collects documents from candidates, stores them, and drafts appointment letters.",
    sub_agents=[
        document_inbox_reader,
        document_processor,
        appointment_letter_drafter,
    ],
)
