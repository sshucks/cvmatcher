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


WORKDIR /frontend

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 8501
COPY . .
# CMD ["streamlit", "run", "matching_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
CMD ["streamlit", "run", "matching_app.py", "--logger.level=debug", "--server.runOnSave=true"]