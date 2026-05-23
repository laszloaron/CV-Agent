FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY mcp/job_analyser/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY mcp/job_analyser/server.py ./server.py

# Configure ENV
ENV PYTHONPATH=/app

EXPOSE 8003

CMD ["python", "server.py"]
