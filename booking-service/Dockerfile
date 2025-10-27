# Use official Python image
FROM python:3.11-slim

# --- NEW: Install build tools for aiokafka's GSSAPI ---
RUN apt-get update && apt-get install -y \
    build-essential \
    libkrb5-dev \
    && rm -rf /var/lib/apt/lists/*
# --- END NEW ---

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY ./app /app

# Run the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]