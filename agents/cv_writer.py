from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.mcp import MCPServerSSE,  MCPServerStreamableHTTP
import pandas as pd
from mcp.client.session import ClientSession
from mcp.shared.context import RequestContext
from mcp.types import ElicitRequestParams, ElicitResult
from typing import Any
from fastmcp import Client
from utils.monitoring import instrumentation


"""
Writes a tailored CV for a specific job
 
"""
SERVER_URL="http://localhost:8002/sse"

async def handle_elicitation(
    context: RequestContext[ClientSession, Any, Any],
    params: ElicitRequestParams,
) -> ElicitResult:
    """Handle elicitation requests from MCP server."""
    tool_name = params.requestedSchema["title"]
    handler = HANDLERS[tool_name]
    if handler:
        return await handler(params)
    else:
      return ElicitResult(action="cancel")  

async def handle_user_data_requests(params: ElicitRequestParams) -> ElicitResult:
    """Handle elicitation requests from MCP server."""
    print(f'\n{params.message}')
    # Collect data for each field
    properties = params.requestedSchema['properties']
    data = {}
    import asyncio
    loop = asyncio.get_event_loop()
    for field, info in properties.items():
        description = info.get('description', field)
        data[field] = await loop.run_in_executor(None, input, f'{description}: ')
        if data[field] == "":
            data[field] = info.get('default', 'Not provided')
    
    #print('Personal data:', data)
    return ElicitResult(action='accept', content=data)

HANDLERS = {
    "UserData": handle_user_data_requests,
}


cv_server = MCPServerSSE(SERVER_URL, elicitation_callback=handle_elicitation)

async def write_cv(job:pd.Series, user_info:str, project_summaries:str):
    """
    Write a CV for a specific job.
    """
    model = OpenAIChatModel('gpt-4o-mini')
    mcp_client = Client(SERVER_URL)
    async with mcp_client:
        cv_structure = await mcp_client.get_prompt("cv_structure_prompt")
        generator_prompt = await mcp_client.get_prompt("cv_generator_prompt", {"job": job.to_dict(), "user_info": user_info, "project_summaries": project_summaries})

    system_prompt = "Egy cv készítő asszisztens vagy. A feadatotd, hogy készíts egy professzionális, strukturált önéletrajzot (CV) a megadott felhasználói adatok alapján. Kövesd pontosan az alábbi struktúrát és mintát. Az egyes részek megfogalmazásához használd a megfelelő eszközöket. Ne fogalmazz meg magadtól bekezdésekete vagy szekciókat.\n"
    agent= Agent(model, instructions=system_prompt+cv_structure.messages[0].content.text, toolsets=[cv_server], instrument=instrumentation)
    agent.set_mcp_sampling_model()
    result = await agent.run(generator_prompt.messages[0].content.text)
    return result.output


class CV_CheckerResult(BaseModel):
    general_impression:str = Field(description="Rövid értékelés a CV erejéről és hangneméről")
    critical_issues:str = Field(description="Hibák, hiányosságok vagy gyenge megfogalmazások a kritériumok alapján")
    corrections:str = Field(description="Mit mivé lehetne átírni")


async def check_cv(cv_text: str):
    #Itt kell egy ellenőrző ágens aki javítja a CV-t, ha szükséges.
    model = OpenAIChatModel('gpt-4o-mini')
    agent = Agent(model, instructions="Te vagy Ágnes, egy precíz, kritikus és tapasztalt HR-szakértő és CV-auditor.", output_type=CV_CheckerResult, instrument=instrumentation)
    mcp_client = Client(SERVER_URL)
    async with mcp_client:
        cv_structure = await mcp_client.get_prompt("cv_structure_prompt")
    prompt = f"Értékeld ki a megadott önéletrajzot (CV) a megadott szigorú minőségi kritériumok alapján. Mutass rá a hibákra, hiányosságokra, logikai ellentmondásokra, és tegyél javaslatot a javításra.\n\nKiértékelendő önéletrajz (CV) szövege:\n{cv_text}\n\nSzigorú minőségi kritériumok és struktúra:\n"

    result= await agent.run(prompt+cv_structure.messages[0].content.text)
    return result.output
    





