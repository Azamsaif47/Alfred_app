# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install PostgreSQL dependencies (if you're using psycopg2)
RUN apt-get update && apt-get install -y libpq-dev gcc

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the image
COPY requirements.txt .

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN ls -la /app  # or wherever the files were copied

# Expose FastAPI default port
EXPOSE 8000
