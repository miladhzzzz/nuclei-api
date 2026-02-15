import os
import requests
import time
import json
import asyncio
from services.helper import (
    logger,
    redis_client,
    TEMPLATE_DIR,
    OLLAMA_URL_DEFAULT,
    OLLAMA_TIMEOUT,
    PROMPT_TEMPLATE,
    conf,
    clean_yaml_content,
    validate_yaml_structure,
)
from pathlib import Path
from typing import List, Dict, Optional, Any
from celery import chain, group, chord
from controllers.NucleiController import NucleiController
from controllers.FingerprintController import FingerprintController
from controllers.TemplateController import TemplateController
from controllers.VulnerabilitySourceController import VulnerabilitySourceController
from controllers.TargetManagementController import TargetManagementController
from api.metrics_routes import (
    record_template_generation, 
    record_template_validation,
)

class TemplateService:
    def __init__(self):
        self.template_controller = TemplateController()
        self.vulnerability_source_controller = VulnerabilitySourceController()
        self.target_management_controller = TargetManagementController()
        self.nuclei_controller = NucleiController()

    async def fetch_vulnerabilities(self, celery_self) -> List[Dict[str, Any]]:
        """Fetch vulnerabilities using the enhanced VulnerabilitySourceController"""
        try:
            cache_key = "all_vulnerabilities"
            cached = redis_client.get(cache_key)
            if cached:
                logger.info("Using cached vulnerabilities")
                return json.loads(cached)
            
            # Use the enhanced vulnerability source controller
            result = await self.vulnerability_source_controller.fetch_vulnerabilities(
                query="recent high severity vulnerabilities", 
                max_results=50
            )
            
            vulnerabilities = result.get("results", [])
            
            # Cache the results
            redis_client.setex(cache_key, 43200, json.dumps(vulnerabilities))
            logger.info(f"Cached {len(vulnerabilities)} vulnerabilities")
            return vulnerabilities
            
        except Exception as e:
            logger.error(f"Error fetching vulnerabilities: {str(e)}", exc_info=True)
            return []

    def process_vulnerabilities(self, vuln_data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Process vulnerabilities for template generation"""
        try:
            processed = []
            for vuln in vuln_data:
                cve_id = vuln.get("cve_id", vuln.get("id", "Unknown"))
                description = vuln.get("description", "No description")
                prompt = PROMPT_TEMPLATE.format(cve_id=cve_id, description=description)
                processed.append({"cve_id": cve_id, "prompt": prompt})
            logger.info(f"Processed {len(processed)} vulnerabilities")
            return processed
        except Exception as e:
            logger.error(f"Error processing vulnerabilities: {str(e)}", exc_info=True)
            return []

    def generate_nuclei_template(self, cve_id: str, prompt: str) -> Optional[Dict[str, str]]:
        """Generate Nuclei template using LLM"""
        try:
            file_path = TEMPLATE_DIR / f"{cve_id}.yaml"
            if file_path.exists():
                logger.info(f"Template for {cve_id} already exists, skipping generation")
                record_template_generation(cve_id, "skipped")
                return {"cve_id": cve_id, "template": file_path.read_text()}
                
            logger.info(f"Starting template generation for {cve_id}")
            ollama_url = conf.ollama_url or OLLAMA_URL_DEFAULT
            payload = {"model": conf.llm_model, "prompt": prompt, "stream": False}
            response = requests.post(ollama_url, json=payload, timeout=OLLAMA_TIMEOUT)
            response.raise_for_status()
            
            raw_template = response.json().get("response", "")
            if not raw_template:
                logger.warning(f"No template generated for {cve_id}")
                record_template_generation(cve_id, "failed")
                return None
                
            # Clean and validate the template
            cleaned_template = clean_yaml_content(raw_template)
            is_valid, error_msg = validate_yaml_structure(cleaned_template)
            
            if not is_valid:
                logger.warning(f"Generated template for {cve_id} has structural issues: {error_msg}")
                # Store the raw template for refinement
                return {
                    "cve_id": cve_id, 
                    "template": cleaned_template,
                    "needs_refinement": True,
                    "validation_error": error_msg
                }
            
            logger.info(f"Generated valid template for {cve_id}")
            record_template_generation(cve_id, "success")
            return {"cve_id": cve_id, "template": cleaned_template}
            
        except Exception as e:
            logger.error(f"Failed to generate template for {cve_id}: {str(e)}", exc_info=True)
            record_template_generation(cve_id, "failed")
            return None

    def generate_nuclei_templates(self, processed_data: List[Dict[str, str]]) -> None:
        """Generate templates using Celery tasks"""
        try:
            from celery_tasks.tasks import generate_nuclei_template, store_templates, validate_templates_callback
            logger.info(f"Starting template generation for {len(processed_data)} vulnerabilities")
            if not processed_data:
                logger.warning("No vulnerabilities to process")
                return None
            job = [generate_nuclei_template.s(item["cve_id"], item["prompt"]) for item in processed_data]
            chord(group(job))(chain(store_templates.s(), validate_templates_callback.s()))
            logger.info(f"Queued {len(processed_data)} template generation tasks with chord callback")
        except Exception as e:
            logger.error(f"Error generating nuclei templates: {str(e)}", exc_info=True)

    def store_templates(self, templates: List[Optional[Dict[str, str]]]) -> List[Dict[str, str]]:
        """Store generated templates"""
        try:
            TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
            stored_templates = []
            templates_needing_refinement = []
            
            for item in templates:
                if not item or not item.get("template"):
                    logger.warning(f"Skipping empty or invalid template: {item}")
                    continue
                    
                cve_id = item["cve_id"]
                template_content = item["template"]
                file_path = TEMPLATE_DIR / f"{cve_id}.yaml"
                
                # Check if template needs refinement
                if item.get("needs_refinement", False):
                    logger.info(f"Template for {cve_id} needs refinement, queuing for processing")
                    templates_needing_refinement.append({
                        "cve_id": cve_id,
                        "template": template_content,
                        "validation_error": item.get("validation_error", "Unknown validation error")
                    })
                    # Store the template temporarily for refinement
                    try:
                        file_path.write_text(template_content)
                        logger.info(f"Stored template for refinement at {file_path}")
                    except IOError as e:
                        logger.error(f"Failed to store template for refinement {cve_id}: {e}")
                        continue
                else:
                    # Store valid template
                    if file_path.exists():
                        logger.info(f"Template for {cve_id} already exists, using existing file")
                    else:
                        try:
                            file_path.write_text(template_content)
                            logger.info(f"Stored new template at {file_path}")
                            redis_client.hincrby("pipeline_metrics", "templates_generated", 1)
                        except IOError as e:
                            logger.error(f"Failed to store template for {cve_id}: {e}")
                            continue
                            
                stored_templates.append({"cve_id": cve_id, "template_file": str(file_path)})
            
            # Queue refinement for templates that need it
            if templates_needing_refinement:
                self.queue_template_refinements(templates_needing_refinement)
                
            logger.info(f"Stored or reused {len(stored_templates)} templates")
            return stored_templates
            
        except Exception as e:
            logger.error(f"Error storing templates: {str(e)}", exc_info=True)
            return []

    def queue_template_refinements(self, templates_needing_refinement: List[Dict[str, str]]) -> None:
        """Queue templates that need refinement for processing"""
        try:
            from celery_tasks.tasks import refine_nuclei_template, store_refined_template, validate_template
            
            for template_info in templates_needing_refinement:
                cve_id = template_info["cve_id"]
                validation_error = template_info["validation_error"]
                
                # Create refinement chain
                refinement_chain = chain(
                    refine_nuclei_template.s(cve_id, validation_error),
                    store_refined_template.s(cve_id),
                    validate_template.s(cve_id, max_attempts=3, attempt=1)
                )
                refinement_chain.apply_async()
                logger.info(f"Queued refinement for template {cve_id}")
                
        except Exception as e:
            logger.error(f"Error queuing template refinements: {str(e)}", exc_info=True)

    def store_refined_template(self, cve_id: str, refined_template: str) -> Dict[str, str]:
        """Store refined template"""
        try:
            file_path = TEMPLATE_DIR / f"{cve_id}.yaml"
            
            # Clean the refined template
            cleaned_template = clean_yaml_content(refined_template)
            
            # Validate the refined template
            is_valid, error_msg = validate_yaml_structure(cleaned_template)
            
            if not is_valid:
                logger.warning(f"Refined template for {cve_id} still has issues: {error_msg}")
                # Store with error info for further refinement
                file_path.write_text(cleaned_template)
                logger.info(f"Stored refined template (with issues) for {cve_id} at {file_path}")
                return {
                    "cve_id": cve_id, 
                    "template_file": str(file_path),
                    "needs_refinement": True,
                    "validation_error": error_msg
                }
            
            # Store valid refined template
            file_path.write_text(cleaned_template)
            logger.info(f"Stored valid refined template for {cve_id} at {file_path}")
            redis_client.hincrby("pipeline_metrics", "templates_refined", 1)
            return {"cve_id": cve_id, "template_file": str(file_path)}
            
        except Exception as e:
            logger.error(f"Failed to store refined template for {cve_id}: {e}", exc_info=True)
            return {"cve_id": cve_id, "template_file": None}

    def validate_template(self, cve_id: str, template_file: str, max_attempts: int = 3, attempt: int = 1) -> Dict[str, Any]:
        """Validate template against vulnerable targets"""
        try:
            start_time = time.time()
            logger.info(f"Validating template {cve_id} (attempt {attempt}/{max_attempts})")
            
            # Get vulnerable hosts using the target management controller
            hosts = self.get_vulnerable_hosts(cve_id)
            global_metrics_key = "pipeline_metrics"
            cve_metrics_key = f"template_metrics:{cve_id}"
            
            if not redis_client.hexists(cve_metrics_key, "attempts"):
                redis_client.hset(cve_metrics_key, mapping={"attempts": 0, "refinements": 0, "validated": 0, "scan_success": 0, "no_result":0})
            
            if not hosts:
                redis_client.hincrby(cve_metrics_key, "attempts", 1)
                redis_client.hincrby(global_metrics_key, "failed_validations", 1)
                return {"status": "failed", "reason": "No vulnerable hosts found"}
            
            try:
                template_content = Path(template_file).read_text()
            except (IOError, TypeError) as e:
                logger.error(f"Failed to read template file {template_file} for {cve_id}: {e}", exc_info=True)
                redis_client.hincrby(cve_metrics_key, "attempts", 1)
                redis_client.hincrby(global_metrics_key, "failed_validations", 1)
                return {"status": "failed", "reason": f"Cannot read template file: {e}"}
            
            try:
                # Validate template using TemplateController
                validation_response = self.template_controller.validate_template_cel(template_file)
                if validation_response is not None:
                    redis_client.hincrby(cve_metrics_key, "attempts", 1)
                    redis_client.hincrby(global_metrics_key, "failed_validations", 1)
                    return {"status": "failed", "reason": validation_response}
                
                redis_client.hset(cve_metrics_key, "validated", 1)
                redis_client.hincrby(global_metrics_key, "templates_validated", 1)
                
                # Run scan using NucleiController
                scan_response = self.nuclei_controller.run_nuclei_scan(target=hosts[0], cve_id=cve_id)
                container_name = scan_response.get("container_name")
                
                if not container_name:
                    raise ValueError("No container_name in scan response")
                
                # Monitor container status
                from controllers.DockerController import DockerController
                docker_controller = DockerController()
                container_status = docker_controller.container_status(container_name)
                
                if container_status is None:
                    redis_client.hincrby(cve_metrics_key, "attempts", 1)
                    redis_client.hincrby(global_metrics_key, "failed_validations", 1)
                    return {"status": "failed", "reason": "Container not found"}
                
                # Wait for container to complete
                while container_status == "running":
                    time.sleep(30)
                    container_status = docker_controller.container_status(container_name)
                
                # Check logs for results
                logs = docker_controller.stream_container_logs(container_name)
                for line in logs:
                    if "[INF]" in line and "matched" in line:
                        logger.info(f"Validated template for {cve_id} on attempt {attempt}")
                        redis_client.hset(cve_metrics_key, "scan_success", 1)
                        redis_client.hincrby(cve_metrics_key, "attempts", 1)
                        redis_client.hincrby(global_metrics_key, "scan_successes", 1)
                        duration = time.time() - start_time
                        redis_client.hincrby(global_metrics_key, "total_validation_duration", int(duration * 1000))
                        record_template_validation(cve_id, "success")
                        return {"status": "success", "attempts": attempt}
                    
                    if "[INF]" in line and "No results found. Better luck next time!" in line:
                        logger.info(f"Did not find anything scanning:{cve_id}")
                        redis_client.hset(global_metrics_key, "no_result", 1)
                
                # If no match found, try refinement
                redis_client.hincrby(cve_metrics_key, "attempts", 1)
                if attempt < max_attempts:
                    from celery_tasks.tasks import refine_nuclei_template, store_refined_template, validate_template
                    refinement_chain = chain(
                        refine_nuclei_template.s(cve_id, "No vulnerabilities detected in validation scan", template_content),
                        store_refined_template.s(cve_id),
                        validate_template.s(cve_id, max_attempts=max_attempts, attempt=attempt + 1)
                    )
                    refinement_chain.apply_async()
                    logger.info(f"Queued refinement and retry for {cve_id} on attempt {attempt}")
                    redis_client.hincrby(cve_metrics_key, "refinements", 1)
                    redis_client.hincrby(global_metrics_key, "refinements", 1)
                    return {"status": "pending", "reason": "Refinement and retry queued"}
                else:
                    logger.info(f"Validation failed for {cve_id} after {max_attempts} attempts")
                    redis_client.hincrby(global_metrics_key, "failed_validations", 1)
                    duration = time.time() - start_time
                    redis_client.hincrby(global_metrics_key, "total_validation_duration", int(duration * 1000))
                    record_template_validation(cve_id, "failed")
                    return {"status": "failed", "reason": "No vulnerabilities detected"}
                    
            except Exception as e:
                logger.error(f"Validation failed for {cve_id}: {e}", exc_info=True)
                redis_client.hincrby(cve_metrics_key, "attempts", 1)
                if attempt < max_attempts:
                    from celery_tasks.tasks import refine_nuclei_template, store_refined_template, validate_template
                    refinement_chain = chain(
                        refine_nuclei_template.s(cve_id, str(e), template_content),
                        store_refined_template.s(cve_id),
                        validate_template.s(cve_id, max_attempts=max_attempts, attempt=attempt + 1)
                    )
                    refinement_chain.apply_async()
                    logger.info(f"Queued refinement and retry for {cve_id} due to error on attempt {attempt}")
                    redis_client.hincrby(cve_metrics_key, "refinements", 1)
                    redis_client.hincrby(global_metrics_key, "refinements", 1)
                    return {"status": "pending", "reason": "Refinement and retry queued"}
                else:
                    logger.info(f"Validation failed for {cve_id} after {max_attempts} attempts")
                    redis_client.hincrby(global_metrics_key, "failed_validations", 1)
                    duration = time.time() - start_time
                    redis_client.hincrby(global_metrics_key, "total_validation_duration", int(duration * 1000))
                    record_template_validation(cve_id, "failed")
                    return {"status": "failed", "reason": "Max attempts reached"}
                    
        except Exception as e:
            logger.error(f"Error validating template for {cve_id}: {str(e)}", exc_info=True)
            return {"status": "failed", "reason": f"Internal error: {str(e)}"}

    def validate_templates_callback(self, templates: List[Dict[str, str]]) -> None:
        """Callback to validate templates after generation"""
        try:
            if not templates:
                logger.error("No templates to validate")
                return
            from celery_tasks.tasks import validate_template
            validation_group = [validate_template.s(t["cve_id"], t["template_file"]) for t in templates]
            group(validation_group).apply_async()
            logger.info(f"Queued validation for {len(templates)} templates")
        except Exception as e:
            logger.error(f"Error in validate_templates_callback: {str(e)}", exc_info=True)

    def generate_templates(self) -> None:
        """Generate templates from vulnerability data"""
        try:
            from celery_tasks.tasks import fetch_vulnerabilities, process_vulnerabilities, generate_nuclei_templates
            logger.info("Starting template generation pipeline")
            workflow = chain(
                fetch_vulnerabilities.s(),
                process_vulnerabilities.s(),
                generate_nuclei_templates.s(),
            )
            workflow.apply_async()
            logger.info("Template generation and validation pipeline queued")
        except Exception as e:
            logger.error(f"Error generating templates pipeline: {str(e)}", exc_info=True)

    def get_vulnerable_hosts(self, cve_id: str) -> List[str]:
        """Get vulnerable hosts for template testing using TargetManagementController"""
        try:
            # Use the target management controller to get targets suitable for testing
            targets = self.target_management_controller.get_targets_for_testing(limit=5)
            
            # Extract host information from targets
            hosts = []
            for target in targets:
                if target.get("ip"):
                    hosts.append(target["ip"])
                elif target.get("domain"):
                    hosts.append(target["domain"])
            
            # Fallback to mock hosts if no targets found
            if not hosts:
                mock_hosts = {
                    "CVE-2021-1234": ["example.com", "test.vuln"],
                    "CVE-2022-5678": ["vuln.host"]
                }
                hosts = mock_hosts.get(cve_id, ["honey.scanme.sh"])
            
            return hosts
            
        except Exception as e:
            logger.error(f"Error getting vulnerable hosts for {cve_id}: {e}")
            return ["honey.scanme.sh"]  # Fallback

    def upload_template(self, content: bytes, filename: str):
        """Upload template file"""
        try:
            save_path = f"{conf.nuclei_upload_template_path}/{filename}"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(content)
            return None
        except Exception as e:
            logger.error(f"Failed to upload template {filename}: {str(e)}", exc_info=True)
            return f"Failed to upload template: {str(e)}"

    # Helper methods for refinement tracking
    def _track_refinement_step(self, cve_id: str, step: str, data: Dict[str, Any]):
        """Track refinement step for debugging"""
        try:
            step_key = f"refinement:{cve_id}:{step}"
            redis_client.setex(step_key, 3600, json.dumps({
                "timestamp": time.time(),
                "step": step,
                "data": data
            }))
        except Exception as e:
            logger.warning(f"Failed to track refinement step: {e}")

    def _track_refinement_failure(self, cve_id: str, attempt: int, error: str, duration: float):
        """Track refinement failure"""
        try:
            failure_key = f"refinement_failure:{cve_id}"
            redis_client.setex(failure_key, 3600, json.dumps({
                "timestamp": time.time(),
                "attempt": attempt,
                "error": error,
                "duration": duration
            }))
        except Exception as e:
            logger.warning(f"Failed to track refinement failure: {e}")
