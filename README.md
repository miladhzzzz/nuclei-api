# Nuclei API Documentation

## Overview

The Nuclei API is a stateless API built to run powerful and customizable vulnerability scans using the Nuclei engine. The API integrates Dockerized Nuclei, ensuring it is lightweight, scalable, and highly portable. It is designed to support various scan types, handle rate-limiting, and validate input targets to ensure efficient and secure operations.

## Features

1. Stateless Architecture

    * Each request is independent and contains all the necessary data for processing.

    * No persistent state is maintained between requests, ensuring scalability and simplicity.

2. Dockerized Scanning

    * Utilizes the official Nuclei Docker image for running scans.

    * Ensures portability and consistency across environments.

3. Template Support

    * Compatible with all official Nuclei templates.

    * Supports mounting custom templates via Docker volume.

4. Target Validation

    * Validates input targets to ensure only proper domains or IPs (with or without HTTP/HTTPS) are scanned.

    * Prevents resource wastage on invalid inputs.

5. Rate Limiting

    * Built-in rate limiting via the FastAPI "slowapi" library.

    * Protects the API from abuse and ensures fair usage.

6. Logging and Debugging

    * Real-time logging of scan results and errors.

    * Easy integration with monitoring systems for operational transparency.

7. Customizable Scan Types

    * Supports all scan types offered by Nuclei, including:

        * CVE scans

        * Misconfiguration scans

        * Information disclosure scans

        * Network scans

8. High Performance

    * Parallel execution of scans using Docker containers.

    * Automatic updates of Nuclei templates on demand.

9. Secure by Design

    * Implements strict input validation to avoid invalid or malicious requests.

    * Runs scans in isolated Docker containers for additional security.

10. Comprehensive API Endpoints

    * GET /: Health check endpoint to verify API availability.

    * POST /nuclei/scan: Run a vulnerability scan with customizable options.

    * GET /nuclei/scan/{container_name}/logs: Fetch scan results.

## API Endpoints

1. Health Check

    *Endpoint*: `GET /`

    *Description*:
        Returns a simple response to confirm the API is up and running.

    *Response*:

    ```json
    {
        "ping": "pong!"
    }
    ```

2. Run a Scan

    *Endpoint*: POST /nuclei/scan

    *Description*:
    Runs a Nuclei vulnerability scan on the specified target.

    *Request Body*:

    ```json
    {
        "target": "<https://example.com>",
        "template": "cves" // Optional
    }
    ```

    *Parameters*:

    * `target`: (Required) The target domain or IP to scan. Accepts domains with or without HTTP/HTTPS.

    * `template`: (Optional) Specifies the type of scan to run. Defaults to all if not provided.

    *Response*:

    ```json
    {
        "status": "success",
        "results": [
            "container_name": "nuclei_scan_929753",
            "message": "Scan started successfully"
        ]
    }
    ```

3. See Scan Results
    *Endpoint*: `GET /nuclei/scan/{container_name}/logs`

    *Description*:
    API endpoint to stream container logs as a JSON stream.

    *Response*:

    ```json
    {
        {'source': 'stderr', 'log': ''},
        {'source': 'stderr', 'log': '__     _'},
        {'source': 'stderr', 'log': '____  __  _______/ /__  (_)'},
        {'source': 'stderr', 'log': '/ __ \\/ / / / ___/ / _ \\/ /'},
        {'source': 'stderr', 'log': '/ / / / /_/ / /__/ /  __/ /'},
        {'source': 'stderr', 'log': '/_/ /_/\\__,_/\\___/_/\\___/_/   v3.3.8'},
        {'source': 'stderr', 'log': ''},
        {'source': 'stderr', 'log': 'projectdiscovery.io'},
    }
    ```

## Installation and Setup

### Prerequisites

* Docker + Docker Compose installed on the host machine.

* FastAPI environment for running the API Locally.

### Run In Docker

1. Clone the Repository:

    ```shell
        git clone <repository-url>
        cd nuclei-api
    ```

2. Use Docker Compose to bring the project up and build the image:

    ```shell
        docker compose up -d
    ```

### Running the API

1. Clone the Repository:

    ```shell
    git clone <repository-url>
    cd nuclei-api
    ```

2. Install Dependencies:

    ```shell
    pip install -r requirements.txt
    ```

3. Run the API:

    ```shell
    python3 app/main.py
    ```

4. Verify API:
    Access http://<host>:8080/ to ensure the API is running.

## Usage Examples

### Running a Basic Scan

```shell
    curl -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "target": "<https://example.com>",
        "template": "cves" // Optional
    }' \
    http://<host>:8080/nuclei/scan
```

### Future Enhancements

1. Authentication

    * Add API key-based authentication for enhanced security.

2. Scan Scheduling

    * Allow users to schedule scans for specific times.

3. Multi-Target Scanning

    * Support scanning multiple targets in a single request.

For more details or support, please contact our development team.
