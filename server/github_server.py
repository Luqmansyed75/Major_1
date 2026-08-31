import base64
import json
import os

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

# ---------------------------------------------------------------------------
# 1. Initialize MCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP("github-server")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
API = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "LiveRag-MCP",
    **({"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}),
}


# ---------------------------------------------------------------------------
# 2. Register GitHub Tools
# ---------------------------------------------------------------------------
@mcp.tool()
def search_repositories(query: str, max_results: int = 5) -> str:
    """Search GitHub repositories by keyword, topic, or user.

    Args:
        query: Search query (e.g. 'langchain', 'user:Luqmansyed75', 'topic:mcp').
        max_results: Maximum repositories to return (default: 5).
    """
    res = httpx.get(
        f"{API}/search/repositories",
        headers=HEADERS,
        params={"q": query, "per_page": max_results},
        timeout=10.0,
    )
    res.raise_for_status()
    repos = [
        {
            "name": r["name"],
            "full_name": r["full_name"],
            "owner": r["owner"]["login"],
            "description": r.get("description"),
            "stars": r["stargazers_count"],
            "forks": r["forks_count"],
            "language": r.get("language"),
            "url": r["html_url"],
        }
        for r in res.json().get("items", [])[:max_results]
    ]
    return json.dumps({"count": len(repos), "repositories": repos}, indent=2)


@mcp.tool()
def get_repository(owner: str, repo: str) -> str:
    """Get detailed metadata of a specific repository.

    Args:
        owner: Repository owner or organization (e.g. 'Luqmansyed75').
        repo: Repository name (e.g. 'Major_1').
    """
    res = httpx.get(f"{API}/repos/{owner}/{repo}", headers=HEADERS, timeout=10.0)
    res.raise_for_status()
    r = res.json()
    return json.dumps(
        {
            "name": r["name"],
            "full_name": r["full_name"],
            "owner": r["owner"]["login"],
            "description": r.get("description"),
            "stars": r["stargazers_count"],
            "forks": r["forks_count"],
            "open_issues": r["open_issues_count"],
            "language": r.get("language"),
            "default_branch": r["default_branch"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
            "url": r["html_url"],
        },
        indent=2,
    )


@mcp.tool()
def list_issues(owner: str, repo: str, state: str = "open", max_results: int = 5) -> str:
    """List issues in a GitHub repository.

    Args:
        owner: Repository owner (e.g. 'Luqmansyed75').
        repo: Repository name (e.g. 'Major_1').
        state: Filter by state — 'open', 'closed', or 'all' (default: 'open').
        max_results: Maximum issues to return (default: 5).
    """
    res = httpx.get(
        f"{API}/repos/{owner}/{repo}/issues",
        headers=HEADERS,
        params={"state": state, "per_page": max_results},
        timeout=10.0,
    )
    res.raise_for_status()
    issues = [
        {
            "number": i["number"],
            "title": i["title"],
            "state": i["state"],
            "user": i["user"]["login"],
            "created_at": i["created_at"],
            "labels": [l["name"] for l in i.get("labels", [])],
            "comments": i["comments"],
            "is_pull_request": "pull_request" in i,
            "url": i["html_url"],
        }
        for i in res.json()[:max_results]
    ]
    return json.dumps(
        {"repository": f"{owner}/{repo}", "count": len(issues), "issues": issues},
        indent=2,
    )


@mcp.tool()
def get_issue(owner: str, repo: str, issue_number: int) -> str:
    """Get full body and details of a specific issue by number.

    Args:
        owner: Repository owner.
        repo: Repository name.
        issue_number: The issue number.
    """
    res = httpx.get(
        f"{API}/repos/{owner}/{repo}/issues/{issue_number}",
        headers=HEADERS,
        timeout=10.0,
    )
    res.raise_for_status()
    i = res.json()
    return json.dumps(
        {
            "number": i["number"],
            "title": i["title"],
            "state": i["state"],
            "user": i["user"]["login"],
            "created_at": i["created_at"],
            "updated_at": i["updated_at"],
            "body": i.get("body") or "",
            "labels": [l["name"] for l in i.get("labels", [])],
            "comments": i["comments"],
            "url": i["html_url"],
        },
        indent=2,
    )


@mcp.tool()
def list_pull_requests(owner: str, repo: str, state: str = "open", max_results: int = 5) -> str:
    """List pull requests in a GitHub repository.

    Args:
        owner: Repository owner.
        repo: Repository name.
        state: Filter by state — 'open', 'closed', or 'all' (default: 'open').
        max_results: Maximum pull requests to return (default: 5).
    """
    res = httpx.get(
        f"{API}/repos/{owner}/{repo}/pulls",
        headers=HEADERS,
        params={"state": state, "per_page": max_results},
        timeout=10.0,
    )
    res.raise_for_status()
    prs = [
        {
            "number": p["number"],
            "title": p["title"],
            "state": p["state"],
            "user": p["user"]["login"],
            "created_at": p["created_at"],
            "head": p["head"]["ref"],
            "base": p["base"]["ref"],
            "body": (p.get("body") or "")[:300],
            "url": p["html_url"],
        }
        for p in res.json()[:max_results]
    ]
    return json.dumps(
        {"repository": f"{owner}/{repo}", "count": len(prs), "pull_requests": prs},
        indent=2,
    )


@mcp.tool()
def get_file_content(owner: str, repo: str, path: str, ref: str = "main") -> str:
    """Read and decode a file's content from a repository at a given branch.

    Args:
        owner: Repository owner.
        repo: Repository name.
        path: File path inside the repository (e.g. 'README.md').
        ref: Branch, tag, or commit SHA (default: 'main').
    """
    res = httpx.get(
        f"{API}/repos/{owner}/{repo}/contents/{path}",
        headers=HEADERS,
        params={"ref": ref},
        timeout=10.0,
    )
    res.raise_for_status()
    data = res.json()
    if data.get("encoding") != "base64" or "content" not in data:
        return json.dumps({"error": f"'{path}' is not a readable file."})
    content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
    return json.dumps(
        {
            "repository": f"{owner}/{repo}",
            "path": path,
            "ref": ref,
            "size": data.get("size"),
            "content": content,
        },
        indent=2,
    )


@mcp.tool()
def list_commits(owner: str, repo: str, max_results: int = 5) -> str:
    """List recent commits in a repository with author, message, and date.

    Args:
        owner: Repository owner.
        repo: Repository name.
        max_results: Maximum commits to return (default: 5).
    """
    res = httpx.get(
        f"{API}/repos/{owner}/{repo}/commits",
        headers=HEADERS,
        params={"per_page": max_results},
        timeout=10.0,
    )
    res.raise_for_status()
    commits = [
        {
            "sha": c["sha"][:7],
            "author": c["commit"]["author"]["name"],
            "date": c["commit"]["author"]["date"],
            "message": c["commit"]["message"].split("\n")[0],
            "url": c["html_url"],
        }
        for c in res.json()[:max_results]
    ]
    return json.dumps(
        {"repository": f"{owner}/{repo}", "count": len(commits), "commits": commits},
        indent=2,
    )


# ---------------------------------------------------------------------------
# 3. Run MCP Server
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(transport="stdio")
