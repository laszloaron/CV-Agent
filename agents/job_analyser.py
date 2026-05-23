
import pandas as pd
from mcp.types import SamplingCapability, SamplingToolsCapability
from fastmcp.client.sampling.handlers.openai import OpenAISamplingHandler
from fastmcp import Client

async def elicitation_handler(message: str, response_type: type, params, context):

    user_input = input(f"{message}: ")
    response_data = response_type(value=user_input)
    return response_data

async def job_analyser(project_summaries:str, user_info:str):
    job_scareper_mcp_client = Client(
            "http://localhost:8003/sse",
            elicitation_handler=elicitation_handler,
            sampling_handler=OpenAISamplingHandler(default_model="gpt-4o-mini"),
            sampling_capabilities=SamplingCapability(tools=SamplingToolsCapability())
        )
    async with job_scareper_mcp_client:
        toolcall_result = await job_scareper_mcp_client.call_tool(
            "job_analyser",
            {"project_summaries":project_summaries, "user_info":user_info}
        )
    return pd.DataFrame(toolcall_result.structured_content["result"])