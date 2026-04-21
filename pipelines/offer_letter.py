"""
Pipeline 2 — Offer Letter Generation

Flow: Fetch selected candidates → Generate offer letters → Draft emails
"""

from google.adk.agents import LlmAgent, SequentialAgent
from config.settings import LLM_MODEL
from tools.mongo_tools import fetch_selected_tool, update_candidate_tool
from tools.letter_tools import generate_offer_letter_tool
from tools.gmail_tools import gmail_draft_tool


# ── Step 2a: Fetch selected candidates ────────────────────
selected_candidate_fetcher_agent = LlmAgent(
    name="selected_candidate_fetcher_agent",
    model=LLM_MODEL,
    description="Fetches candidates marked as selected after interview from MongoDB.",
    instruction="""You are a candidate fetcher agent. Use the fetch_selected_candidates
tool to get all candidates where is_selected is True and offer_letter_sent is False.

List out each candidate with their:
- _id (the MongoDB ObjectId string)
- name
- email
- position_applied
- salary_offered

If no candidates are found, report "No candidates pending offer letters" and stop.""",
    tools=[fetch_selected_tool],
)


# ── Step 2b: Generate offer letters and draft emails ──────
offer_letter_drafter_agent = LlmAgent(
    name="offer_letter_drafter_agent",
    model=LLM_MODEL,
    description="Generates offer letters and drafts them as Gmail emails.",
    instruction="""You are an offer letter drafter agent. For each selected candidate
from the previous agent, do these 3 steps in order:

1. Use the generate_offer_letter tool with:
   - name: candidate's name
   - position: candidate's position_applied
   - salary: candidate's salary_offered

2. Use the gmail_draft tool to create a draft email:
   - to: candidate's email address
   - subject: "Offer Letter — [position] at Our Company"
   - body: the full offer letter text from step 1

3. Use the update_candidate_in_mongo tool to mark the offer as sent:
   - candidate_id: the candidate's _id string
   - update_fields: JSON object with key "offer_letter_sent" set to true

Repeat for each candidate. Report how many offer letters were drafted.""",
    tools=[generate_offer_letter_tool, gmail_draft_tool, update_candidate_tool],
)


# ── Pipeline assembly ─────────────────────────────────────
offer_letter_pipeline = SequentialAgent(
    name="offer_letter_pipeline",
    description="Generates and drafts offer letters for interview-selected candidates.",
    sub_agents=[
        selected_candidate_fetcher_agent,
        offer_letter_drafter_agent,
    ],
)
