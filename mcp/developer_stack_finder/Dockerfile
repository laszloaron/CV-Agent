FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY mcp/developer_stack_finder/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY mcp/developer_stack_finder/server.py ./server.py

# Configure ENV
ENV YAML_PATH=/app/local_projects.yaml
ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["python", "server.py"]
