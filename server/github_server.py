import base64
import json
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
import httpx
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# 1. FastMCP Server Instance
# ---------------------------------------------------------------------------
mcp = FastMCP("github-server")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_API_BASE = os.getenv("GITHUB_API_BASE", "https://api.github.com").rstrip("/")
USE_MOCK = os.getenv("USE_MOCK_GITHUB", "false").lower() in ("true", "1", "yes")

# ---------------------------------------------------------------------------
# Mock Data for Sandbox / Offline Testing
# ---------------------------------------------------------------------------
MOCK_REPOSITORIES = [
    {
        "id": 101,
        "name": "Major_1",
        "full_name": "Luqmansyed75/Major_1",
        "owner": "Luqmansyed75",
        "description": "Enterprise Agentic RAG System with MCP and LangGraph",
        "stars": 14,
        "forks": 3,
        "open_issues_count": 4,
        "default_branch": "main",
        "language": "Python",
        "html_url": "https://github.com/Luqmansyed75/Major_1",
    },
    {
        "id": 102,
        "name": "live-rag-eval",
        "full_name": "techcorp/live-rag-eval",
        "owner": "techcorp",
        "description": "Automated CI/CD evaluation framework for MCP and live tool grounding",
        "stars": 88,
        "forks": 12,
        "open_issues_count": 2,
        "default_branch": "main",
        "language": "Python",
        "html_url": "https://github.com/techcorp/live-rag-eval",
    },
    {
        "id": 103,
        "name": "fastmcp-integrations",
        "full_name": "modelcontextprotocol/fastmcp-integrations",
        "owner": "modelcontextprotocol",
        "description": "Collection of FastMCP server reference implementations",
        "stars": 420,
        "forks": 65,
        "open_issues_count": 8,
        "default_branch": "main",
        "language": "Python",
        "html_url": "https://github.com/modelcontextprotocol/fastmcp-integrations",
    },
]

MOCK_ISSUES = [
    {
        "number": 1,
        "repo": "Luqmansyed75/Major_1",
        "title": "Add GitHub MCP Server for repository queries",
        "state": "open",
        "user": "Luqmansyed75",
        "created_at": "2026-08-28T10:00:00Z",
        "body": "We need to build a GitHub FastMCP server with client and graph integrations for Live Rag.",
        "labels": ["enhancement", "mcp"],
        "comments": 2,
    },
    {
        "number": 2,
        "repo": "Luqmansyed75/Major_1",
        "title": "Implement automated evaluation pipeline for LangGraph state",
        "state": "open",
        "user": "santhosh-kumar",
        "created_at": "2026-08-29T14:30:00Z",
        "body": "Set up evaluation scenarios comparing ground-truth answers with live tool outputs.",
        "labels": ["evaluation", "high-priority"],
        "comments": 1,
    },
    {
        "number": 12,
        "repo": "techcorp/live-rag-eval",
        "title": "Fix token refresh timeout on long-running MCP queries",
        "state": "open",
        "user": "eng-lead",
        "created_at": "2026-08-27T08:15:00Z",
        "body": "OAuth token refresh intermittently causes a timeout on large payload fetches.",
        "labels": ["bug"],
        "comments": 3,
    },
]

MOCK_PRS = [
    {
        "number": 3,
        "repo": "Luqmansyed75/Major_1",
        "title": "feat: Add Gmail MCP integration and interactive tester",
        "state": "open",
        "user": "Luqmansyed75",
        "created_at": "2026-08-29T16:00:00Z",
        "head_branch": "feature/gmail-mcp",
        "base_branch": "main",
        "body": "Adds FastMCP server for Gmail search and read actions with offline mock fallback.",
    },
    {
        "number": 4,
        "repo": "Luqmansyed75/Major_1",
        "title": "feat: GitHub MCP server and client integration",
        "state": "open",
        "user": "Luqmansyed75",
        "created_at": "2026-08-30T12:00:00Z",
        "head_branch": "feature/github-mcp",
        "base_branch": "main",
        "body": "Implements github_server.py and github_client.py connected to LangGraph workflow.",
    },
]

MOCK_FILES = {
    ("Luqmansyed75/Major_1", "README.md", "main"): (
        "# Major 1: Live Rag - Eval\n\n"
        "Enterprise-grade Agentic RAG system with Model Context Protocol (MCP) and LangGraph."
    ),
    ("Luqmansyed75/Major_1", "agent.md", "main"): (
        "# Agent Profile: Live Rag - Eval\n\n"
        "Safety guardrails, MCP tools (Gmail, GitHub, Notion, Jira), and LangGraph evaluation."
    ),
}


