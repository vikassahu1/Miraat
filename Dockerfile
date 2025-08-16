# Start with a Python version that is compatible with your dependencies (TensorFlow, etc.)
# Python 3.9 is a safe and common choice for these libraries.
FROM python:3.12-slim

# Set environment variables for better logging and path management
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set the working directory inside the container
WORKDIR /app


# Install essential system dependencies.
# build-essential contains common compilers (like gcc) needed by some Python packages.
# libpq-dev contains the development files for PostgreSQL, which is good practice
# even when using the binary version of psycopg2.
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*



# Copy the requirements file and install dependencies first
# This uses Docker's layer caching to speed up future builds
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Expose the port your application runs on
EXPOSE 8000

# The command to run your FastAPI application using Uvicorn
# The --host 0.0.0.0 is crucial for Docker networking
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]