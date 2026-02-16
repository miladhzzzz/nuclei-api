import re, socket
from typing import Optional, List
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, BackgroundTasks, Body
from fastapi.responses import StreamingResponse, JSONResponse
from celery.result import AsyncResult
from celery_tasks.tasks import *
from pydantic import BaseModel, Field, ValidationError
from models.models import (
    ScanRequest, ScanWithPromptRequest, ScanResponse, TaskStatusResponse, 
    CustomTemplateScanRequest, ComprehensiveScanRequest, FingerprintRequest,
    FingerprintResponse, TemplateUploadResponse, WorkflowUploadRequest, ScanResult
)
from services import ScanService, TemplateService
from controllers.DockerController import DockerController
from controllers.TemplateController import TemplateController
import logging

router = APIRouter()
scan_service = ScanService()
template_service = TemplateService()

logger = logging.getLogger(__name__)

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
limiter = Limiter(key_func=get_remote_address)

def is_valid_domain(value: str) -> bool:
    domain_regex = r"^(https?://)?(?!-)(?:[A-Za-z0-9-]{1,63}\.?)+$"
    return bool(re.match(domain_regex, value)) and '.' in value

def is_valid_ip(value: str) -> bool:
    try:
        socket.inet_pton(socket.AF_INET, value)
        return True
    except socket.error:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, value)
        return True
    except socket.error:
        pass
    return False

def _queue_or_503(task, *args):
    try:
        return task.delay(*args)
    except (OperationalError, RedisConnectionError) as exc:
        logger.error("Queue unavailable while dispatching v2 request: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Queue is temporarily unavailable (Redis/Celery). Please retry shortly.",
        )

# Legacy endpoints for backward compatibility
@router.post("/scan", response_model=ScanResponse)
@limiter.limit("20/minute")
async def custom_scan(request: Request, scan_request: ScanRequest):
    try:
        if not (is_valid_domain(scan_request.target) or is_valid_ip(scan_request.target)):
            logger.warning(f"Invalid target: {scan_request.target}")
            raise HTTPException(status_code=400, detail="Invalid target. Must be a valid FQDN or IP address.")
        
        task = run_scan.delay(scan_request.target, scan_request.templates, scan_request.prompt)
        return ScanResponse(task_id=task.id, message="Scan pipeline started")
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error in /scan endpoint for target {scan_request.target}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start scan. Please try again or contact support.")

@router.post("/scans", response_model=ScanResponse)
@limiter.limit("20/minute")
async def comprehensive_scan(request: Request, scan_request: ComprehensiveScanRequest):
    """
    Comprehensive scan endpoint that handles all scan types.
    
    Scan types:
    - auto: Intelligent scan with fingerprinting and OS-specific templates
    - fingerprint: Scan with fingerprinting and OS-specific templates
    - ai: AI-powered scan with custom prompt
    - custom: Scan with custom template
    - workflow: Scan using workflow file
    - standard: Standard scan with provided templates
    """
    try:
        if not (is_valid_domain(scan_request.target) or is_valid_ip(scan_request.target)):
            logger.warning(f"Invalid target: {scan_request.target}")
            raise HTTPException(status_code=400, detail="Invalid target. Must be a valid FQDN or IP address.")
        
        # Convert Pydantic model to dict for Celery task
        scan_request_dict = scan_request.dict()
        
        # Queue the comprehensive scan task
        task = comprehensive_scan_pipeline.delay(scan_request_dict)
        
        return ScanResponse(task_id=task.id, message=f"Comprehensive {scan_request.scan_type} scan started")
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error in /scan/comprehensive endpoint for target {scan_request.target}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start comprehensive scan. Please try again or contact support.")

@router.post("/scans/ai", response_model=ScanResponse)
@limiter.limit("20/minute")
async def scan_with_prompt(request: Request, scan_request: ScanWithPromptRequest):
    try:
        if not (is_valid_domain(scan_request.target) or is_valid_ip(scan_request.target)):
            logger.warning(f"Invalid target: {scan_request.target}")
            raise HTTPException(status_code=400, detail="Invalid target. Must be a valid FQDN or IP address.")
        
        task = ai_scan_pipeline.delay(scan_request.target, scan_request.prompt)
        return ScanResponse(task_id=task.id, message="AI scan pipeline started")
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error in /scan/ai endpoint for target {scan_request.target}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start AI scan. Please try again or contact support.")

