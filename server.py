from fastmcp import FastMCP
from mcp.server.session import ServerSession
from typing import List, Dict, Any
import logging
import requests
import os
from github import Github, UnknownObjectException
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
github_token = os.getenv("GITHUB_TOKEN")

old__received_request = ServerSession._received_request

async def _received_request(self, *args, **kwargs):
    try:
        return await old__received_request(self, *args, **kwargs)
    except RuntimeError:
        pass


ServerSession._received_request = _received_request

# Create FastMCP app
mcp = FastMCP("Github MCP Server")

@mcp.tool
def get_commit_history(repo_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieves the recent commit history for a given repository.
    Args:
        repo_name: The name of the repository (e.g., "streamlit/streamlit").
        limit: The maximum number of commits to return.
    Returns:
        A list of dictionaries, where each dictionary represents a commit.
    """
    print(repo_name)
    print(limit)
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.error("GITHUB_TOKEN environment variable is not set.")
        return []

    if "/" not in repo_name:
        logger.error("Invalid repo format. Use 'owner/repo' format.")
        return []

    try:
        g = Github(github_token)
        repo = g.get_repo(repo_name)

        recent_commits = repo.get_commits()
        limit = min(limit, 100)

        commits_data = []
        for i, commit in enumerate(recent_commits):
            if i >= limit:
                break

            commit_info = {
                "sha": commit.sha,
                "author": commit.commit.author.name,
                "date": commit.commit.author.date.isoformat(),
                "message": commit.commit.message.split('\n')[0]
            }
            commits_data.append(commit_info)

        return commits_data

    except UnknownObjectException:
        logger.warning(f"Repository '{repo_name}' not found or token invalid.")
        return []
    except Exception as e:
        logger.exception(f"Unexpected error while fetching commits: {e}")
        return []




@mcp.tool
def search_code_in_repo(repo_name: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Searches for a specific code pattern or function name in a GitHub repository.

    Args:
        repo_name: The full name of the repository (e.g., "streamlit/streamlit").
        query: The code pattern or function name to search for.
        limit: The maximum number of search results to return (default: 10, max: 100).

    Returns:
        A list of dictionaries with details of matching code locations.
    """
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.error("GITHUB_TOKEN environment variable is not set.")
        return []

    if "/" not in repo_name:
        logger.error("Invalid repo format. Use 'owner/repo'.")
        return []

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3.text-match+json"
    }

    search_query = f"{query} repo:{repo_name} in:file"
    url = f"https://api.github.com/search/code?q={search_query}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        results = response.json().get("items", [])[:limit]

        matches = []
        for item in results:
            match = {
                "name": item["name"],
                "path": item["path"],
                "repository": item["repository"]["full_name"],
                "html_url": item["html_url"],
            }
            matches.append(match)

        return matches

    except requests.exceptions.RequestException as e:
        logger.exception(f"Error querying GitHub code search API: {e}")
        return []


@mcp.tool
def get_file_content(repo_name: str, file_path: str, ref: str = "master") -> Dict[str, Any]:
    """
    Retrieves the raw content of a specific file from a GitHub repository.

    Args:
        repo_name: Full repository name in 'owner/repo' format.
        file_path: Path to the file within the repository.
        ref: Git reference (branch or commit SHA), default is 'master'.

    Returns:
        A dictionary containing the file content and metadata.
    """
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.error("GITHUB_TOKEN environment variable is not set.")
        return {"error": "Missing GitHub token."}

    if "/" not in repo_name:
        logger.error("Invalid repo format. Use 'owner/repo'.")
        return {"error": "Invalid repository name."}

    try:
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        file_content = repo.get_contents(file_path, ref=ref)

        return {
            "name": file_content.name,
            "path": file_content.path,
            "sha": file_content.sha,
            "size": file_content.size,
            "encoding": file_content.encoding,
            "decoded_content": file_content.decoded_content.decode("utf-8")
        }

    except UnknownObjectException:
        logger.warning(f"File '{file_path}' not found in repo '{repo_name}' at ref '{ref}'.")
        return {"error": "File not found."}
    except Exception as e:
        logger.exception(f"Error fetching file content: {e}")
        return {"error": str(e)}


@mcp.tool
def get_full_repo_tree(repo_name: str, ref: str = "master") -> List[Dict[str, Any]]:
    """
    Retrieves the full recursive directory tree structure of a GitHub repository.

    Args:
        repo_name: Full repository name in 'owner/repo' format.
        ref: Branch or commit SHA (default: 'master').

    Returns:
        A list of dictionaries representing all files and directories in the repository.
    """
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.error("GITHUB_TOKEN environment variable is not set.")
        return []

    if "/" not in repo_name:
        logger.error("Invalid repo format. Use 'owner/repo'.")
        return []

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        # Get the SHA of the specified branch or commit
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        commit = repo.get_commit(ref)
        tree_sha = commit.commit.tree.sha

        # GitHub API: /repos/:owner/:repo/git/trees/:sha?recursive=1
        url = f"https://api.github.com/repos/{repo_name}/git/trees/{tree_sha}?recursive=1"
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        tree = response.json().get("tree", [])
        structure = []
        for item in tree:
            structure.append({
                "path": item["path"],
                "type": item["type"],  # 'blob' (file) or 'tree' (directory)
                "sha": item["sha"],
                "mode": item["mode"],
                "size": item.get("size", None),
                "url": f"https://github.com/{repo_name}/blob/{ref}/{item['path']}" if item["type"] == "blob"
                       else f"https://github.com/{repo_name}/tree/{ref}/{item['path']}"
            })

        return structure

    except UnknownObjectException:
        logger.warning(f"Repository or reference not found: {repo_name}@{ref}")
        return []
    except Exception as e:
        logger.exception(f"Error retrieving full repo tree: {e}")
        return []






# Optional health check
@mcp.tool
def health_check() -> Dict[str, str]:
    return {"status": "ok"}

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000)
