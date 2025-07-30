# Nuclei API: Automated Vulnerability Template Generation & Scanning Platform

## Overview

**Nuclei API** is an advanced, AI-augmented platform for automated vulnerability scanning and template management, built around [Nuclei](https://nuclei.projectdiscovery.io/). It provides a REST API for running scans, managing templates, and orchestrating a pipeline that fetches new vulnerabilities, generates detection templates using an LLM, validates them, and refines them as needed. The system leverages FastAPI, Celery, Redis, Docker, and Ollama (LLM) to deliver scalable, intelligent, and automated security scanning.

---

## Key Features

- **Automated CVE Template Generation:**  
  Fetches recent vulnerabilities (CVEs) from public sources and uses an LLM to generate Nuclei YAML templates for each.
- **Template Validation & Refinement:**  
  Validates generated templates by running them against known vulnerable hosts. If validation fails, templates are refined using the LLM and retried.
- **Flexible Scanning API:**  
  Exposes endpoints to run Nuclei scans on targets (IP/domain), with support for custom templates, AI-generated templates, and standard templates.
- **Custom Template Scanning:**  
  Upload and scan with your own Nuclei YAML templates via base64-encoded content or file uploads.
- **AI-Powered Scanning:**  
  Generate and run custom templates using natural language prompts describing the vulnerability you want to detect.
- **MCP (Model Context Protocol) Integration:**  
  Full LLM/agent integration with discoverable tools and standardized tool-calling interface for AI-powered security workflows.
- **Asynchronous Pipeline:**  
  Uses Celery for distributed, asynchronous task orchestration (fetching, generating, validating, refining).
- **Metrics & Caching:**  
  Uses Redis for caching vulnerability data and tracking pipeline metrics.
- **Containerized Scanning:**  
  Runs Nuclei scans in Docker containers for isolation and resource control.
- **Real-Time Log Streaming:**  
  Stream scan logs directly from running Docker containers.
- **Modern Web UI:**  
  Next.js frontend with TypeScript, Tailwind CSS, and Radix UI components for a professional user experience.
- **Extensible & Modular:**  
  Modular controllers for Docker, Nuclei, Fingerprinting, and Templates with service-oriented architecture.
- **Production-Ready Docker Setup:**  
  Multi-stage builds, optimized images, and comprehensive Docker Compose configuration for easy deployment.

---

## Architecture

```mermaid
flowchart TD
    subgraph User
        A1[API Client / UI / LLM Agent]
    end
    subgraph API
        B1[FastAPI App]
        B2[NucleiRoutes]
        B3[PipelineRoutes]
        B4[MCP Routes]
    end
    subgraph ServiceLayer
        S1[ScanService]
        S2[TemplateService]
    end
    subgraph Celery
        C1[fetch_vulnerabilities]
        C2[process_vulnerabilities]
        C3[generate_nuclei_template]
        C4[store_templates]
        C5[validate_template]
        C6[refine_nuclei_template]
        C7[run_scan]
        C8[run_ai_scan]
    end
    subgraph Infra
        D1[Ollama LLM]
        D2[Redis]
        D3[Docker Engine]
        D4[Nuclei Scanner]
        D5[FileSystem]
    end

    A1--REST/MCP-->B1
    B1--routes-->B2
    B1--routes-->B3
    B1--routes-->B4
    B2--calls-->S1
    B2--calls-->S2
    B3--calls-->S1
    B3--calls-->S2
    B4--calls-->S1
    B4--calls-->S2
    S1--orchestrates-->Celery
    S2--orchestrates-->Celery
    C1--uses-->D2
    C2--uses-->D1
    C3--uses-->D1
    C4--stores-->D5
    C5--runs-->D4
    C5--in-->D3
    C5--metrics-->D2
    C6--uses-->D1
    C7--runs-->D4
    C8--runs-->D4
    D4--runs in-->D3
```

### Description

- **User/Agent**: Interacts via REST or MCP endpoints (for LLM/agent integration).
- **API Layer**: Modular FastAPI routers:
  - `NucleiRoutes` (scanning, template management)
  - `PipelineRoutes` (pipeline/metrics)
  - `MCP Routes` (LLM/agent tool manifest and tool-calls)
- **Service Layer**: `ScanService`, `TemplateService` encapsulate business logic, orchestrate Celery pipelines, and interact with controllers.
- **Celery Tasks**: Handle async, distributed work (fetch, generate, validate, scan, refine).
- **Controllers**: Stateless adapters for Docker, Nuclei, etc. (not shown in diagram for brevity).
- **Models**: Pydantic models for all API and internal data.
- **Infrastructure**: Redis (cache/metrics), Docker (isolation), Ollama LLM (template generation/refinement), Nuclei (scanning), FileSystem (template storage).

### API Structure

- `app/api/NucleiRoutes.py` — main scan/template endpoints
- `app/api/PipelineRoutes.py` — pipeline/metrics endpoints
- `app/api/mcp_routes.py` — MCP endpoints for LLM/agent integration
- `app/services/` — business logic
- `app/models/` — Pydantic models
- `app/celery_tasks/` — Celery task definitions
- `app/controllers/` — external system adapters

---

## Pipeline Flow

```mermaid
flowchart TD
    A[fetch_vulnerabilities] --> B[process_vulnerabilities]
    B --> C[generate_nuclei_templates_group]
    C --> D[store_templates]
    D --> E[validate_templates_callback_group]
    E --> F[validate_template_per_template]
    F --fail--> G[refine_nuclei_template]
    G --> H[store_refined_template]
    H --> F
    F --success--> I[Done]
```

---

## Setup Instructions

### Prerequisites

- **Python 3.8+**
- **Docker & Docker Compose**
- **Redis**
- **Ollama (or compatible LLM API)**
- **Node.js 18+ & pnpm** (for frontend development)

### Clone the Repository

```sh
git clone <repository-url>
cd nuclei-api
```

## Docker Deployment

### Production Deployment

```sh
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale services if needed
docker-compose up -d --scale celery_worker=3
```

### Services Included

The Docker Compose setup includes the following services:

- **nuclei-api** (Port 8000): Main FastAPI application
- **redis** (Port 6379): Cache and message broker for Celery
- **celery_worker**: Background task processing for scans and template generation
- **celery_beat**: Task scheduler for automated template generation
- **flower** (Port 5555): Celery monitoring and task management UI
- **ollama** (Port 11434): LLM service for template generation and refinement
- **open-webui** (Port 3331): Web interface for Ollama model management
- **nuclei-fingerprint** (Port 3330): OS fingerprinting service
- **loki** (Port 3100): Log aggregation and monitoring

### Development with Hot Reload

```sh
# Start with volume mounts for development
docker-compose -f docker-compose.dev.yml up -d
```

### Staging Environment

```sh
# Use staging configuration
docker-compose -f docker-compose.staging.yaml up -d
```

### Service Management

```sh
# View service status
docker-compose ps

# View logs for specific service
docker-compose logs -f nuclei-api

# Restart a specific service
docker-compose restart celery_worker

# Scale workers for high load
docker-compose up -d --scale celery_worker=5
```

### Option 2: Development Setup

#### Install Python Dependencies

```sh
pip install -r requirements.txt
```

#### Clone Nuclei Templates

```sh
git clone https://github.com/projectdiscovery/nuclei-templates.git
```

#### Start Redis and Ollama

```sh
docker-compose up -d redis ollama
```

#### Run the API

```sh
# From project root (recommended)
python3 -m app.main

# Or with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

#### Run the Frontend (Optional)

```sh
cd frontend
pnpm install
pnpm dev
```

The API will be available at `http://localhost:8080` and frontend at `http://localhost:3000`.

---

## Usage Examples

### 1. **Trigger the Automated Template Generation Pipeline**

```sh
curl -X GET http://localhost:8080/nuclei/template/generate
```
This will fetch new CVEs, generate templates using the LLM, store, and validate them.

### 2. **Run a Scan (API)**

#### Basic Scan

```sh
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{ "target": "https://example.com", "templates": ["cves/"] }' \
  http://localhost:8080/nuclei/scan
```

#### Custom Template Scan

```sh
curl -X POST \
  -F "target=https://example.com" \
  -F "template_file=@/path/to/custom-template.yaml" \
  http://localhost:8080/nuclei/scan/custom
```

#### Fetch Scan Logs

```sh
curl http://localhost:8080/nuclei/scan/nuclei_scan_123456/logs
```

---

## API Endpoints

### Health Check

- **GET /**  
  Returns `{ "ping": "pong!" }`

### Run a Scan

- **POST /nuclei/scan**  
  Request:
  ```json
  {
    "target": "https://example.com",
    "templates": ["cves/"] // Optional
  }
  ```
  Response:  
  Returns scan result or task ID for async scans.

### Run a Custom Scan

- **POST /nuclei/scan/custom**  
  Form Data:
    - `target`: The target domain or IP to scan.
    - `template_file`: Custom template YAML file (optional).
    - `templates`: Comma-separated list of templates (optional).

### Get Scan Logs

- **GET /nuclei/scan/{container_id}/logs**  
  Streams logs from the running scan container.

### Upload a Custom Template

- **POST /nuclei/template/upload**  
  Upload and validate a custom Nuclei template.

### Scan with Custom Template

- **POST /nuclei/scan/custom-template**  
  Run a scan with a custom template file provided by the user.
  
  Request:
  ```json
  {
    "target": "https://example.com",
    "template_file": "base64_encoded_yaml_content",
    "template_filename": "custom-template.yaml"
  }
  ```
  
  Example with curl:
  ```sh
  # First, encode your YAML template
  TEMPLATE_B64=$(base64 -w 0 /path/to/your/template.yaml)
  
  curl -X POST \
    -H "Content-Type: application/json" \
    -d "{
      \"target\": \"https://example.com\",
      \"template_file\": \"$TEMPLATE_B64\",
      \"template_filename\": \"my-custom-template.yaml\"
    }" \
    http://localhost:8080/nuclei/scan/custom-template
  ```

### Trigger Template Generation Pipeline

- **GET /nuclei/template/generate**  
  Starts the full CVE-to-template pipeline.

### Prometheus Metrics

- **GET /metrics**  
  Prometheus-compatible metrics endpoint for monitoring and alerting.
  
  Returns metrics including:
  - HTTP request counts, durations, and sizes
  - Celery task execution metrics
  - Nuclei scan performance and results
  - Template generation and validation statistics
  - System resource usage (CPU, memory, disk)
  - Redis operations and memory usage
  - Custom business metrics (active scans, templates available)

- **GET /health**  
  Health check endpoint with basic metrics and service status.
  
  Returns:
  ```json
  {
    "status": "healthy",
    "timestamp": 1234567890.123,
    "services": {
      "redis": "healthy",
      "system": "healthy", 
      "api": "healthy"
    },
    "metrics": {
      "active_scans": 5,
      "cpu_usage": 45.2,
      "memory_usage": 1073741824,
      "redis_memory": 52428800
    }
  }
  ```

### Prometheus Configuration

Add this to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'nuclei-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

---

## MCP (Model Context Protocol) Endpoints

The API exposes endpoints for LLM/agent integration via the Model Context Protocol (MCP):

- **GET /v1/tools**  
  Returns a manifest of all available tools (API actions) and their argument schemas, for agent/LLM discovery.

- **POST /v1/tool-calls**  
  Allows an agent or LLM to invoke any supported tool by name, passing arguments as a JSON object. Returns the result or error.

**Example:**
```sh
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{ "tool_name": "nuclei_scan", "arguments": { "target": "https://example.com" } }' \
  http://localhost:8080/v1/tool-calls
```

The MCP endpoints are implemented in `app/api/mcp_routes.py` and registered in `main.py`.

---

### Monitoring and Debugging

- **Flower Dashboard**: `http://localhost:5555` - Monitor Celery tasks and workers
- **Open WebUI**: `http://localhost:3331` - Manage Ollama models and chat
- **Loki Logs**: `http://localhost:3100` - Centralized logging
- **API Documentation**: `http://localhost:8000/docs` - Interactive API docs
- **Grafana Dashboard**: `http://localhost:3000` - Comprehensive monitoring dashboard (admin/admin)
- **Prometheus**: `http://localhost:9090` - Metrics collection and querying

### Grafana Dashboard Features

The Nuclei API dashboard provides comprehensive monitoring with the following panels:

#### **API Performance**
- HTTP request rate and duration
- Response sizes and error rates
- API endpoint usage patterns

#### **Celery Task Monitoring**
- Task execution rates and durations
- Queue sizes and worker status
- Task success/failure rates

#### **Nuclei Scan Metrics**
- Scan execution rates and durations
- Vulnerability discovery tracking
- Template usage statistics

#### **Template Pipeline**
- Template generation and validation rates
- Pipeline execution statistics
- Success/failure rates by CVE

#### **System Resources**
- CPU, memory, and disk usage
- Redis memory and connection metrics
- Docker container statistics

#### **Business Metrics**
- Active scans count
- Available templates by type
- Error rates and system health

### Dashboard Setup

1. **Access Grafana**: Navigate to `http://localhost:3000`
2. **Login**: Use `admin/admin` (change in production)
3. **Dashboard**: The Nuclei API dashboard loads automatically
4. **Customize**: Modify panels, add alerts, or create new dashboards

### Alerting Setup

Configure alerts in Grafana for:
- High error rates (>5% for 5 minutes)
- Low Celery worker count (<1 for 5 minutes)
- High system resource usage (>80% CPU/memory)
- Scan failures (>10% failure rate)

---

## API Structure & Organization

- **app/api/NucleiRoutes.py**: Main Nuclei scan/template API endpoints
- **app/api/PipelineRoutes.py**: Pipeline and metrics endpoints
- **app/api/mcp_routes.py**: MCP endpoints for LLM/agent integration
- **app/services/**: Business logic and orchestration
- **app/models/**: Pydantic models for request/response validation
- **app/celery_tasks/**: Celery task definitions
- **app/controllers/**: Stateless controllers for external systems (Docker, Nuclei, etc.)

Routers are imported and registered in `main.py` using the new import paths (e.g., `from app.api.NucleiRoutes import router as nuclei_router`).

---

## Metrics & Monitoring

- **Redis** is used for caching vulnerability data and tracking pipeline metrics (templates generated, validated, refinements, failures, etc.).
- **Sentry** integration is available for error monitoring (configure via environment).
- **Pipeline Metrics**: Track template generation success rates, validation attempts, and scan performance.
- **Real-time Dashboard**: Monitor system health and performance through the web interface.

---

## Extending & Customizing

- **Add new vulnerability sources** by editing the `fetch_vulnerabilities` task.
- **Change LLM model or endpoint** via configuration.
- **Integrate with your own UI** or use the provided API directly.
- **Add new MCP tools** by extending the tools manifest and handler.
- **Customize scan workflows** by modifying the service layer.
- **Extend the frontend** with new components and pages.

---

## Contributing

Contributions are welcome! Please open issues or pull requests for bug fixes, new features, or improvements.

### Development Guidelines

1. **Code Style**: Follow PEP 8 for Python, ESLint for TypeScript
2. **Testing**: Add tests for new features and API endpoints
3. **Documentation**: Update README and add docstrings for new functions
4. **Docker**: Ensure changes work with the provided Docker setup

---

## License

[MIT](LICENSE) or as specified in the repository.

---

## Contact

For more details or support, please contact the development team.