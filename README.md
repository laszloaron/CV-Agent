# AI Job Agent

A multi-agent AI system built with [Pydantic AI](https://ai.pydantic.dev/) and the [Model Context Protocol (MCP)](https://modelcontextprotocol.io). This tool automates the tedious parts of job hunting by analyzing job postings, extracting your technological stack from local projects, and automatically generating highly tailored CVs for specific jobs.

## Features

- **Job Analyser**: Scrapes job postings and analyzes them to extract key requirements.
- **Developer Stack Finder**: Scans your local project directories to understand the technologies you have experience with and generates project summaries.
- **CV Writer**: Automatically drafts a targeted CV based on the job requirements, your personal information, and your project history. It uses a **Human-in-the-Loop** approach with the MCP Elicit protocol to interactively ask for any missing personal data.
- **Self-Correcting CV Review**: Reviews and critiques the generated CV, pointing out missing information or logical inconsistencies based on strict HR criteria.
- **Native Web UI**: A completely integrated Streamlit web interface that allows you to configure your profile, manage project paths, and interact with the agent in a virtual terminal environment.

## Architecture

The system uses a **chain topology** of agents and servers:
1. The **Job Analyser Server** finds relevant jobs.
2. The **Developer Stack Finder Server** reads local repositories.
3. The **CV Writer Server** provides structure, prompts the user for missing data (using Elicit), and generates the final document.

All MCP servers run independently in Docker containers, simulating a distributed microservice architecture.

## Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose (to run the MCP servers and monitoring).
- [uv](https://github.com/astral-sh/uv) package manager.
- Python (configured via `.python-version`).
- OpenAI API Key (configured in `.env`).

## Setup

1. **Environment Variables**
   Copy the example environment file and add your API keys:
   ```bash
   cp .env.example .env
   ```
   *Make sure to fill in your `OPENAI_API_KEY` in the `.env` file.*

2. **Start the MCP Servers**
   Start all the backend services (MCP servers and the Phoenix tracing platform) in the background using Docker Compose:
   ```bash
   docker compose up -d --build
   ```

## Usage (Streamlit Web UI)

The recommended way to run the application is through the integrated web UI:

```bash
uv run streamlit run streamlit_app.py
```

### 1. Configuration Page
Use the UI to comfortably set up:
- **User Profile:** Describe your general background, education, and career goals (saved to `user_input.txt`).
- **Local Projects:** Add absolute paths to your local coding projects. The system will scan these to extract your tech stack (saved to `mcp/developer_stack_finder/local_projects.yaml`).

### 2. Run Page
Click **"Agent Indítása"** (Start Agent) to begin the process.
- The system will start analyzing jobs and printing output to the virtual terminal.
- **Human-in-the-Loop:** Whenever the agent needs a decision (e.g., "Do you want to apply for this job?") or personal data (via Elicit requests like "Email: "), the process will pause and an input box will appear below the terminal.
- Type your answer and click submit to continue the workflow.

## Legacy Console Usage

If you prefer the command line, you can still run the agent natively in the terminal:
```bash
uv run main.py
```

## Monitoring & Observability

This project includes **Arize Phoenix** for comprehensive trace monitoring. While the Docker containers are running, you can view the agent traces, tool calls, and LLM token usage at [http://localhost:6006](http://localhost:6006).