@router.post("/fingerprints", response_model=FingerprintResponse)
@limiter.limit("10/minute")
async def fingerprint_target_endpoint(request: Request, fingerprint_request: FingerprintRequest):
    """Fingerprint a target without running a scan."""
    try:
        if not (is_valid_domain(fingerprint_request.target) or is_valid_ip(fingerprint_request.target)):
            logger.warning(f"Invalid target: {fingerprint_request.target}")
            raise HTTPException(status_code=400, detail="Invalid target. Must be a valid FQDN or IP address.")
        
        task = fingerprint_only.delay(fingerprint_request.target)
        return FingerprintResponse(
            target=fingerprint_request.target,
            task_id=task.id,
            message="Fingerprinting started"
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error in /fingerprint endpoint for target {fingerprint_request.target}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start fingerprinting. Please try again or contact support.")

@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(request: Request, task_id: str):
    try:
        # Check if this is a container name (nuclei_scan_XXXXXX format)
        if task_id.startswith("nuclei_scan_") and len(task_id.split("_")) == 3:
            # This is a container name, get container status
            docker_controller = DockerController()
            container_status = docker_controller.get_container_status(task_id)
            
            if "error" in container_status:
                raise HTTPException(status_code=404, detail=f"Container not found: {task_id}")
            
            # Map container status to task status
            if container_status.get("running", False):
                status = "PENDING"
            elif container_status.get("status") == "exited":
                status = "SUCCESS"
            else:
                status = "FAILURE"
            
            response = TaskStatusResponse(task_id=task_id, status=status)
            
            # If container is finished, get the logs
            if status in ["SUCCESS", "FAILURE"]:
                try:
                    logs = docker_controller.get_container_logs(task_id)
                    response.result = {"logs": logs, "container_status": container_status}
                except Exception as e:
                    logger.warning(f"Failed to get logs for container {task_id}: {e}")
                    response.result = {"container_status": container_status}
            
            return response
        else:
            # This is a Celery task ID
            task_result = AsyncResult(task_id)
            if not task_result:
                logger.warning(f"Task not found: {task_id}")
                raise HTTPException(status_code=404, detail="Task not found")
            
            response = TaskStatusResponse(task_id=task_id, status=task_result.status)
            if task_result.ready():
                if task_result.successful():
                    result = task_result.result
                    response.result = result
                    
                    # If the task result contains a container name, also provide container logs
                    if isinstance(result, dict) and "container_name" in result:
                        container_name = result["container_name"]
                        try:
                            docker_controller = DockerController()
                            container_status = docker_controller.get_container_status(container_name)
                            
                            # Get container logs if available
                            if container_status.get("status") == "exited":
                                logs = docker_controller.get_container_logs(container_name)
                                if "logs" not in response.result:
                                    response.result["logs"] = logs
                                response.result["container_status"] = container_status
                                
                        except Exception as e:
                            logger.warning(f"Failed to get container logs for {container_name}: {e}")
                    
                else:
                    response.error = str(task_result.result)
            return response
            
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error in /task/{task_id} endpoint: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch task status. Please try again or contact support.")

@router.get("/containers/{container_id}/logs", response_class=StreamingResponse)
@limiter.limit("20/minute")
async def get_logs(request: Request, container_id: str):
    try:
        docker_controller = DockerController()
        if not re.match(r"^nuclei_scan_\d{6}$", container_id):
            logger.warning(f"Invalid container ID: {container_id}")
            raise HTTPException(status_code=400, detail="Invalid container ID.")
        async def log_stream():
            logs = []
            for log_line in docker_controller.stream_container_logs(container_id):
                clean_log = ANSI_ESCAPE.sub('', log_line)
                logs.append(clean_log)
            for log in logs:
                yield f"{log}\n"
        return StreamingResponse(log_stream(), media_type="application/json")
    except Exception as exc:
        logger.error(f"Error in /scan/{container_id}/logs endpoint: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch logs. Please try again or contact support.")

@router.get("/containers/{container_name}/status")
@limiter.limit("20/minute")
async def get_container_status(request: Request, container_name: str):
    """
    Get status for any container by name.
    Useful for monitoring scan progress.
    """
    try:
        docker_controller = DockerController()
        
        # Validate container name format
        if not re.match(r"^[a-zA-Z0-9_-]+$", container_name):
            logger.warning(f"Invalid container name format: {container_name}")
            raise HTTPException(status_code=400, detail="Invalid container name format.")
        
        # Get container status
        container_status = docker_controller.get_container_status(container_name)
        if "error" in container_status:
            raise HTTPException(status_code=404, detail=f"Container not found: {container_name}")
        
        return {"container_name": container_name, "status": container_status}
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error in /container/{container_name}/status endpoint: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch container status. Please try again or contact support.")

@router.post("/templates/validate", response_model=TemplateUploadResponse)
@limiter.limit("10/minute")
async def validate_template_endpoint(request: Request, template_content: str = Body(..., embed=True), template_filename: Optional[str] = Body(None, embed=True)):
    """Validate a template without running a scan."""
    try:
        task = template_validation_pipeline.delay(template_content, template_filename)
        return TemplateUploadResponse(
            filename=template_filename or "template.yaml",
            message="Template validation started",
            task_id=task.id
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error in /template/validate endpoint: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to validate template. Please try again or contact support.")

@router.post("/templates/upload")
@limiter.limit("5/minute")
async def upload_template(request: Request, template_file: UploadFile = File(...)):
    try:
        if not template_file.filename.endswith('.yaml') and not template_file.filename.endswith('.yml'):
            raise HTTPException(status_code=400, detail="Template file must be a YAML file (.yaml or .yml)")
        
        content = await template_file.read()
        error = template_service.upload_template(content, template_file.filename)
        
        if error:
            raise HTTPException(status_code=500, detail=error)
        
        return TemplateUploadResponse(
            filename=template_file.filename,
            message="Template uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error in /template/upload endpoint: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload template. Please try again or contact support.")

@router.get("/templates/generate")
@limiter.limit("1/minute")
async def template_generate(request: Request):
    try:
        template_service.generate_templates()
        return {"message": "Template generation pipeline started"}
    except Exception as exc:
        logger.error(f"Error in /template/generate endpoint: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start template generation. Please try again or contact support.")