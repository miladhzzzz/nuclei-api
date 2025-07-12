import datetime
import os
import requests
import logging
import time
import redis
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from celery.result import GroupResult
from celery import chain, group ,chord
from celery_config import celery_app
from helpers import config
from controllers.DockerController import DockerController
from controllers.FingerprintController import FingerprintController
from controllers.NucleiController import NucleiController
from controllers.TemplateController import TemplateController

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize Redis with environment variables for security
redis_client = redis.Redis(
    host="redis",
    port=6379,
    db=0,
    decode_responses=True  # Simplify JSON handling
)

OLLAMA_URL_DEFAULT = "http://ollama:11434/api/generate"
OLLAMA_TIMEOUT = 2000  # seconds
TEMPLATE_DIR = Path("/app/templates")

# Controllers
fingerprint_controller = FingerprintController()
docker_controller = DockerController()
nuclei_controller = NucleiController()
template_controller = TemplateController()
conf = config.Config()

# Load prompt template
try:
    with open(os.path.join(os.path.dirname(__file__), "template.txt"), "r") as f:
        PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    logger.error("Prompt template file not found")
    PROMPT_TEMPLATE = "Generate a Nuclei template for {cve_id} with description: {description}"

def get_last_seven_days_range() -> Tuple[str, str]:
    """
    Returns a tuple of (start_date, end_date) strings for the last 7 days in ISO 8601 format.
    """
    current_date = datetime.datetime.utcnow()
    end_date = current_date - datetime.timedelta(days=1)  # Yesterday
    start_date = end_date - datetime.timedelta(days=6)    # 7 days total
    return (
        start_date.strftime("%Y-%m-%dT00:00:00Z"),
        end_date.strftime("%Y-%m-%dT00:00:00Z")
    )


@celery_app.task
def refine_nuclei_template(cve_id: str, template: str, error: Optional[str] = None) -> str:
    """Refine an existing Nuclei template based on error or improvement needs."""
    logger.info(f"Starting template refinement for {cve_id}")
    prompt = (
        f"Fix this template for {cve_id} that caused error '{error}':\n{template}"
        if error else f"Refine this template for {cve_id} to improve detection:\n{template}"
    )
    ollama_url = conf.ollama_url or OLLAMA_URL_DEFAULT
    payload = {"model": conf.llm_model, "prompt": prompt, "stream": False}
    try:
        response = requests.post(ollama_url, json=payload, timeout=OLLAMA_TIMEOUT)
        response.raise_for_status()
        refined_template = response.json().get("response", "")
        if refined_template:
            logger.info(f"Refined template for {cve_id}")
            return refined_template
        logger.warning(f"No refined template generated for {cve_id}")
        return template  # Return original if refinement fails
    except requests.RequestException as e:
        logger.error(f"Failed to refine template for {cve_id}: {e}")
        return template  # Return original on failure

