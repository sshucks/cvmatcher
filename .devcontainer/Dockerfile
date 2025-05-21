# Start from an official Debian base
FROM python:3.12-slim

# Avoid prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Update and install dependencies
RUN apt-get update && apt-get install -y \
    php-cli \
    php-curl \
    curl \
    git \
    ca-certificates \
    tmux \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a working directory
WORKDIR /workspace

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt


CMD ["/workspace/start-services.sh"]