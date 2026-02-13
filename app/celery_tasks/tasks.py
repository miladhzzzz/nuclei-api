import datetime
import os
import requests
import logging
import time
import redis
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from celery.result import GroupResult
from celery import chain, group, chord
from celery_config import celery_app
from helpers import config
from services import ScanService, TemplateService
from models.models import ScanRequest, ScanWithPromptRequest, ScanResponse, TaskStatusResponse, ComprehensiveScanRequest
from api.metrics_routes import record_celery_task, record_template_generation, record_template_validation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

redis_client = redis.Redis(
    host="redis",
    port=6379,
    db=0,
    decode_responses=True
)

scan_service = ScanService()
template_service = TemplateService()

@celery_app.task(bind=True, max_retries=3)
def fetch_vulnerabilities(self) -> List[Dict[str, Any]]:
    start_time = time.time()
    try:
        # Run the async method in an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(template_service.fetch_vulnerabilities(self))
        finally:
            loop.close()
        
        duration = time.time() - start_time
        record_celery_task("fetch_vulnerabilities", "success", duration)
        return result
    except Exception as e:
        duration = time.time() - start_time
        record_celery_task("fetch_vulnerabilities", "failed", duration)
        raise

@celery_app.task
def process_vulnerabilities(vuln_data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    start_time = time.time()
    try:
        result = template_service.process_vulnerabilities(vuln_data)
        duration = time.time() - start_time
        record_celery_task("process_vulnerabilities", "success", duration)
        return result
    except Exception as e:
        duration = time.time() - start_time
        record_celery_task("process_vulnerabilities", "failed", duration)
        raise

@celery_app.task
def generate_nuclei_template(cve_id: str, prompt: str) -> Optional[Dict[str, str]]:
    start_time = time.time()
    try:
        result = template_service.generate_nuclei_template(cve_id, prompt)
        duration = time.time() - start_time
        status = "success" if result else "failed"
        record_celery_task("generate_nuclei_template", status, duration)
        record_template_generation(cve_id, status)
        return result
    except Exception as e:
        duration = time.time() - start_time
        record_celery_task("generate_nuclei_template", "failed", duration)
        record_template_generation(cve_id, "failed")
        raise

@celery_app.task
def generate_nuclei_templates(processed_data: List[Dict[str, str]]) -> None:
    return template_service.generate_nuclei_templates(processed_data)

@celery_app.task
def store_templates(templates: List[Optional[Dict[str, str]]]) -> List[Dict[str, str]]:
    return template_service.store_templates(templates)

@celery_app.task
def refine_nuclei_template(cve_id: str, validation_error: str, current_template: str = None) -> str:
    """
    Refine a Nuclei template that failed validation.
    
    Args:
        cve_id: The CVE ID
        validation_error: The validation error message
        current_template: The current template content (optional)
        
    Returns:
        Refined template content
    """
    start_time = time.time()
    try:
        # Track refinement step
        template_service._track_refinement_step(cve_id, "llm_refinement_start", {
            "validation_error": validation_error,
            "has_current_template": current_template is not None
        })
        
        # Load the current template if not provided
        if not current_template:
            template_file = Path("/app/templates") / f"{cve_id}.yaml"
            if template_file.exists():
                current_template = template_file.read_text()
                template_service._track_refinement_step(cve_id, "template_loaded", {
                    "source": "file",
                    "template_length": len(current_template)
                })
            else:
                raise ValueError(f"Template file not found for {cve_id}")
        else:
            template_service._track_refinement_step(cve_id, "template_loaded", {
                "source": "parameter",
                "template_length": len(current_template)
            })
        
        # Load refinement prompt template
        try:
            with open(os.path.join(os.path.dirname(__file__), "refinement_template.txt"), "r") as f:
                refinement_prompt_template = f.read()
            template_service._track_refinement_step(cve_id, "prompt_template_loaded", {
                "template_found": True
            })
        except FileNotFoundError:
            logger.error("Refinement prompt template not found")
            refinement_prompt_template = "Fix this YAML template: {current_template}\nError: {validation_error}\nReturn only the corrected YAML:"
            template_service._track_refinement_step(cve_id, "prompt_template_loaded", {
                "template_found": False,
                "using_fallback": True
            })
        
        # Create refinement prompt
        refinement_prompt = refinement_prompt_template.format(
            cve_id=cve_id,
            validation_error=validation_error,
            current_template=current_template
        )
        
        template_service._track_refinement_step(cve_id, "llm_request_prepared", {
            "prompt_length": len(refinement_prompt),
            "ollama_url": conf.ollama_url or "http://ollama:11434/api/generate"
        })
        
        # Call LLM for refinement
        conf = config.Config()
        ollama_url = conf.ollama_url or "http://ollama:11434/api/generate"
        payload = {
            "model": conf.llm_model, 
            "prompt": refinement_prompt, 
            "stream": False
        }
        
        response = requests.post(ollama_url, json=payload, timeout=2000)
        response.raise_for_status()
        
        refined_template = response.json().get("response", "")
        if not refined_template:
            raise ValueError("No refinement response from LLM")
        
        template_service._track_refinement_step(cve_id, "llm_response_received", {
            "response_length": len(refined_template),
            "response_status": response.status_code
        })
        
        duration = time.time() - start_time
        record_celery_task("refine_nuclei_template", "success", duration)
        logger.info(f"Refined template for {cve_id}")
        
        return refined_template
        
    except Exception as e:
        duration = time.time() - start_time
        record_celery_task("refine_nuclei_template", "failed", duration)
        
        # Track refinement failure
        template_service._track_refinement_failure(cve_id, 1, str(e), duration)
        
        logger.error(f"Failed to refine template for {cve_id}: {str(e)}", exc_info=True)
        raise

@celery_app.task
def store_refined_template(cve_id: str, refined_template: str) -> Dict[str, str]:
    return template_service.store_refined_template(cve_id, refined_template)

@celery_app.task
def validate_template(cve_id: str, template_file: str, max_attempts: int = 3, attempt: int = 1) -> Dict[str, Any]:
    start_time = time.time()
    try:
        result = template_service.validate_template(cve_id, template_file, max_attempts, attempt)
        duration = time.time() - start_time
        status = "success" if result.get("status") == "success" else "failed"
        record_celery_task("validate_template", status, duration)
        record_template_validation(cve_id, status)
        return result
    except Exception as e:
        duration = time.time() - start_time
        record_celery_task("validate_template", "failed", duration)
        record_template_validation(cve_id, "failed")
        raise

@celery_app.task
def validate_templates_callback(templates: List[Dict[str, str]]) -> None:
    return template_service.validate_templates_callback(templates)

@celery_app.task
def generate_templates() -> None:
    return template_service.generate_templates()

@celery_app.task
def fingerprint_target(target: str) -> Optional[str]:
    return scan_service.fingerprint_target(target)

@celery_app.task(bind=True, max_retries=1)
def run_nuclei_scan(self, os_name: Optional[str], target: str, templates: Optional[List[str]] = None, template_file: Optional[str] = None) -> Dict[str, Any]:
    start_time = time.time()
    try:
        if template_file:
            result = scan_service.run_custom_template_scan(target, template_file)
        else:
            result = scan_service.run_scan(target, templates)
        duration = time.time() - start_time
        record_celery_task("run_nuclei_scan", "success", duration)
        return result
    except Exception as e:
        duration = time.time() - start_time
        record_celery_task("run_nuclei_scan", "failed", duration)
        raise

@celery_app.task
def fingerprint_scan_pipeline(target: str, templates: Optional[List[str]] = None, template_file: Optional[str] = None) -> Any:
    start_time = time.time()
    try:
        result = scan_service.fingerprint_scan_pipeline(target, templates, template_file)
        duration = time.time() - start_time
        record_celery_task("fingerprint_scan_pipeline", "success", duration)
        return result
    except Exception as e:
        duration = time.time() - start_time
        record_celery_task("fingerprint_scan_pipeline", "failed", duration)
        raise

@celery_app.task(bind=True, max_retries=1)
def ai_scan_pipeline(self, target: str, prompt: Optional[str] = None) -> Any:
    start_time = time.time()
    try:
        if prompt:
            result = scan_service.run_ai_scan(target, prompt)
        else:
            result = scan_service.run_scan(target, prompt=prompt)
        duration = time.time() - start_time
        record_celery_task("ai_scan_pipeline", "success", duration)
        return result
    except Exception as e:
        duration = time.time() - start_time
        record_celery_task("ai_scan_pipeline", "failed", duration)
        raise

@celery_app.task(bind=True, max_retries=1)
def run_custom_template_scan(self, target: str, template_content: str, template_filename: Optional[str] = None) -> Dict[str, Any]:
    start_time = time.time()
    try:
        result = scan_service.run_custom_template_scan(target, template_content, template_filename)
        duration = time.time() - start_time
        record_celery_task("run_custom_template_scan", "success", duration)
        return result
    except Exception as e:
        duration = time.time() - start_time
        record_celery_task("run_custom_template_scan", "failed", duration)
        raise

@celery_app.task(bind=True, max_retries=1)
def comprehensive_scan_pipeline(self, scan_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Comprehensive scan pipeline that handles all scan types.
    
    Args:
        scan_request: Dictionary containing scan parameters
        
    Returns:
        Scan results
    """
    start_time = time.time()
    try:
        # Extract parameters from scan request
        target = scan_request.get("target")
        scan_type = scan_request.get("scan_type", "auto")
        templates = scan_request.get("templates")
        template_file = scan_request.get("template_file")
        template_content = scan_request.get("template_content")
        prompt = scan_request.get("prompt")
        workflow_file = scan_request.get("workflow_file")
        use_fingerprinting = scan_request.get("use_fingerprinting", True)
        custom_parameters = scan_request.get("custom_parameters")
        
        # Run comprehensive scan
        result = scan_service.run_comprehensive_scan(
            target=target,
            scan_type=scan_type,
            templates=templates,
            template_file=template_file,
            template_content=template_content,
            prompt=prompt,
            workflow_file=workflow_file,
            use_fingerprinting=use_fingerprinting,
            custom_parameters=custom_parameters
        )
        
        duration = time.time() - start_time
        record_celery_task("comprehensive_scan_pipeline", "success", duration)
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        record_celery_task("comprehensive_scan_pipeline", "failed", duration)
        logger.error(f"Comprehensive scan pipeline failed: {str(e)}", exc_info=True)
        raise

@celery_app.task(bind=True, max_retries=1)
def auto_scan_pipeline(self, target: str, templates: Optional[List[str]] = None, use_fingerprinting: bool = True) -> Dict[str, Any]:
    """Auto scan pipeline with fingerprinting"""
    start_time = time.time()
    try:
        result = scan_service.run_comprehensive_scan(
            target=target,
            scan_type="auto",
            templates=templates,
            use_fingerprinting=use_fingerprinting
        )
        duration = time.time() - start_time
        record_celery_task("auto_scan_pipeline", "success", duration)
        return result
    except Exception as e:
        duration = time.time() - start_time
        record_celery_task("auto_scan_pipeline", "failed", duration)
        raise

@celery_app.task(bind=True, max_retries=1)
def workflow_scan_pipeline(self, target: str, workflow_file: str) -> Dict[str, Any]:
    """Workflow scan pipeline"""
    start_time = time.time()
    try:
        result = scan_service.run_comprehensive_scan(
            target=target,
            scan_type="workflow",
            workflow_file=workflow_file
        )
        duration = time.time() - start_time
        record_celery_task("workflow_scan_pipeline", "success", duration)
        return result
    except Exception as e:
        duration = time.time() - start_time
        record_celery_task("workflow_scan_pipeline", "failed", duration)
        raise

@celery_app.task
def fingerprint_only(target: str) -> Dict[str, Any]:
    """Fingerprint target only"""
    start_time = time.time()
    try:
        # Use the fingerprint controller directly
        from controllers.FingerprintController import FingerprintController
        fingerprint_controller = FingerprintController()
        result = fingerprint_controller.fingerprint_target(target)
        
        duration = time.time() - start_time
        record_celery_task("fingerprint_only", "success", duration)
        return {"target": target, "fingerprint": result}
    except Exception as e:
        duration = time.time() - start_time
        record_celery_task("fingerprint_only", "failed", duration)
        raise

@celery_app.task
def discover_targets(query: str = "vulnerable hosts", max_results: int = 50) -> Dict[str, Any]:
    """Discover targets using the enhanced controllers"""
    start_time = time.time()
    try:
        # Use the vulnerability source controller to find targets
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            from controllers.VulnerabilitySourceController import VulnerabilitySourceController
            vuln_controller = VulnerabilitySourceController()
            result = loop.run_until_complete(vuln_controller.fetch_vulnerabilities(query, max_results))
        finally:
            loop.close()
        
        duration = time.time() - start_time
        record_celery_task("discover_targets", "success", duration)
        return result
    except Exception as e:
        duration = time.time() - start_time
        record_celery_task("discover_targets", "failed", duration)
        raise

@celery_app.task
def validate_target_connectivity(target: Dict[str, Any]) -> Dict[str, Any]:
    """Validate target connectivity using TargetManagementController"""
    start_time = time.time()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            from controllers.TargetManagementController import TargetManagementController
            target_controller = TargetManagementController()
            result = loop.run_until_complete(target_controller.validate_target_connectivity(target))
        finally:
            loop.close()
        
        duration = time.time() - start_time
        record_celery_task("validate_target_connectivity", "success", duration)
        return result
    except Exception as e:
        duration = time.time() - start_time
        record_celery_task("validate_target_connectivity", "failed", duration)
        raise

@celery_app.task
def template_validation_pipeline(template_content: str, template_filename: Optional[str] = None) -> Dict[str, Any]:
    """Template validation pipeline"""
    start_time = time.time()
    try:
        # Save template to temporary file if content provided
        if template_content and not template_filename:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(template_content)
                template_filename = f.name
        
        if not template_filename:
            raise ValueError("No template file or content provided")
        
        # Validate template using TemplateController
        from controllers.TemplateController import TemplateController
        template_controller = TemplateController()
        validation_result = template_controller.validate_template_cel(template_filename)
        
        if validation_result:
            result = {"status": "failed", "error": validation_result}
        else:
            result = {"status": "success", "template_file": template_filename}
        
        duration = time.time() - start_time
        record_celery_task("template_validation_pipeline", "success", duration)
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        record_celery_task("template_validation_pipeline", "failed", duration)
        raise

@celery_app.task(bind=True, max_retries=1)
def run_scan(self, target: str, templates: Optional[List[str]] = None, prompt: Optional[str] = None):
    """Legacy scan task for backward compatibility"""
    start_time = time.time()
    try:
        if prompt:
            result = scan_service.run_ai_scan(target, prompt)
        else:
            result = scan_service.run_scan(target, templates)
        duration = time.time() - start_time
        record_celery_task("run_scan", "success", duration)
        return result
    except Exception as e:
        duration = time.time() - start_time
        record_celery_task("run_scan", "failed", duration)
        raise