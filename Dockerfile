FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (minimal set for Railway)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create upload directories
RUN mkdir -p app/uploads/pet_images app/uploads/messages app/uploads/success_stories app/uploads/profile_pictures

# Expose port (Railway will set PORT env var)
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:$PORT/')"

# Run the application
CMD ["python", "-m", "app.main"]
