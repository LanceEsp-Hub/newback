# FROM python:3.11-slim

# WORKDIR /app

# # Install system dependencies
# RUN apt-get update && apt-get install -y \
#     gcc \
#     g++ \
#     libpq-dev \
#     && rm -rf /var/lib/apt/lists/*

# # Copy requirements and install Python dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy application code
# COPY . .

# # Create upload directories
# RUN mkdir -p app/uploads/pet_images app/uploads/messages app/uploads/success_stories

# # Expose port
# EXPOSE 8000

# # Run the application
# CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]



# Use a lightweight Python image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for psycopg2 and other libraries
# libpq-dev for PostgreSQL client library
# gcc, g++ for compiling Python packages with C extensions
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of your application code
COPY . /app

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PORT 8000

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
# Use gunicorn with uvicorn workers for production
# --host 0.0.0.0 makes the server accessible from outside the container
# --port $PORT uses the environment variable for the port
# app.main:app refers to the FastAPI app instance in app/main.py
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
