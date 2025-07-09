import asyncio
import os
import json
from dotenv import load_dotenv
from mcp_use import MCPAgent, MCPClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

load_dotenv()

SYSTEM_INSTRUCTION = """You are an **conversational**, intelligent AI agent specializing in GitHub repositories. 
Your purpose is to answer user questions by intelligently using a suite of Model Context Protocol (MCP) servers. 
You will select and chain the appropriate MCP tools (e.g., File Content, Repository Structure, Commit History, Issue/PR, Code Search, Documentation,
Code Analysis, Dependency Analysis, Change Detection, Playwright navigation, web search etc.) to gather information and synthesize clear, 
concise answers, always indicating which tools were used. 

**You should prefer using tools every time to provide an answer, avoid making an answer on your own.**"""


with open('servers.json', 'r') as handle:
    config = json.load(handle)
    client = MCPClient.from_dict(config)


def create_agent():
    llm = ChatGoogleGenerativeAI(
        model='gemini-2.5-pro',
        temperature=0.3,
        google_api_key=os.getenv('GEMINI_API_KEY')
    )
    agent = MCPAgent(
        llm=llm,
        client=client,
        memory_enabled=True,
        max_steps=10,
        system_prompt=SYSTEM_INSTRUCTION,
        verbose=True
    )
    return agent



def execute_task(task, history):
    agent = create_agent()
    messages = list()
    for item in history:
        messages.append(
            HumanMessage(item.get('user'))
        )
        messages.append(
            AIMessage(item.get('agent'))
        )
    return  asyncio.run(agent.run(task, external_history=messages))
