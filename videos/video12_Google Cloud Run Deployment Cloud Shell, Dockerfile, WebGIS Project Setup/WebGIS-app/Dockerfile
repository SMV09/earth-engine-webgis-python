# Base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Cloud Run port
ENV PORT=8080

# Start with gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
