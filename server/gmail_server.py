import base64
import json
import os
from email.mime.text import MIMEText
from typing import Any, Dict

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from config.logger_config import logger

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# 1. FastMCP Server Instance
# ---------------------------------------------------------------------------
mcp = FastMCP("gmail-server")

# OAuth scopes required for Gmail read + send
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

# Fallback paths for server-level / environment credentials
CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
TOKEN_FILE       = os.getenv("GMAIL_TOKEN_PATH", "token.json")


# ---------------------------------------------------------------------------
# 2. Gmail Authentication & Service Helper
# ---------------------------------------------------------------------------
def get_gmail_service(gmail_token_json: str = ""):
    """
    Return an authenticated Gmail API service object.

    Credential resolution priority:
      1. gmail_token_json argument  — per-user token injected by the agent (from DB)
      2. GMAIL_TOKEN_JSON env var   — server-level JSON string (Render secret)
      3. token.json file            — local development file
      4. InstalledAppFlow           — interactive OAuth (local dev only)
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None

    # 1. Per-user token passed directly from the agent (highest priority)
    if gmail_token_json and gmail_token_json.strip():
        try:
            creds = Credentials.from_authorized_user_info(
                json.loads(gmail_token_json), SCOPES
            )
        except Exception as e:
            logger.warning(f"get_gmail_service | could not load per-user token: {e}")

    # 2. Server-level env var (Render secret or local .env)
    if not creds:
        token_json_str = os.getenv("GMAIL_TOKEN_JSON")
        if token_json_str:
            try:
                creds = Credentials.from_authorized_user_info(
                    json.loads(token_json_str), SCOPES
                )
            except Exception as e:
                logger.warning(f"get_gmail_service | could not load GMAIL_TOKEN_JSON: {e}")

    # 3. Local token.json file
    if not creds and os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # 4. Refresh expired credentials or run interactive OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise RuntimeError(
                    "Gmail credentials not found. "
                    "On Render: add GMAIL_TOKEN_JSON as an env var. "
                    "Locally: run auth_gmail.py first to generate token.json."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def extract_email_body(payload: Dict[str, Any]) -> str:
    """Recursively decodes base64 email body text from a Gmail payload."""
    if not payload:
        return ""

    if "parts" in payload:
        for part in payload["parts"]:
            mime_type = part.get("mimeType", "")
            if mime_type == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            elif "parts" in part:
                body = extract_email_body(part)
                if body:
                    return body
    elif payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")

    return ""


# ---------------------------------------------------------------------------
# 3. Tools — each accepts an optional gmail_token_json injected by the agent
# ---------------------------------------------------------------------------
@mcp.tool()
def search_emails(query: str, max_results: int = 5, gmail_token_json: str = "") -> str:
    """Searches emails in the Gmail inbox matching a search query.

    Args:
        query: Gmail search query syntax (e.g. 'from:boss', 'subject:meeting').
        max_results: Maximum number of emails to retrieve (default: 5).
        gmail_token_json: Per-user Gmail OAuth token JSON (injected by agent).

    Returns:
        JSON string containing the list of matching emails with headers and snippets.
    """
    logger.info(f"search_emails | query='{query}', max_results={max_results}")
    try:
        service = get_gmail_service(gmail_token_json)
        results = service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()
        messages = results.get("messages", [])

        email_list = []
        for msg_meta in messages:
            msg = service.users().messages().get(
                userId="me", id=msg_meta["id"], format="metadata"
            ).execute()
            headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
            email_list.append({
                "id": msg["id"],
                "threadId": msg.get("threadId"),
                "from": headers.get("from", "Unknown"),
                "to": headers.get("to", "Unknown"),
                "subject": headers.get("subject", "No Subject"),
                "date": headers.get("date", "Unknown"),
                "snippet": msg.get("snippet", ""),
            })

        return json.dumps({"count": len(email_list), "emails": email_list}, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Gmail API error: {str(e)}"})


@mcp.tool()
def read_email(message_id: str, gmail_token_json: str = "") -> str:
    """Retrieves the full content of a specific email by its message ID.

    Args:
        message_id: The unique identifier of the email message.
        gmail_token_json: Per-user Gmail OAuth token JSON (injected by agent).

    Returns:
        JSON string containing the full email headers, snippet, and decoded body.
    """
    logger.info(f"read_email | message_id='{message_id}'")
    try:
        service = get_gmail_service(gmail_token_json)
        msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
        headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
        body_text = extract_email_body(msg.get("payload", {}))

        return json.dumps({
            "email": {
                "id": msg["id"],
                "threadId": msg.get("threadId"),
                "from": headers.get("from", "Unknown"),
                "to": headers.get("to", "Unknown"),
                "subject": headers.get("subject", "No Subject"),
                "date": headers.get("date", "Unknown"),
                "snippet": msg.get("snippet", ""),
                "body": body_text or msg.get("snippet", ""),
            }
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to read email '{message_id}': {str(e)}"})


@mcp.tool()
def list_unread_emails(max_results: int = 5, gmail_token_json: str = "") -> str:
    """Lists recent unread emails from the inbox.

    Args:
        max_results: Maximum number of unread emails to return (default: 5).
        gmail_token_json: Per-user Gmail OAuth token JSON (injected by agent).

    Returns:
        JSON string containing unread emails.
    """
    logger.info(f"list_unread_emails | max_results={max_results}")
    return search_emails(query="is:unread", max_results=max_results, gmail_token_json=gmail_token_json)


@mcp.tool()
def send_email(to: str, subject: str, body: str, gmail_token_json: str = "") -> str:
    """Sends an email to a specified recipient via Gmail.

    Args:
        to: Email address of the recipient.
        subject: Subject line of the email.
        body: Plaintext body content of the email.
        gmail_token_json: Per-user Gmail OAuth token JSON (injected by agent).

    Returns:
        JSON string confirming the sent email or an error message.
    """
    logger.info(f"send_email | to='{to}', subject='{subject}'")
    try:
        service = get_gmail_service(gmail_token_json)
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return json.dumps({
            "status": "sent",
            "message_id": sent.get("id"),
            "thread_id": sent.get("threadId"),
            "to": to,
            "subject": subject,
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to send email: {str(e)}"})


# ---------------------------------------------------------------------------
# 4. Run Server
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(transport="stdio")
