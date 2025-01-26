from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from controllers.NucleiController import NucleiController
from controllers.DockerController import DockerController

router = APIRouter()
nuclei_controller = NucleiController()

@router.post("/scan")
async def run_scan(target: str, template: str = None):
    """
    Start a Nuclei scan for the given target.
    
    Args:
        target (str): The target to scan.
        template (str): Optional template to use.
    """
    try:
        result = nuclei_controller.run_nuclei_scan(target, template)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scan/{container_id}/logs", response_class=StreamingResponse)
async def get_logs(container_id: str):
    """
    API endpoint to stream container logs as a JSON stream.

    Args:
        container_id (str): The ID of the container.

    Returns:
        StreamingResponse: Real-time logs as JSON.
    """
    docker_controller = DockerController()

    async def log_stream():
        for log_line in docker_controller.stream_container_logs(container_id):
            yield f"{log_line}\n"  # Ensure newline after each JSON object

    return StreamingResponse(log_stream(), media_type="application/json")