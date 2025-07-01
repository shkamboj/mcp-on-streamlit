from fastmcp import FastMCP
from typing import List, Dict, Any
import logging
import os
from github import Github, UnknownObjectException

from dotenv import load_dotenv
load_dotenv()
github_token = os.getenv("GITHUB_TOKEN")

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
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("ERROR: GITHUB_TOKEN environment variable is not set.")
        return []

    try:
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        
        recent_commits = repo.get_commits()
        
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
        print(f"Error: Repository '{repo_name}' not found or token is invalid.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000)