@celery_app.task(bind=True, max_retries=3)
def fetch_vulnerabilities(self) -> List[Dict[str, Any]]:
    """
    Fetch vulnerabilities from multiple sources and cache in Redis for 12 hours.
    Uses exponential backoff for retries.
    """
    cache_key = "all_vulnerabilities"
    cached = redis_client.get(cache_key)
    if cached:
        logger.info("Using cached vulnerabilities")
        return json.loads(cached)

    start_date, end_date = get_last_seven_days_range()
    sources = [
        {
            "name": "NVD",
            "url": "https://services.nvd.nist.gov/rest/json/cves/2.0",
            "params": {"resultsPerPage": 500, "cvssV3Severity": "HIGH", "pubStartDate": start_date, "pubEndDate": end_date}
        },
        {
            "name": "CISA KEV",
            "url": "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
        },
        {
            "name": "Red Hat",
            "url": "https://access.redhat.com/hydra/rest/securitydata/cve.json",
            "params": {"per_page": 100, "severity": "important"}
        }
    ]
    all_vulns = []
    for source in sources:
        try:
            params = source.get("params", {})
            response = requests.get(source["url"], params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            vulns = (
                data.get("vulnerabilities", []) if source["name"] in ["NVD", "CISA KEV"] else
                data if source["name"] == "Red Hat" and isinstance(data, list) else []
            )
            all_vulns.extend(vulns)
            logger.info(f"Fetched {len(vulns)} vulnerabilities from {source['name']}")
        except requests.RequestException as e:
            logger.error(f"Failed to fetch from {source['name']}: {str(e)}")
            if self.request.retries < self.max_retries:
                delay = 2 ** self.request.retries  # Exponential backoff
                raise self.retry(countdown=delay)

    unique_vulns = list({v.get("cve", {}).get("id", v.get("id")): v for v in all_vulns if isinstance(v, dict)}.values())
    redis_client.setex(cache_key, 43200, json.dumps(unique_vulns))
    logger.info(f"Cached {len(unique_vulns)} unique vulnerabilities")
    return unique_vulns

@celery_app.task
def process_vulnerabilities(vuln_data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Process vulnerabilities into prompts for template generation.
    """
    processed = []
    for vuln in vuln_data:
        cve_id = vuln.get("cve", {}).get("id", vuln.get("id", "Unknown"))
        description = (
            vuln["cve"]["descriptions"][0]["value"]
            if "cve" in vuln and "descriptions" in vuln["cve"] else
            vuln.get("description", "No description")
        )
        prompt = PROMPT_TEMPLATE.format(cve_id=cve_id, description=description)
        processed.append({"cve_id": cve_id, "prompt": prompt})
    logger.info(f"Processed {len(processed)} vulnerabilities")
    return processed

@celery_app.task
def generate_nuclei_template(cve_id: str, prompt: str) -> Optional[Dict[str, str]]:
    """Generate a single Nuclei template for a given CVE."""

    file_path = TEMPLATE_DIR / f"{cve_id}.yaml"
    if file_path.exists():
        logger.info(f"Template for {cve_id} already exists, skipping generation")
        return {"cve_id": cve_id, "template": file_path.read_text()}
    
    logger.info(f"Starting template generation for {cve_id}")
    ollama_url = conf.ollama_url or OLLAMA_URL_DEFAULT
    payload = {"model": conf.llm_model, "prompt": prompt, "stream": False}
    try:
        response = requests.post(ollama_url, json=payload, timeout=OLLAMA_TIMEOUT)
        response.raise_for_status()
        template = response.json().get("response", "")
        if template:
            logger.info(f"Generated template for {cve_id}")
            return {"cve_id": cve_id, "template": template}
        logger.warning(f"No template generated for {cve_id}")
        return None
    except requests.RequestException as e:
        logger.error(f"Failed to generate template for {cve_id}: {e}")
        return None

@celery_app.task
def generate_nuclei_templates(processed_data: List[Dict[str, str]]) -> None:
    """Queue template generation tasks for all vulnerabilities."""
    logger.info(f"Starting template generation for {len(processed_data)} vulnerabilities")
    if not processed_data:
        logger.warning("No vulnerabilities to process")
        return None

    # Create a group of template generation tasks
    job = group(generate_nuclei_template.s(item["cve_id"], item["prompt"]) for item in processed_data)
    # Use a chord to link the group to a callback chain
    chord(job)(chain(store_templates.s(), validate_templates_callback.s()))
    logger.info(f"Queued {len(processed_data)} template generation tasks with chord callback")

@celery_app.task
def store_templates(templates: List[Optional[Dict[str, str]]]) -> List[Dict[str, str]]:
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    stored_templates = []
    for item in templates:
        if not item or not item.get("template"):
            logger.warning(f"Skipping empty or invalid template: {item}")
            continue
        file_path = TEMPLATE_DIR / f"{item['cve_id']}.yaml"
        cleaned_template = item["template"].strip()
        if cleaned_template.startswith("```yaml"):
            cleaned_template = cleaned_template[len("```yaml"):].strip()
        if cleaned_template.endswith("```"):
            cleaned_template = cleaned_template[:-len("```")].strip()

        if file_path.exists():
            logger.info(f"Template for {item['cve_id']} already exists, using existing file")
        else:
            try:
                file_path.write_text(cleaned_template)
                logger.info(f"Stored new template at {file_path}")
                redis_client.hincrby("pipeline_metrics", "templates_generated", 1)  # Count new templates
            except IOError as e:
                logger.error(f"Failed to store template for {item['cve_id']}: {e}")
                continue
        stored_templates.append({"cve_id": item["cve_id"], "template_file": str(file_path)})
    logger.info(f"Stored or reused {len(stored_templates)} templates")
    return stored_templates

def get_vulnerable_hosts(cve_id: str) -> List[str]:
    """
    Placeholder to fetch known vulnerable hosts for a CVE.
    In practice, this could query a database or external service.
    """
    # Mock implementation; replace with real logic
    mock_hosts = {
        "CVE-2021-1234": ["example.com", "test.vuln"],
        "CVE-2022-5678": ["vuln.host"]
    }
    return mock_hosts.get(cve_id, default=["honey.scanme.sh"])

@celery_app.task
def store_refined_template(cve_id: str, refined_template: str) -> Dict[str, str]:
    file_path = TEMPLATE_DIR / f"{cve_id}.yaml"
    cleaned_template = refined_template.strip()
    if cleaned_template.startswith("```yaml"):
        cleaned_template = cleaned_template[len("```yaml"):].strip()
    if cleaned_template.endswith("```"):
        cleaned_template = cleaned_template[:-len("```")].strip()

    try:
        file_path.write_text(cleaned_template)
        logger.info(f"Stored refined template for {cve_id} at {file_path}")
        return {"cve_id": cve_id, "template_file": str(file_path)}
    except IOError as e:
        logger.error(f"Failed to store refined template for {cve_id}: {e}")
        return {"cve_id": cve_id, "template_file": None}  # Handle error gracefully

@celery_app.task
def validate_template(cve_id: str, template_file: str, max_attempts: int = 3, attempt: int = 1) -> Dict[str, Any]:
    """Validate a Nuclei template against known vulnerable hosts, refining asynchronously if needed, with metrics tracking."""
    logger.info(f"Validating template for {cve_id}, attempt {attempt}")
    start_time = time.time()  # For optional duration tracking
    hosts = get_vulnerable_hosts(cve_id)
    
    # Redis keys
    global_metrics_key = "pipeline_metrics"
    cve_metrics_key = f"template_metrics:{cve_id}"

    # Initialize CVE metrics if not present
    if not redis_client.hexists(cve_metrics_key, "attempts"):
        redis_client.hset(cve_metrics_key, mapping={"attempts": 0, "refinements": 0, "validated": 0, "scan_success": 0, "no_result":0})

    if not hosts:
        redis_client.hincrby(cve_metrics_key, "attempts", 1)
        redis_client.hincrby(global_metrics_key, "failed_validations", 1)
        return {"status": "failed", "reason": "No vulnerable hosts found"}

    # Read template content for refinement
    try:
        template_content = Path(template_file).read_text()
    except (IOError, TypeError) as e:
        logger.error(f"Failed to read template file {template_file} for {cve_id}: {e}")
        redis_client.hincrby(cve_metrics_key, "attempts", 1)
        redis_client.hincrby(global_metrics_key, "failed_validations", 1)
        return {"status": "failed", "reason": f"Cannot read template file: {e}"}

    try:
        # Validate template syntax
        validation_response = template_controller.validate_template_cel(template_file)
        if validation_response is not None:
            redis_client.hincrby(cve_metrics_key, "attempts", 1)
            redis_client.hincrby(global_metrics_key, "failed_validations", 1)
            return {"status": "failed", "reason": validation_response}
        
        # Mark as validated if syntax check passes
        redis_client.hset(cve_metrics_key, "validated", 1)
        redis_client.hincrby(global_metrics_key, "templates_validated", 1)

        # Run Nuclei scan
        scan_response = nuclei_controller.run_nuclei_scan(target=hosts[0], cve_id=cve_id)
        container_name = scan_response.get("container_name")
        if not container_name:
            raise ValueError("No container_name in scan response")

        container_status = docker_controller.container_status(container_name)
        if container_status is None:
            redis_client.hincrby(cve_metrics_key, "attempts", 1)
            redis_client.hincrby(global_metrics_key, "failed_validations", 1)
            return {"status": "failed", "reason": "Container not found"}

        while container_status == "running":
            time.sleep(30)
            container_status = docker_controller.container_status(container_name)

        logs = docker_controller.stream_container_logs(container_name)
        for line in logs:
            if "[INF]" in line and "matched" in line:
                logger.info(f"Validated template for {cve_id} on attempt {attempt}")
                redis_client.hset(cve_metrics_key, "scan_success", 1)
                redis_client.hincrby(cve_metrics_key, "attempts", 1)
                redis_client.hincrby(global_metrics_key, "scan_successes", 1)
                duration = time.time() - start_time
                redis_client.hincrby(global_metrics_key, "total_validation_duration", int(duration * 1000))  # ms
                return {"status": "success", "attempts": attempt}
            # Scan did not find anything
            if "[INF]" in line and "No results found. Better luck next time!" in line:
                logger.info(f"Did not find anything scanning:{cve_id}")
                redis_client.hset(global_metrics_key, "no_result", 1)

        # No match found
        redis_client.hincrby(cve_metrics_key, "attempts", 1)
        if attempt < max_attempts:
            refinement_chain = chain(
                refine_nuclei_template.s(cve_id, template_content),
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
            redis_client.hincrby(global_metrics_key, "total_validation_duration", int(duration * 1000))  # ms
            return {"status": "failed", "reason": "No vulnerabilities detected"}

    except Exception as e:
        logger.error(f"Validation failed for {cve_id}: {e}")
        redis_client.hincrby(cve_metrics_key, "attempts", 1)
        if attempt < max_attempts:
            refinement_chain = chain(
                refine_nuclei_template.s(cve_id, template_content, str(e)),
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
            redis_client.hincrby(global_metrics_key, "total_validation_duration", int(duration * 1000))  # ms
            return {"status": "failed", "reason": "Max attempts reached"}

@celery_app.task
def fingerprint_target(ip_address: str) -> Optional[str]:
    """
    Fingerprint an IP address to detect the OS.
    """
    try:
        response = fingerprint_controller.fingerprint_target(ip_address)
        os_name = response if isinstance(response, str) else response.get("os")
        if not os_name:
            logger.warning(f"No OS detected for {ip_address}")
            return None
        logger.info(f"Detected OS for {ip_address}: {os_name}")
        return os_name
    except Exception as e:
        logger.error(f"Fingerprinting failed for {ip_address}: {str(e)}")
        return None

@celery_app.task
def run_nuclei_scan(os_name: Optional[str], target: str, templates: Optional[List[str]] = None, template_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Run a Nuclei scan with OS-specific or default templates.
    """
    try:
        os_tag_map = {"Linux": "linux", "Windows": "windows", "macOS": "macos"}
        template = templates or (template_file and [template_file]) or (
            [f"{os_tag_map[os_name]}/"] if os_name in os_tag_map else ["http/"]
        )
        result = nuclei_controller.run_nuclei_scan(target=target, template=template)
        logger.info(f"Nuclei scan completed for {target}")
        return result
    except Exception as e:
        logger.error(f"Nuclei scan failed for {target}: {str(e)}")
        raise

@celery_app.task
def validate_templates_callback(templates: List[Dict[str, str]]) -> None:
    if not templates:
        logger.error("No templates to validate")
        return
    validation_group = group(
        validate_template.s(t["cve_id"], t["template_file"]) for t in templates
    )
    validation_group.apply_async()
    logger.info(f"Queued validation for {len(templates)} templates")

@celery_app.task
def generate_templates() -> None:
    """
    Orchestrate the template generation and validation pipeline asynchronously.
    """
    logger.info("Starting template generation pipeline")
    workflow = chain(
        fetch_vulnerabilities.s(),
        process_vulnerabilities.s(),
        generate_nuclei_templates.s(),
        #store_templates.s(),
        #validate_templates_callback.s()
    )
    workflow.apply_async()
    logger.info("Template generation and validation pipeline queued")

@celery_app.task
def fingerprint_scan_pipeline(target: str, templates: Optional[List[str]] = None, template_file: Optional[str] = None) -> Any:
    """
    Chain fingerprinting and scanning tasks.
    """
    logger.info(f"Starting scan pipeline for {target}")

    task_chain = chain(
        fingerprint_target.s(target),
        run_nuclei_scan.s(target=target, templates=templates, template_file=template_file)
    )
    return task_chain.apply_async()

@celery_app.task
def ai_scan_pipeline(target: str, prompt: Optional[str] = None) -> Any:
    """
    Chain fingerprinting and scanning tasks.
    """
    logger.info(f"Starting scan pipeline for {target}")

    task_chain = chain(
        fingerprint_target.s(target),
        generate_nuclei_template.s(None, prompt),
        run_nuclei_scan.s(target=target),
    )
    return task_chain.apply_async()