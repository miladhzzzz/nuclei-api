import os
import requests
import logging
import time
import redis
import base64
import uuid
from services.helper import clean_yaml_content, validate_yaml_structure
from pathlib import Path
from typing import List, Dict, Optional, Any
from helpers import config
from controllers.NucleiController import NucleiController
from controllers.FingerprintController import FingerprintController
from controllers.TemplateController import TemplateController
from api.metrics_routes import (
    record_nuclei_scan, 
    record_template_validation,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

conf = config.Config()
redis_client = redis.Redis.from_url(conf.redis_url, decode_responses=True)
TEMPLATE_DIR = Path(conf.template_dir)
OLLAMA_URL_DEFAULT = conf.ollama_url
OLLAMA_TIMEOUT = conf.ollama_timeout

try:
    with open(os.path.join(os.path.dirname(__file__), "../celery_tasks/template.txt"), "r") as f:
        PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    logger.error("Prompt template file not found")
    PROMPT_TEMPLATE = "Generate a Nuclei template for {cve_id} with description: {description}"


class ScanService:
    def __init__(self):
        self.conf = config.Config()
        self.nuclei_controller = NucleiController()
        self.fingerprint_controller = FingerprintController()
        self.template_controller = TemplateController()

    def fingerprint_target(self, target: str) -> Optional[str]:
        """
        Fingerprint a target to determine OS and other characteristics.
        
        Args:
            target: Target IP or domain
            
        Returns:
            OS name if detected, None otherwise
        """
        try:
            response = self.fingerprint_controller.fingerprint_target(target)
            os_name = response if isinstance(response, str) else response.get("os")
            if not os_name:
                logger.warning(f"No OS detected for {target}")
                return None
            logger.info(f"Detected OS for {target}: {os_name}")
            return os_name
        except Exception as e:
            logger.error(f"Fingerprinting failed for {target}: {str(e)}", exc_info=True)
            return None

    def get_os_specific_templates(self, os_name: str) -> List[str]:
        """
        Get OS-specific template categories based on detected OS.
        
        Args:
            os_name: Detected OS name
            
        Returns:
            List of template categories to use
        """
        os_template_map = {
            "Linux": ["linux/", "unix/", "http/"],
            "Windows": ["windows/", "http/"],
            "macOS": ["macos/", "unix/", "http/"],
            "FreeBSD": ["unix/", "http/"],
            "OpenBSD": ["unix/", "http/"],
            "NetBSD": ["unix/", "http/"]
        }
        
        return os_template_map.get(os_name, ["http/"])

    def run_comprehensive_scan(self, 
                             target: str, 
                             scan_type: str = "auto",
                             templates: Optional[List[str]] = None,
                             template_file: Optional[str] = None,
                             template_content: Optional[str] = None,
                             prompt: Optional[str] = None,
                             workflow_file: Optional[str] = None,
                             use_fingerprinting: bool = True,
                             custom_parameters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Comprehensive scan method that handles all scan scenarios.
        
        Args:
            target: Target to scan (IP or domain)
            scan_type: Type of scan - "auto", "fingerprint", "ai", "custom", "workflow", "standard"
            templates: List of template categories to use
            template_file: Path to custom template file
            template_content: Base64 encoded template content
            prompt: Natural language prompt for AI scan
            workflow_file: Path to workflow file
            use_fingerprinting: Whether to use fingerprinting for OS detection
            custom_parameters: Additional custom parameters
            
        Returns:
            Dict containing scan results or error information
        """
        try:
            start_time = time.time()
            logger.info(f"Starting comprehensive scan for {target} with type: {scan_type}")
            
            # Validate target
            if not self._validate_target(target):
                return {"error": f"Invalid target: {target}"}
            
            # Determine scan approach based on scan_type
            if scan_type == "auto":
                return self._run_auto_scan(target, templates, use_fingerprinting, custom_parameters)
            elif scan_type == "fingerprint":
                return self._run_fingerprint_scan(target, templates, custom_parameters)
            elif scan_type == "ai":
                return self._run_ai_scan(target, prompt, custom_parameters)
            elif scan_type == "custom":
                return self._run_custom_template_scan(target, template_file, template_content, custom_parameters)
            elif scan_type == "workflow":
                return self._run_workflow_scan(target, workflow_file, custom_parameters)
            elif scan_type == "standard":
                return self._run_standard_scan(target, templates, custom_parameters)
            else:
                return {"error": f"Unknown scan type: {scan_type}"}
                
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_scan_metrics(target, "comprehensive", "failed", duration)
            logger.error(f"Comprehensive scan failed for {target}: {str(e)}", exc_info=True)
            return {"error": f"Comprehensive scan failed for {target}: {str(e)}"}

    def _validate_target(self, target: str) -> bool:
        """Validate target format."""
        import socket
        import re
        
        # Check if it's a valid IP
        try:
            socket.inet_pton(socket.AF_INET, target)
            return True
        except socket.error:
            pass
        
        try:
            socket.inet_pton(socket.AF_INET6, target)
            return True
        except socket.error:
            pass
        
        # Check if it's a valid domain
        domain_regex = r"^(https?://)?(?!-)(?:[A-Za-z0-9-]{1,63}\.?)+$"
        return bool(re.match(domain_regex, target)) and '.' in target

    def _run_auto_scan(self, target: str, templates: Optional[List[str]], use_fingerprinting: bool, custom_parameters: Optional[Dict]) -> Dict[str, Any]:
        """Run automatic scan with intelligent template selection."""
        try:
            start_time = time.time()
            
            # Use fingerprinting if enabled
            if use_fingerprinting:
                os_name = self.fingerprint_target(target)
                if os_name:
                    templates = self.get_os_specific_templates(os_name)
                    logger.info(f"Using OS-specific templates for {target}: {templates}")
                else:
                    templates = templates or ["http/"]
                    logger.info(f"Using fallback templates for {target}: {templates}")
            else:
                templates = templates or ["http/"]
            
            # Run the scan
            result = self.nuclei_controller.run_nuclei_scan(target=target, template=templates)
            
            duration = time.time() - start_time
            self._record_scan_metrics(target, "auto", "success" if "error" not in result else "failed", duration)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_scan_metrics(target, "auto", "failed", duration)
            raise

    def _run_fingerprint_scan(self, target: str, templates: Optional[List[str]], custom_parameters: Optional[Dict]) -> Dict[str, Any]:
        """Run scan with fingerprinting and OS-specific templates."""
        try:
            start_time = time.time()
            
            # Always use fingerprinting for this scan type
            os_name = self.fingerprint_target(target)
            if os_name:
                templates = self.get_os_specific_templates(os_name)
                logger.info(f"Using OS-specific templates for {target}: {templates}")
            else:
                templates = templates or ["http/"]
                logger.info(f"Using fallback templates for {target}: {templates}")
            
            # Run the scan
            result = self.nuclei_controller.run_nuclei_scan(target=target, template=templates)
            
            # Add fingerprinting info to result
            if os_name:
                result["fingerprinting"] = {"os_detected": os_name, "templates_used": templates}
            
            duration = time.time() - start_time
            self._record_scan_metrics(target, "fingerprint", "success" if "error" not in result else "failed", duration)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_scan_metrics(target, "fingerprint", "failed", duration)
            raise

    def _run_ai_scan(self, target: str, prompt: str, custom_parameters: Optional[Dict]) -> Dict[str, Any]:
        """Run AI-powered scan with custom prompt."""
        try:
            start_time = time.time()
            logger.info(f"Starting AI scan for {target} with prompt: {prompt}")
            
            # Generate template using LLM
            ollama_url = self.conf.ollama_url or OLLAMA_URL_DEFAULT
            
            # Create enhanced prompt for template generation
            template_prompt = f"""
Generate a comprehensive Nuclei template to scan for: {prompt}

Target: {target}

Create a template that will detect vulnerabilities related to this description.
The template should be specific, accurate, and follow Nuclei best practices.

Template requirements:
- Must have a unique ID
- Include proper info section with name, author, severity, description
- Use appropriate HTTP methods and paths
- Include proper matchers and extractors
- Follow YAML syntax correctly

Return only valid YAML without markdown formatting.

Generate the template:
"""
            
            # Call LLM to generate template
            payload = {
                "model": self.conf.llm_model,
                "prompt": template_prompt,
                "stream": False
            }
            
            response = requests.post(ollama_url, json=payload, timeout=OLLAMA_TIMEOUT)
            response.raise_for_status()
            
            raw_template = response.json().get("response", "")
            if not raw_template:
                return {"error": "No template generated by LLM"}
            
            # Clean and validate the template
            cleaned_template = clean_yaml_content(raw_template)
            is_valid, error_msg = validate_yaml_structure(cleaned_template)
            
            if not is_valid:
                logger.warning(f"Generated template has issues: {error_msg}")
                return {"error": f"Generated template is invalid: {error_msg}"}
            
            upload_dir = Path(self.conf.nuclei_upload_template_path)
            upload_dir.mkdir(parents=True, exist_ok=True)
            template_filename = f"ai-{uuid.uuid4().hex}.yaml"
            template_path = upload_dir / template_filename
            template_path.write_text(cleaned_template)

            # Run the scan with the generated template from mounted templates directory.
            result = self.nuclei_controller.run_nuclei_scan(
                target=target,
                template_file=template_filename
            )
            
            # Add template info to result
            result["ai_generated_template"] = cleaned_template
            result["prompt"] = prompt
            
            duration = time.time() - start_time
            self._record_scan_metrics(target, "ai", "success" if "error" not in result else "failed", duration)
            
            logger.info(f"AI scan completed for {target}")
            return result
                    
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_scan_metrics(target, "ai", "failed", duration)
            raise

    def _run_custom_template_scan(self, target: str, template_file: Optional[str], template_content: Optional[str], custom_parameters: Optional[Dict]) -> Dict[str, Any]:
        """Run scan with custom template."""
        try:
            start_time = time.time()
            
            # Determine template source
            upload_dir = Path(self.conf.nuclei_upload_template_path)
            upload_dir.mkdir(parents=True, exist_ok=True)

            if template_content:
                # Use base64 encoded template content and persist it in mounted custom dir.
                try:
                    template_bytes = base64.b64decode(template_content)
                    template_yaml = template_bytes.decode('utf-8')
                except Exception as e:
                    return {"error": f"Invalid template content: {str(e)}"}

                template_filename = f"custom-{uuid.uuid4().hex}.yaml"
                template_path = upload_dir / template_filename
                template_path.write_text(template_yaml)
            elif template_file:
                # Use existing template filename from custom dir.
                template_filename = os.path.basename(template_file)
                template_path = upload_dir / template_filename
                if not template_path.exists():
                    return {"error": f"Template file not found: {template_filename}"}
                
            else:
                return {"error": "Either template_file or template_content must be provided"}
            
            # Validate the template
            validation_error = self.template_controller.validate_template_cel(str(template_path))
            if validation_error is not None:
                logger.error(f"Template validation failed: {validation_error}")
                record_template_validation("custom", "failed")
                return {"error": f"Template validation failed: {validation_error}"}
            
            record_template_validation("custom", "success")
            
            # Run the scan via mounted custom template name.
            result = self.nuclei_controller.run_nuclei_scan(
                target=target,
                template_file=template_filename
            )
            
            duration = time.time() - start_time
            self._record_scan_metrics(target, "custom", "success" if "error" not in result else "failed", duration)
            
            logger.info(f"Custom template scan completed for {target}")
            return result
                        
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_scan_metrics(target, "custom", "failed", duration)
            raise

    def _run_workflow_scan(self, target: str, workflow_file: str, custom_parameters: Optional[Dict]) -> Dict[str, Any]:
        """Run scan using workflow file."""
        try:
            start_time = time.time()
            
            upload_dir = Path(self.conf.nuclei_upload_template_path)
            workflow_name = os.path.basename(workflow_file)
            workflow_path = upload_dir / workflow_name

            # Validate workflow file exists in mounted custom templates directory.
            if not workflow_path.exists():
                return {"error": f"Workflow file not found: {workflow_name}"}
            
            # Run the scan with workflow
            result = self.nuclei_controller.run_nuclei_scan(
                target=target,
                template_file=workflow_name
            )
            
            duration = time.time() - start_time
            self._record_scan_metrics(target, "workflow", "success" if "error" not in result else "failed", duration)
            
            logger.info(f"Workflow scan completed for {target}")
            return result
            
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_scan_metrics(target, "workflow", "failed", duration)
            raise

    def _run_standard_scan(self, target: str, templates: Optional[List[str]], custom_parameters: Optional[Dict]) -> Dict[str, Any]:
        """Run standard scan with provided templates."""
        try:
            start_time = time.time()
            
            templates = templates or ["http/"]
            
            # Run the scan
            result = self.nuclei_controller.run_nuclei_scan(target=target, template=templates)
            
            duration = time.time() - start_time
            self._record_scan_metrics(target, "standard", "success" if "error" not in result else "failed", duration)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            self._record_scan_metrics(target, "standard", "failed", duration)
            raise

    def _record_scan_metrics(self, target: str, scan_type: str, status: str, duration: float):
        """Record scan metrics."""
        try:
            target_type = "domain" if "." in target else "ip"
            record_nuclei_scan(
                target_type=target_type,
                template_type=scan_type,
                status=status,
                duration=duration
            )
        except Exception as e:
            logger.warning(f"Failed to record scan metrics: {str(e)}")

    # Legacy methods for backward compatibility
    def run_scan(self, target: str, templates: Optional[List[str]] = None, prompt: Optional[str] = None):
        """Legacy scan method - redirects to comprehensive scan."""
        if prompt:
            return self.run_comprehensive_scan(target, scan_type="ai", prompt=prompt)
        else:
            return self.run_comprehensive_scan(target, scan_type="standard", templates=templates)

    def run_ai_scan(self, target: str, prompt: str):
        """Legacy AI scan method."""
        return self.run_comprehensive_scan(target, scan_type="ai", prompt=prompt)

    def run_custom_template_scan(self, target: str, template_content: str, template_filename: Optional[str] = None):
        """Legacy custom template scan method."""
        return self.run_comprehensive_scan(target, scan_type="custom", template_content=template_content)

    def fingerprint_scan_pipeline(self, target: str, templates: Optional[List[str]] = None, template_file: Optional[str] = None):
        """Legacy fingerprint scan pipeline."""
        return self.run_comprehensive_scan(target, scan_type="fingerprint", templates=templates)