# ---------------------------------------------------------------------------
# 2. HTTP Helper for GitHub API
# ---------------------------------------------------------------------------
def _get_github_headers() -> Dict[str, str]:
    """Generates standard GitHub API request headers."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "FastMCP-GitHub-Server",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def _is_live_available() -> bool:
    """Returns True if live GitHub API is configured and mock mode is not forced."""
    return bool(GITHUB_TOKEN) and not USE_MOCK


# ---------------------------------------------------------------------------
# 3. Register FastMCP Tools
# ---------------------------------------------------------------------------
@mcp.tool()
def search_repositories(query: str, max_results: int = 5) -> str:
    """Searches GitHub repositories matching a keyword, topic, or query string.
    
    Args:
        query: Search keyword or query (e.g. 'Live Rag', 'user:Luqmansyed75', 'FastMCP').
        max_results: Maximum number of repositories to return (default: 5).
        
    Returns:
        JSON string containing the repository list with details.
    """
    if _is_live_available():
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(
                    f"{GITHUB_API_BASE}/search/repositories",
                    headers=_get_github_headers(),
                    params={"q": query, "per_page": max_results},
                )
                res.raise_for_status()
                data = res.json()
                items = data.get("items", [])
                repos = [
                    {
                        "name": item.get("name"),
                        "full_name": item.get("full_name"),
                        "owner": item.get("owner", {}).get("login"),
                        "description": item.get("description"),
                        "stars": item.get("stargazers_count"),
                        "forks": item.get("forks_count"),
                        "open_issues": item.get("open_issues_count"),
                        "language": item.get("language"),
                        "url": item.get("html_url"),
                    }
                    for item in items[:max_results]
                ]
                return json.dumps(
                    {"source": "live_github", "count": len(repos), "repositories": repos},
                    indent=2,
                )
        except Exception as e:
            return json.dumps({"error": f"Live GitHub API error: {str(e)}"})

    # --- Sandbox Mock Fallback ---
    q_lower = query.lower()
    filtered = [
        repo
        for repo in MOCK_REPOSITORIES
        if q_lower in repo["name"].lower()
        or q_lower in repo["full_name"].lower()
        or q_lower in repo["description"].lower()
        or query == ""
    ][:max_results]

    return json.dumps(
        {
            "source": "mock_sandbox",
            "note": "Using mock data (GITHUB_TOKEN not provided or USE_MOCK_GITHUB=true)",
            "count": len(filtered),
            "repositories": filtered,
        },
        indent=2,
    )


@mcp.tool()
def list_issues(owner: str, repo: str, state: str = "open", max_results: int = 5) -> str:
    """Lists issues from a specific GitHub repository.
    
    Args:
        owner: Repository owner/organization (e.g. 'Luqmansyed75').
        repo: Repository name (e.g. 'Major_1').
        state: State of issues to fetch ('open', 'closed', or 'all'). Default: 'open'.
        max_results: Maximum number of issues to return (default: 5).
        
    Returns:
        JSON string containing the list of issues with metadata.
    """
    repo_full_name = f"{owner}/{repo}".lower()

    if _is_live_available():
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(
                    f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
                    headers=_get_github_headers(),
                    params={"state": state, "per_page": max_results},
                )
                res.raise_for_status()
                items = res.json()
                issues = [
                    {
                        "number": item.get("number"),
                        "title": item.get("title"),
                        "state": item.get("state"),
                        "user": item.get("user", {}).get("login"),
                        "created_at": item.get("created_at"),
                        "body": (item.get("body") or "")[:300],
                        "labels": [label.get("name") for label in item.get("labels", [])],
                        "is_pull_request": "pull_request" in item,
                        "url": item.get("html_url"),
                    }
                    for item in items[:max_results]
                ]
                return json.dumps(
                    {"source": "live_github", "repository": f"{owner}/{repo}", "count": len(issues), "issues": issues},
                    indent=2,
                )
        except Exception as e:
            return json.dumps({"error": f"Live GitHub API error: {str(e)}"})

    # --- Sandbox Mock Fallback ---
    filtered = [
        issue
        for issue in MOCK_ISSUES
        if issue["repo"].lower() == repo_full_name
        and (state == "all" or issue["state"].lower() == state.lower())
    ][:max_results]

    return json.dumps(
        {
            "source": "mock_sandbox",
            "repository": f"{owner}/{repo}",
            "note": "Using mock data (GITHUB_TOKEN not provided or USE_MOCK_GITHUB=true)",
            "count": len(filtered),
            "issues": filtered,
        },
        indent=2,
    )


@mcp.tool()
def get_issue(owner: str, repo: str, issue_number: int) -> str:
    """Gets complete details, full body, and status of a specific GitHub issue or pull request.
    
    Args:
        owner: Repository owner/organization.
        repo: Repository name.
        issue_number: Issue or pull request number.
        
    Returns:
        JSON string containing detailed issue content.
    """
    repo_full_name = f"{owner}/{repo}".lower()

    if _is_live_available():
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(
                    f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{issue_number}",
                    headers=_get_github_headers(),
                )
                res.raise_for_status()
                item = res.json()
                issue_data = {
                    "number": item.get("number"),
                    "title": item.get("title"),
                    "state": item.get("state"),
                    "user": item.get("user", {}).get("login"),
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at"),
                    "body": item.get("body") or "",
                    "labels": [l.get("name") for l in item.get("labels", [])],
                    "comments_count": item.get("comments", 0),
                    "url": item.get("html_url"),
                }
                return json.dumps({"source": "live_github", "issue": issue_data}, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Live GitHub API error: {str(e)}"})

    # --- Sandbox Mock Fallback ---
    for issue in MOCK_ISSUES:
        if issue["repo"].lower() == repo_full_name and issue["number"] == issue_number:
            return json.dumps({"source": "mock_sandbox", "issue": issue}, indent=2)

    return json.dumps({"error": f"Issue #{issue_number} in '{owner}/{repo}' not found."})


@mcp.tool()
def list_pull_requests(owner: str, repo: str, state: str = "open", max_results: int = 5) -> str:
    """Lists pull requests for a specific GitHub repository.
    
    Args:
        owner: Repository owner/organization.
        repo: Repository name.
        state: State of PRs ('open', 'closed', or 'all'). Default: 'open'.
        max_results: Maximum number of PRs to retrieve (default: 5).
        
    Returns:
        JSON string containing the pull requests.
    """
    repo_full_name = f"{owner}/{repo}".lower()

    if _is_live_available():
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(
                    f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls",
                    headers=_get_github_headers(),
                    params={"state": state, "per_page": max_results},
                )
                res.raise_for_status()
                items = res.json()
                prs = [
                    {
                        "number": item.get("number"),
                        "title": item.get("title"),
                        "state": item.get("state"),
                        "user": item.get("user", {}).get("login"),
                        "created_at": item.get("created_at"),
                        "head_branch": item.get("head", {}).get("ref"),
                        "base_branch": item.get("base", {}).get("ref"),
                        "body": (item.get("body") or "")[:300],
                        "url": item.get("html_url"),
                    }
                    for item in items[:max_results]
                ]
                return json.dumps(
                    {"source": "live_github", "repository": f"{owner}/{repo}", "count": len(prs), "pull_requests": prs},
                    indent=2,
                )
        except Exception as e:
            return json.dumps({"error": f"Live GitHub API error: {str(e)}"})

    # --- Sandbox Mock Fallback ---
    filtered = [
        pr
        for pr in MOCK_PRS
        if pr["repo"].lower() == repo_full_name
        and (state == "all" or pr["state"].lower() == state.lower())
    ][:max_results]

    return json.dumps(
        {
            "source": "mock_sandbox",
            "repository": f"{owner}/{repo}",
            "note": "Using mock data (GITHUB_TOKEN not provided or USE_MOCK_GITHUB=true)",
            "count": len(filtered),
            "pull_requests": filtered,
        },
        indent=2,
    )


@mcp.tool()
def get_file_content(owner: str, repo: str, path: str, ref: str = "main") -> str:
    """Reads the text content of a file from a GitHub repository at a given ref/branch.
    
    Args:
        owner: Repository owner/organization.
        repo: Repository name.
        path: File path within the repository (e.g. 'README.md', 'src/main.py').
        ref: Git branch, tag, or commit SHA (default: 'main').
        
    Returns:
        JSON string containing the decoded file content.
    """
    repo_key = (f"{owner}/{repo}", path, ref)

    if _is_live_available():
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(
                    f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}",
                    headers=_get_github_headers(),
                    params={"ref": ref},
                )
                res.raise_for_status()
                data = res.json()
                if "content" in data and data.get("encoding") == "base64":
                    content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
                    return json.dumps(
                        {
                            "source": "live_github",
                            "repository": f"{owner}/{repo}",
                            "path": path,
                            "ref": ref,
                            "size": data.get("size"),
                            "content": content,
                        },
                        indent=2,
                    )
                else:
                    return json.dumps({"error": f"Path '{path}' is not a file or encoding is not base64."})
        except Exception as e:
            return json.dumps({"error": f"Live GitHub API error: {str(e)}"})

    # --- Sandbox Mock Fallback ---
    for (mock_repo, mock_path, mock_ref), content in MOCK_FILES.items():
        if mock_repo.lower() == f"{owner}/{repo}".lower() and mock_path == path:
            return json.dumps(
                {
                    "source": "mock_sandbox",
                    "repository": f"{owner}/{repo}",
                    "path": path,
                    "ref": ref,
                    "content": content,
                },
                indent=2,
            )

    return json.dumps({"error": f"File '{path}' in repository '{owner}/{repo}' (ref: {ref}) not found in sandbox."})


# ---------------------------------------------------------------------------
# 4. Server Execution Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(transport="stdio")
