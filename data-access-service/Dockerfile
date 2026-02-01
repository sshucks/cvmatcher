# Start from an official Debian base
FROM python:3.12-slim

# Avoid prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Update and install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ca-certificates \
    tmux \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /data-access-service

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]