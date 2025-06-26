# Dockerfile for the transcritor-pdf service

# --- Builder Stage ---
# This stage installs build dependencies and Python packages
FROM python:3.11-slim as builder

WORKDIR /opt/build

# Install build-time system dependencies
# build-essential and libpq-dev might be needed if some packages compile from source.
# If all packages have wheels, these might not be strictly necessary.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv

# Activate virtual environment and install Python dependencies
# Using venv path directly for pip install
COPY requirements.txt .
RUN /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


# --- Final Stage ---
# This stage copies the installed packages and application code to a clean image
FROM python:3.11-slim

WORKDIR /app

# Install runtime system dependencies
# libpq5 for PostgreSQL client libraries (if not using psycopg2-binary which bundles them)
# curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application code
# Only copy necessary source code, exclude tests, .git, etc. if not needed in image
COPY src ./src
COPY celery_app.py . # If celery_app.py is at root of transcritor-pdf, adjust if it's in src
# If main.py or celery_app.py are inside src, the CMD needs to reflect that, e.g. src.main:app

# Make the virtual environment's Python the default
ENV PATH="/opt/venv/bin:$PATH"

# Expose the port the application will run on (same as before)
EXPOSE 8002

# Command to run the application with Uvicorn
# Note: --reload is typically for development. For production, remove --reload.
# The command in docker-compose.yml overrides this, so this is a fallback/default.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
