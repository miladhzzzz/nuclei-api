import re, socket
from typing import Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse
from celery.result import AsyncResult
from celery_tasks.tasks import *
from pydantic import BaseModel, Field
from controllers.NucleiController import NucleiController
from controllers.DockerController import DockerController
from controllers.TemplateController import TemplateController

router = APIRouter()
nuclei_controller = NucleiController()
template_controller = TemplateController()

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
    prompt: str = Field(None, example="run a scan for finding this CVE on this Operating system") # Optional prompt field

# Pydantic model to validate 'get_logs' parameters
class ContainerIDRequest(BaseModel):
    container_id: str = Field(..., example="nuclei_scan_123456", pattern=r"^nuclei_scan_\d{6}$")  # Must start with 'nuclei_scan_' followed by 6 digits

@router.post("/scan")
@limiter.limit("5/minute")
async def custom_scan(request: Request, background_task: BackgroundTasks, scan_request: ScanRequest ):

    if not (is_valid_domain(scan_request.target) or is_valid_ip(scan_request.target)):
        raise HTTPException(status_code=400, detail="Invalid target. Must be a valid FQDN or IP address.")
    is_ip = is_valid_ip(scan_request.target)

    if scan_request.prompt:
        print("")
        
    if scan_request.templates:
        template_list = scan_request.templates
    # IP scan with pipeline (async, includes fingerprinting)
    if is_ip:
        task = scan_pipeline.delay(scan_request.target, templates=template_list)
        return {"task_id": task.id, "message": "Scan pipeline started"}
    # Standard scan for domains (sync, no fingerprinting)
    else:
        try:
            result = nuclei_controller.run_nuclei_scan(scan_request.target, template=template_list)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Standard scan failed: {str(e)}")


@router.post("/scan/custom")
@limiter.limit("5/minute")
async def unified_scan(
    background_tasks: BackgroundTasks,
    request: Request,
    target: str = Form(...),
    templates: Optional[list] = Form(default=None),  # Comma-separated string for simplicity
    template_file: Optional[UploadFile] = File(default=None),
):
    """
    Unified endpoint to start a Nuclei scan (standard, AI-driven, or custom).

    Args:
        target (str): The target to scan (domain or IP).
        templates (str, optional): Comma-separated list of templates for standard scan (e.g., "cves/,http/").
        template_file (UploadFile, optional): Custom YAML template file for custom scan.

    Returns:
        dict: Task ID and message for async scans, or direct result for synchronous scans.
    """
    # Validate target
    if not (is_valid_domain(target) or is_valid_ip(target)):
        raise HTTPException(status_code=400, detail="Invalid target. Must be a valid FQDN or IP address.")

    is_ip = is_valid_ip(target)
    template_list = templates.split(",") if templates else None

    # Custom scan with uploaded template
    if template_file:
        if not template_file.filename.lower().endswith(".yaml"):
            raise HTTPException(status_code=400, detail="Template must be a .yaml file.")
        content = await template_file.read()
        save_validation = await template_controller.save_template(content, template_file.filename)
        if save_validation:
            raise HTTPException(status_code=400, detail=f"Invalid template: {save_validation}")
        try:
            result = nuclei_controller.run_nuclei_scan(target, template_file=template_file.filename)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Custom scan failed: {str(e)}")
        
    # IP scan with pipeline (async, includes fingerprinting)
    elif is_ip:
        task = scan_pipeline.delay(target, templates=template_list)
        return {"task_id": task.id, "message": "Scan pipeline started"}

    # Standard scan for domains (sync, no fingerprinting)
    else:
        try:
            result = nuclei_controller.run_nuclei_scan(target, template=template_list)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Standard scan failed: {str(e)}")

@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Retrieve the status and result of an asynchronous scan task.

    Args:
        task_id (str): The Celery task ID returned by the /scan endpoint.

    Returns:
        dict: Task status and result (if completed).

    Authentication:
        Requires a valid JWT token in the Authorization header (Bearer <token>).
    """
    task_result = AsyncResult(task_id)
    if not task_result:
        raise HTTPException(status_code=404, detail="Task not found")

    response = {
        "task_id": task_id,
        "status": task_result.status,  # PENDING, STARTED, SUCCESS, FAILURE, etc.
    }

    if task_result.ready():
        if task_result.successful():
            response["result"] = task_result.result  # Container name or scan output
        else:
            response["error"] = str(task_result.result)  # Exception message if failed

    return response

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

@router.post("/template/upload")
@limiter.limit("5/minute")
async def upload_template(request: Request ,template_file: UploadFile = File):
    """
    Save a custom Nuclei template.

    Args:
        template_file (UploadFile): Custom Template YAML file.
    """
    # Validate template file presence and type
    if not template_file or not template_file.filename:
        raise HTTPException(status_code=400, detail="No template file provided.")
    if not template_file.filename.lower().endswith(".yaml"):
        raise HTTPException(status_code=400, detail="Template must be a .yaml file.")
    
    content = await template_file.read()

    # save the template
    save_validation =  await template_controller.save_template(content, template_file.filename)

    if save_validation is not None:
        raise HTTPException(status_code=400, detail=f"Invalid template: {save_validation}")
    
    return {"template_name": template_file.filename, "message": "Template Saved successfully"}


@router.get("/template/generate")
@limiter.limit("1/minute")
async def template_generate(request: Request):
    """
    Trigger the Nuclei template generation pipeline asynchronously.
    Returns the task ID for tracking.
    """
    try:
        # Trigger the Celery task asynchronously
        task_result: AsyncResult = generate_templates.delay()
        logger.info(f"Triggered template generation task with ID: {task_result.id}")
        
        # Return the task ID in the response for client tracking
        return {"task_id": task_result.id, "status": "Task queued successfully"}
    except Exception as e:
        logger.error(f"Failed to trigger template generation task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start task: {str(e)}")