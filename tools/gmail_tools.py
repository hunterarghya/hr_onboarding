"""
Gmail tools — search inbox and draft emails.

Credentials come from the Google OAuth login flow stored in MongoDB.
"""

import re
import base64
import os
import uuid
import tempfile
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.adk.tools import FunctionTool

from config.settings import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from db.connection import get_db


def _get_gmail_service():
    """Build an authenticated Gmail API service from the OAuth token in MongoDB."""
    users_col = get_db()["users"]
    user = users_col.find_one(sort=[("last_login", -1)])

    if not user or "google_token" not in user:
        raise RuntimeError(
            "No Google OAuth token found in database. "
            "Please login via the dashboard first (Login with Google)."
        )

    google_token = user["google_token"]

    # Build credentials from the stored OAuth token
    creds_info = {
        "token": google_token.get("access_token"),
        "refresh_token": google_token.get("refresh_token"),
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "scopes": (
            google_token.get("scope", "").split()
            if isinstance(google_token.get("scope"), str)
            else google_token.get("scope", [])
        ),
    }

    creds = Credentials.from_authorized_user_info(creds_info)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build("gmail", "v1", credentials=creds)


def _extract_email(sender: str) -> str:
    """Extract email address from a 'Name <email>' formatted string."""
    match = re.search(r"<(.+?)>", sender)
    return match.group(1) if match else sender.strip()


def gmail_search(query: str, max_results: int = 10) -> dict:
    """Search Gmail inbox for messages matching a query.

    Args:
        query: Gmail search query string
               (e.g. 'subject:Application has:attachment newer_than:7d').
        max_results: Maximum number of results to return.

    Returns:
        Dictionary with key 'messages' containing a list of email dicts,
        each with id, sender, subject, snippet, and attachments.
    """
    service = _get_gmail_service()
    print(f"DEBUG: Searching Gmail with query: '{query}'")
    results = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()
    messages = results.get("messages", [])
    print(f"DEBUG: Found {len(messages)} potential messages.")

    if not messages:
        return {"messages": [], "count": 0}

    emails = []
    for msg_ref in messages:
        print(f"DEBUG: Processing message ID: {msg_ref['id']}")
        msg = service.users().messages().get(
            userId="me", id=msg_ref["id"], format="full"
        ).execute()
        headers = msg.get("payload", {}).get("headers", [])

        subject = next(
            (h["value"] for h in headers if h["name"] == "Subject"), "No Subject"
        )
        sender_raw = next(
            (h["value"] for h in headers if h["name"] == "From"), "Unknown"
        )
        sender = _extract_email(sender_raw)

        # Extract attachments
        attachments = []
        parts = msg.get("payload", {}).get("parts", [])
        for part in parts:
            filename = part.get("filename", "")
            if filename and part.get("body", {}).get("attachmentId"):
                att = service.users().messages().attachments().get(
                    userId="me", messageId=msg_ref["id"],
                    id=part["body"]["attachmentId"]
                ).execute()
                att_data = att.get("data", "")
                
                filepath = ""
                if att_data:
                    file_bytes = base64.urlsafe_b64decode(att_data)
                    
                    storage_dir = "temp_resumes"
                    if not os.path.exists(storage_dir):
                        os.makedirs(storage_dir)
                        
                    filepath = os.path.abspath(os.path.join(storage_dir, f"{uuid.uuid4()}_{filename}"))
                    with open(filepath, "wb") as f:
                        f.write(file_bytes)
                    print(f"DEBUG: Saved attachment to: {filepath}")

                attachments.append({
                    "filename": filename,
                    "filepath": filepath,
                    "mime_type": part.get("mimeType", ""),
                })

        print(f"DEBUG: Email from {sender} has {len(attachments)} attachments.")
        emails.append({
            "id": msg_ref["id"],
            "sender": sender,
            "subject": subject,
            "snippet": msg.get("snippet", ""),
            "attachments": attachments,
        })

    print(f"DEBUG: Gmail search complete. Returning {len(emails)} emails.")
    return {"messages": emails, "count": len(emails)}


def gmail_draft(to: str, subject: str, body: str) -> dict:
    """Create a draft email in Gmail (does NOT send it).

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Email body text.

    Returns:
        Dictionary with draft status and draft ID.
    """
    service = _get_gmail_service()

    message = EmailMessage()
    message.set_content(body)
    message["To"] = to
    message["From"] = "me"
    message["Subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    draft = service.users().drafts().create(
        userId="me", body={"message": {"raw": raw}}
    ).execute()

    return {
        "status": "drafted",
        "draft_id": draft.get("id", ""),
        "to": to,
        "subject": subject,
    }


# ── ADK FunctionTool wrappers ─────────────────────────────
gmail_search_tool = FunctionTool(func=gmail_search)
gmail_draft_tool = FunctionTool(func=gmail_draft)
