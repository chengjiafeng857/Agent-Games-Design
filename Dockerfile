FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/tmp/uv-cache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Create app directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY README.md QUICKSTART.md ./

# Install Python dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ ./src/
COPY examples/ ./examples/
COPY tests/ ./tests/

# Install the package
RUN uv pip install -e .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port for potential web interface
EXPOSE 8000

# Default command
CMD ["uv", "run", "agent-games", "--help"]
