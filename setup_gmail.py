"""
One-time Gmail OAuth2 setup script.

Prerequisites:
  1. Go to Google Cloud Console → APIs & Services → Credentials
  2. Create an OAuth 2.0 Client ID (Desktop application)
  3. Download the JSON and save as 'credentials.json' in this directory

Usage:
  python setup_gmail.py

This will open a browser for Google login, then save the token to token.json.
After that, the ADK agents can access Gmail automatically.
"""

import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def main():
    print("=== Gmail OAuth2 Setup ===")
    print("This will open your browser for Google authorization.\n")

    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)

    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "scopes": creds.scopes if isinstance(creds.scopes, list) else list(creds.scopes),
    }

    with open("token.json", "w") as f:
        json.dump(token_data, f, indent=2)

    print("\n✅ Token saved to token.json")
    print("You can now run the HR onboarding agents.")


if __name__ == "__main__":
    main()
