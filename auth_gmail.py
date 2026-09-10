"""
Run this ONCE to authenticate Gmail and save token.json.
After this, the MCP server will use token.json automatically.

Usage:
    python auth_gmail.py
"""
import os
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]
CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
TOKEN_FILE = os.getenv("GMAIL_TOKEN_PATH", "token.json")


def authenticate():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None

    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no valid credentials, run the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            print(f"Opening browser for Gmail OAuth login...")
            print(f"Using credentials file: {CREDENTIALS_FILE}\n")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the token for future use
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
        print(f"\n✅ Authentication successful! Token saved to '{TOKEN_FILE}'")
    else:
        print(f"✅ Token is already valid. No re-authentication needed.")


if __name__ == "__main__":
    authenticate()
