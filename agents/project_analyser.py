from pydantic import BaseModel, Field
from pydantic_ai import Agent, UsageLimits
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.mcp import MCPServerStreamableHTTP
from pydantic_ai.models.openai import OpenAIChatModel
from fastmcp import Client
from utils.monitoring import instrumentation

import os
import json
import asyncio


mcp_url="http://localhost:8001/mcp"

async def get_project_names():
    mcp_client = Client(mcp_url)
    async with mcp_client:
        content = await mcp_client.read_resource("resource://projects")
        return json.loads(content[0].text)['projects']


async def get_project_summaries():
    project_summaries = []

    #provider = GoogleProvider(api_key=os.getenv("GEMINI_API_KEY"))
    #model = GoogleModel("gemini-2.5-flash-lite", provider=provider)

    model = OpenAIChatModel('gpt-4o-mini')
    
    # We have to connect to the MCP server first using
    toolset = MCPServerStreamableHTTP(mcp_url)

    #Define the agent
    agent = Agent(model, toolsets=[toolset], instrument=instrumentation)
    prompt = "Analyze the the project, and give a summary about the developers skill-set, and stack, and knowledge."

    projects = await get_project_names()
    for i, p in enumerate(projects):
        result = await agent.run(
            f"{prompt} Project name: {p}",
            #usage_limits=UsageLimits(response_tokens_limit=100)
        )
        project_summaries.append(f"{i+1}. Project: {p}\n{result.output}\n")
    return "\n".join(project_summaries)
