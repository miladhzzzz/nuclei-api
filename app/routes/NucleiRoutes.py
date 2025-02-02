import re, socket
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from controllers.NucleiController import NucleiController
from controllers.DockerController import DockerController

router = APIRouter()
nuclei_controller = NucleiController()

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

# Initialize Limiter
limiter = Limiter(key_func=get_remote_address)

# Custom validation function for domain and IP
def is_valid_domain(value: str) -> bool:
    # Regex to match domains with optional http:// or https://
    domain_regex = r"^(https?://)?(?!-)(?:[A-Za-z0-9-]{1,63}\.?)+$"
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
    templates: list = Field(None, example="cves/")  # Optional template field   
# Pydantic model to validate 'get_logs' parameters
class ContainerIDRequest(BaseModel):
    container_id: str = Field(..., example="nuclei_scan_123456", pattern=r"^nuclei_scan_\d{6}$")  # Must start with 'nuclei_scan_' followed by 6 digits

@router.post("/scan")
@limiter.limit("5/minute")
async def run_scan(scan_request: ScanRequest, request: Request):
    """
    Start a Nuclei scan for the given target.
    
    Args:
        target (str): The target to scan.
        template (list): Optional templates to use.
    """
    # Validate target: check if it's a valid domain or IP address
    if not (is_valid_domain(scan_request.target) or is_valid_ip(scan_request.target)):
        raise HTTPException(status_code=400, detail="Invalid target. Must be a valid FQDN or IP address.")
    try:
        result = nuclei_controller.run_nuclei_scan(scan_request.target, scan_request.templates)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scan/{container_id}/logs", response_class=StreamingResponse)
@limiter.limit("20/minute")
async def get_logs(container_id: str, request: Request):
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
        logs = []  # List to collect the logs in the reverse order
        for log_dict in docker_controller.stream_container_logs(container_id):  # Use regular for loop
                # Extract the first key from the dictionary
                log_line = list(log_dict)[0]  # Assumes the first value is the log message
                # print(log_line)
                # Clean the log line by removing ANSI escape sequences
                clean_log = ANSI_ESCAPE.sub('', log_line)
                
                # Append the cleaned log message to the list
                logs.append(clean_log)

        # Now, yield logs in the correct order (reversed)
        for log in logs:
            yield f"{log}\n"  # Add a newline after each cleaned log

    return StreamingResponse(log_stream(), media_type="application/json")