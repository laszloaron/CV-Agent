FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY mcp/cv_writer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY mcp/cv_writer/cv_mcp.py ./server.py

# Configure ENV
ENV PYTHONPATH=/app

EXPOSE 8002

CMD ["python", "server.py"]
