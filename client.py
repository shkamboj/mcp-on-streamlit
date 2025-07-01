import asyncio
import os
import json
from dotenv import load_dotenv
from mcp_use import MCPAgent, MCPClient
from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv
load_dotenv()

SYSTEM_INSTRUCTION = """You are an intelligent AI agent specializing in GitHub repositories. 
Your purpose is to answer user questions by intelligently using a suite of Model Context Protocol (MCP) servers. 
You will select and chain the appropriate MCP tools (e.g., File Content, Repository Structure, Commit History, Issue/PR, Code Search, Documentation,
Code Analysis, Dependency Analysis, Change Detection, Playwright navigation, web search etc.) to gather information and synthesize clear, 
concise answers, always indicating which tools were used."""


with open('servers.json', 'r') as handle:
    config = json.load(handle)
    client = MCPClient.from_dict(config)

def create_agent():
    llm = ChatGoogleGenerativeAI(
        model='gemini-2.5-pro',
        temperature=0.3,
        google_api_key=os.getenv('GEMINI_API_KEY')
    )
    agent = MCPAgent(llm=llm, client=client, memory_enabled=True, max_steps=10)
    return agent


def execute_task(agent, task: str):
    return asyncio.run(agent.run(f"Role & Responsibility: {SYSTEM_INSTRUCTION} \n\n Task: {task}"))
    # result = await agent.run(f"Role & Responsibility: {SYSTEM_INSTRUCTION} \n\n Task: {task}")
    # return result


# Usage example
if __name__ == "__main__":
    task = "Can you please fetch commits of fastapi github repo."
    result = asyncio.run(execute_task(task=task))
    print(result)