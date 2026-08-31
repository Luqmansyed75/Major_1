import base64
import json
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# 1. FastMCP Server Instance
# ---------------------------------------------------------------------------
mcp = FastMCP("gmail-server")

# OAuth Configuration
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]
CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
TOKEN_FILE = os.getenv("GMAIL_TOKEN_PATH", "token.json")
USE_MOCK = os.getenv("USE_MOCK_GMAIL", "false").lower() in ("true", "1", "yes")


# ---------------------------------------------------------------------------
# Mock Data for Sandbox / Offline Testing
# ---------------------------------------------------------------------------
MOCK_EMAILS = [
    {
        "id": "msg_001",
        "threadId": "thread_001",
        "from": "santhosh.kumar@rgukt.ac.in",
        "to": "luqmansyed75@gmail.com",
        "subject": "Major Project 1: Live Rag - Eval Review Schedule",
        "date": "2026-08-25 10:30:00",
        "unread": True,
        "snippet": "Please submit your v1 LangGraph architecture and MCP integration progress by Friday...",
        "body": (
            "Hi Luqman and Manoj,\n\n"
            "Please ensure your Live Rag - Eval architecture documentation and initial v1 "
            "LangGraph workflow are ready for the upcoming internal review this Friday at 3 PM.\n\n"
            "Best regards,\n"
            "Dr. P. Santhosh Kumar\n"
            "Assistant Professor, RGUKT RK Valley"
        )
    },
    {
        "id": "msg_002",
        "threadId": "thread_002",
        "from": "eng-lead@techcorp.io",
        "to": "luqmansyed75@gmail.com",
        "subject": "Sprint Update: Q3 Deliverables and Blockers",
        "date": "2026-08-26 15:45:00",
        "unread": False,
        "snippet": "Jira ticket DEV-402 is currently blocked pending OAuth verification approval...",
        "body": (
            "Team,\n\n"
            "Quick update on sprint goals: We have 12 key tasks scheduled for this quarter. "
            "Two deadlines were updated last week. Jira ticket DEV-402 is currently blocked "
            "pending OAuth verification scopes. Notion PRD docs have been updated.\n\n"
            "Cheers,\nEngineering Team"
        )
    },
    {
        "id": "msg_003",
        "threadId": "thread_003",
        "from": "security-alerts@domain.com",
        "to": "luqmansyed75@gmail.com",
        "subject": "Security Notice: API Token Rotation Required",
        "date": "2026-08-27 09:15:00",
        "unread": True,
        "snippet": "Your developer API tokens for external integrations are due for quarterly rotation...",
        "body": (
            "Hello,\n\n"
            "This is an automated reminder that developer API credentials and session keys "
            "should be rotated regularly to adhere to enterprise security policies.\n\n"
            "Security Operations"
        )
    }
]


# ---------------------------------------------------------------------------
# 2. Gmail Authentication & Service Helper
# ---------------------------------------------------------------------------
def get_gmail_service():
    """Initializes and returns the Gmail API service, or None if in mock mode."""
    if USE_MOCK:
        return None

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif os.path.exists(CREDENTIALS_FILE):
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
                with open(TOKEN_FILE, "w") as token:
                    token.write(creds.to_json())
            else:
                # Fallback to mock mode if credentials.json is not present
                return None

        return build("gmail", "v1", credentials=creds)
    except Exception:
        return None


def extract_email_body(payload: Dict[str, Any]) -> str:
    """Helper to decode base64 email body text."""
    if not payload:
        return ""

    body_data = ""
    if "parts" in payload:
        for part in payload["parts"]:
            mime_type = part.get("mimeType", "")
            if mime_type == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body_data = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    break
            elif "parts" in part:
                body_data = extract_email_body(part)
                if body_data:
                    break
    elif "body" in payload and payload["body"].get("data"):
        data = payload["body"]["data"]
        body_data = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    return body_data


