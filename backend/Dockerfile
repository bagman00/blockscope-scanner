# Use slim Python image (smaller, faster)
FROM python:3.11-slim

# Install system dependencies (git + curl)
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install semgrep loguru

# Copy all code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Make sure the app waits for DB before starting (optional)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000"]
