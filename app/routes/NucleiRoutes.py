import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from controllers.NucleiController import NucleiController
from controllers.DockerController import DockerController

router = APIRouter()
nuclei_controller = NucleiController()

# Pydantic model to validate 'run_scan' parameters
class ScanRequest(BaseModel):
    target: str = Field(..., example="google.com", pattern=r"^[a-zA-Z0-9.-]+$")  # Allow domain names or IPs
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