# ---------------------------------------------------------------------------
# 3. Register FastMCP Tools
# ---------------------------------------------------------------------------
@mcp.tool()
def search_emails(query: str, max_results: int = 5) -> str:
    """Searches emails in the Gmail inbox matching a search query.
    
    Args:
        query: Gmail search query syntax (e.g. 'from:boss', 'subject:meeting', 'project deadline').
        max_results: Maximum number of emails to retrieve (default: 5).
    
    Returns:
        JSON string containing the list of matching emails with headers and snippets.
    """
    service = get_gmail_service()

    # --- Live Gmail API Execution ---
    if service is not None:
        try:
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
                    "snippet": msg.get("snippet", "")
                })

            return json.dumps({"source": "live_gmail", "count": len(email_list), "emails": email_list}, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Gmail API error: {str(e)}"})

    # --- Mock Sandbox Fallback ---
    q_lower = query.lower()
    filtered = [
        email for email in MOCK_EMAILS
        if q_lower in email["subject"].lower()
        or q_lower in email["snippet"].lower()
        or q_lower in email["from"].lower()
        or q_lower in email["body"].lower()
        or query == ""
        or query == "is:unread"
    ][:max_results]

    return json.dumps({
        "source": "mock_sandbox",
        "note": "Using mock data (credentials.json not found or USE_MOCK_GMAIL=true)",
        "count": len(filtered),
        "emails": filtered
    }, indent=2)


@mcp.tool()
def read_email(message_id: str) -> str:
    """Retrieves the full content and details of a specific email by its message ID.
    
    Args:
        message_id: The unique identifier of the email message.
        
    Returns:
        JSON string containing the full email headers, snippet, and decoded body.
    """
    service = get_gmail_service()

    # --- Live Gmail API Execution ---
    if service is not None:
        try:
            msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
            headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
            body_text = extract_email_body(msg.get("payload", {}))

            email_details = {
                "id": msg["id"],
                "threadId": msg.get("threadId"),
                "from": headers.get("from", "Unknown"),
                "to": headers.get("to", "Unknown"),
                "subject": headers.get("subject", "No Subject"),
                "date": headers.get("date", "Unknown"),
                "snippet": msg.get("snippet", ""),
                "body": body_text if body_text else msg.get("snippet", "")
            }
            return json.dumps({"source": "live_gmail", "email": email_details}, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to read email {message_id}: {str(e)}"})

    # --- Mock Sandbox Fallback ---
    for email in MOCK_EMAILS:
        if email["id"] == message_id:
            return json.dumps({"source": "mock_sandbox", "email": email}, indent=2)

    return json.dumps({"error": f"Email with ID '{message_id}' not found."})


@mcp.tool()
def list_unread_emails(max_results: int = 5) -> str:
    """Lists recent unread emails from the inbox.
    
    Args:
        max_results: Maximum number of unread emails to return (default: 5).
        
    Returns:
        JSON string containing unread emails.
    """
    return search_emails(query="is:unread", max_results=max_results)


@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """Sends an email to a specified recipient via Gmail.

    Args:
        to: Email address of the recipient.
        subject: Subject line of the email.
        body: Plaintext body content of the email.

    Returns:
        JSON string confirming the sent email or an error message.
    """
    from email.mime.text import MIMEText

    service = get_gmail_service()

    # --- Live Gmail API Execution ---
    if service is not None:
        try:
            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            sent = service.users().messages().send(
                userId="me", body={"raw": raw}
            ).execute()
            return json.dumps({
                "source": "live_gmail",
                "status": "sent",
                "message_id": sent.get("id"),
                "thread_id": sent.get("threadId"),
                "to": to,
                "subject": subject,
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to send email: {str(e)}"})

    # --- Mock Sandbox Fallback ---
    return json.dumps({
        "source": "mock_sandbox",
        "status": "sent (simulated)",
        "note": "Email was not actually sent (mock mode active)",
        "to": to,
        "subject": subject,
        "body": body,
    }, indent=2)


# ---------------------------------------------------------------------------
# 4. Server Execution Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Runs the MCP server using standard I/O (stdio) transport
    mcp.run(transport="stdio")

