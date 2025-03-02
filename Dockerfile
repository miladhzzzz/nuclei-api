FROM ubuntu:latest

# Install dependencies
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common

# Install Docker CLI client, git, Python3, and pip3
RUN apt-get update && apt-get install -y docker.io python3 python3-pip wget unzip

RUN wget https://github.com/projectdiscovery/nuclei/releases/download/v3.3.9/nuclei_3.3.9_linux_amd64.zip \
    && unzip nuclei_3.3.9_linux_amd64.zip \
    && mv nuclei /usr/local/bin/ \
    && chmod +x /usr/local/bin/nuclei \
    && rm -rf nuclei_amd64.zip

WORKDIR /app

# Copy the application files into the working directory
COPY .env ./
COPY requirements.txt ./
COPY app/ ./ 

# Install dependencies
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Start the FastAPI application
CMD ["python3", "main.py"]
