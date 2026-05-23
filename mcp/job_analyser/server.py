import asyncio
from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
from jobspy import scrape_jobs
import pandas as pd

"""
Scrapes for relevant jobs to the user's profile and projects.
Analyses jobs using LLMs and evaluates their relevance to the user's profile and projects.
Returns a sorted list of jobs by relevance, 
Adds a summary for each job.
"""
mcp = FastMCP(
    "Job Analyser Server",
    #sampling_handler=OpenAISamplingHandler(default_model="gpt-4o-mini"),
    #sampling_handler_behavior="fallback" #csak abban az esetben ha a kliens nem támogatja a samplingot, vagy "always", ha teljesen ki akarja kerülni a klienst
)

class ScraperQuery(BaseModel):
    search_term: str = Field(description="The job title or position's name to search for.", default=None)
    location: str = Field(description="The location or city to search for.", default=None)
    country: str = Field(description="The country to search for.", default=None)

class JobAnalyzerOutput(BaseModel):
    relevance:int = Field(description="The relevance of the job to the user's profile and projects.")
    summary:str = Field(description="The short bullet point summary of the job, based on the description. The key responsibilities, what will be the applicants exercises.")
    
async def job_analyser_function(context:Context,job:pd.Series, project_summaries:str, user_info:str) -> JobAnalyzerOutput:
    prompt = f"""Analyze the job "{job.title}" at {job.company} and evaluate its relevance to the user's profile and projects. 
    User information: {user_info}
    Project summaries: {project_summaries}
    Return an integer between 0 and 10 where 10 is the most relevant.
    """
    result = await context.sample(
        messages=prompt,
        result_type=JobAnalyzerOutput,
    )
    return result.result.relevance, result.result.summary


@mcp.tool()
async def job_analyser(context: Context, project_summaries:str, user_info:str) -> list:
    
    #get scraper query with sampling
    sampling_result = await context.sample(
        messages=f"Extract the job title, location, country from this text: {user_info}",
        system_prompt="You are a helpful assistant, who can extract the needed information from a text. The most important is, if the asked info is not provided do not make it up, just leave it empty.",
        result_type=ScraperQuery,
    )
    query = sampling_result.result
    if not query.search_term:
        elicit_result = await context.elicit(
            message="Please provide the job title or position's name to search for",
            response_type=str,
        )
        query.search_term = elicit_result.data
    if not query.location:
        elicit_result = await context.elicit(
            message="Please provide the location (e.g. Budapest) of the job, you are looking for",
            response_type=str,
        )
        query.location = elicit_result.data
    if not query.country:
        elicit_result = await context.elicit(
            message="Please provide the country of the job, you are looking for",
            response_type=str,
        )
        query.country = elicit_result.data

    #scrape jobs
    jobs = scrape_jobs(
        site_name=["indeed"],
        search_term=query.search_term,
        location=query.location,
        results_wanted=5,
        hours_old=24*14,
        country_indeed=query.country,
    )

    if not jobs.empty:
        tasks = [job_analyser_function(context, row, project_summaries, user_info) for _, row in jobs.iterrows()]
        results = await asyncio.gather(*tasks)
        jobs['relevance'] = [r[0] for r in results]
        jobs['summary'] = [r[1] for r in results]
    else:
        jobs['relevance'] = []
        jobs['summary'] = []

    jobs = jobs.sort_values('relevance', ascending=False)
    return jobs.to_dict(orient="records")

if __name__ == "__main__":
    mcp.run(
        transport='sse',
        host='0.0.0.0',
        port=8003,
        json_response=True,
    )