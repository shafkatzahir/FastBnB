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
RUN pip install --no-cache-dir bcrypt==3.2.2

# Copy app source
COPY .. .
# Run the FastAPI app
ENTRYPOINT ["./entrypoint.sh"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]