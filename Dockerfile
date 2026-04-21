FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if any are needed (e.g. for pypdf or image processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start the FastAPI server
CMD ["python", "run.py"]
