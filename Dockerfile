# Dockerfile for YARNNN Agents

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY yarnnn_agents/ ./yarnnn_agents/
COPY integrations/ ./integrations/
COPY examples/ ./examples/

# Copy configuration
COPY pyproject.toml .
COPY README.md .

# Install package in development mode
RUN pip install -e .

# Create state directory
RUN mkdir -p /app/state

# Set Python path
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command (can be overridden in docker-compose)
CMD ["python", "-m", "examples.knowledge_agent.run", "--help"]
