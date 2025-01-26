import re
import socket
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from controllers.NucleiController import NucleiController
from controllers.DockerController import DockerController

router = APIRouter()
nuclei_controller = NucleiController()

# Custom validation function for domain and IP
def is_valid_domain(value: str) -> bool:
    # Simple domain regex to match a domain with at least one period (.)
    domain_regex = r"^(?!-)(?:[A-Za-z0-9-]{1,63}\.?)+$"  # Basic regex for domain
    return bool(re.match(domain_regex, value)) and '.' in value

def is_valid_ip(value: str) -> bool:
    # Check if it's a valid IPv4 address
    try:
        socket.inet_pton(socket.AF_INET, value)  # IPv4 check
        return True
    except socket.error:
        pass

    # Check if it's a valid IPv6 address
    try:
        socket.inet_pton(socket.AF_INET6, value)  # IPv6 check
        return True
    except socket.error:
        pass

    return False

# Pydantic model for the scan request
class ScanRequest(BaseModel):
    target: str = Field(..., example="google.com")  # Relaxed regex to allow letters, numbers, dots, hyphens
    template: str = Field(None, example="cves")  # Optional template field   
# Pydantic model to validate 'get_logs' parameters
class ContainerIDRequest(BaseModel):
    container_id: str = Field(..., example="nuclei_scan_123456", pattern=r"^nuclei_scan_\d{6}$")  # Must start with 'nuclei_scan_' followed by 6 digits

@router.post("/scan")
async def run_scan(scan_request: ScanRequest):
    """
    Start a Nuclei scan for the given target.
    
    Args:
        target (str): The target to scan.
        template (str): Optional template to use.
    """
    # Validate target: check if it's a valid domain or IP address
    if not (is_valid_domain(scan_request.target) or is_valid_ip(scan_request.target)):
        raise HTTPException(status_code=400, detail="Invalid target. Must be a valid FQDN or IP address.")
    
    try:
        result = nuclei_controller.run_nuclei_scan(scan_request.target, scan_request.template)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scan/{container_id}/logs", response_class=StreamingResponse)
async def get_logs(container_id: str):
    """
    API endpoint to stream container logs as a JSON stream.

    Args:
        container_name (str): The Name of the container.
    Returns:
        StreamingResponse: Real-time logs as JSON.
    """
    docker_controller = DockerController()

    # Validate the container_id with a regex pattern
    if not re.match(r"^nuclei_scan_\d{6}$", container_id):
        raise HTTPException(status_code=400, detail="Invalid container ID.")

    async def log_stream():
        for log_line in docker_controller.stream_container_logs(container_id):
            yield f"{log_line}\n"  # Ensure newline after each JSON object

    return StreamingResponse(log_stream(), media_type="application/json")