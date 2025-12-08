# Dockerfile optimizado para FastAPI en Fly.io
FROM python:3.11-slim

# Set working director
WORKDIR /code

# Install PostgreSQL development libraries (needed for psycopg2-binary)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy application code
COPY ./app ./app

# Create models directory
RUN mkdir -p /code/models

# Command to run the application using dynamic PORT
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"
