# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set working directory in the container
WORKDIR /app

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY docker_api.py .

# Expose the port the app runs on
EXPOSE 1337

# Run the application with uvicorn
CMD ["uvicorn", "docker_api:app", "--host", "0.0.0.0", "--port", "1337"] 