import os
import requests
from typing import Dict, Any, Optional

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


def ask_question(question: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Sends a question with the persistent session thread_id.
    """
    url = f"{API_BASE_URL}/chat/ask"
    payload = {"question": question}
    if thread_id:
        payload["thread_id"] = thread_id

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "answer": f"❌ Could not connect to backend at {API_BASE_URL}. Please ensure FastAPI is running.",
            "thread_id": thread_id or "",
            "hitl_event": None
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "answer": f"❌ Error communicating with backend: {str(e)}",
            "thread_id": thread_id or "",
            "hitl_event": None
        }


def resume_action(thread_id: str, approval: str) -> Dict[str, Any]:
    """
    Resumes a paused execution for the given thread_id.
    """
    url = f"{API_BASE_URL}/chat/resume"
    payload = {"thread_id": thread_id, "approval": approval}
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "answer": f"❌ Could not connect to backend at {API_BASE_URL}. Please ensure FastAPI is running.",
            "thread_id": thread_id,
            "hitl_event": None
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "answer": f"❌ Error resuming action: {str(e)}",
            "thread_id": thread_id,
            "hitl_event": None
        }