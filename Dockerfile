# Use the official Python lightweight image
FROM python:3.13-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (often required for machine learning libraries)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code and environment variables
COPY src/ ./src/
COPY .env .

# Expose the port FastAPI runs on
EXPOSE 8000

# Command to launch the Uvicorn server
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]