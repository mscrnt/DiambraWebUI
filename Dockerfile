# Base image
FROM pytorch/pytorch:2.4.1-cuda12.4-cudnn9-runtime

# Install system dependencies including PostgreSQL server
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    libglib2.0-0 && \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application directory
COPY app/ ./app


# Expose the Flask and Tensorboard ports
EXPOSE 5000 6006

# Set the entry point to the initialization script
CMD ["flask run --host=0.0.0.0 --port=5000 "]
