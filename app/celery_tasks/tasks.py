import datetime , os , requests , logging , time, redis , json
from herlpers import config
from controllers.FingerprintController import FingerprintController
from celery_config import celery_app
from celery import chain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_client = redis.Redis(host='redis', port=6379, db=0)

fingerprint_controller = FingerprintController()
conf = config.Config()

def get_last_seven_days_range():
    """
    Returns a tuple of (start_date, end_date) strings for the last 7 days
    in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
    """
    current_date = datetime.datetime.now()
    end_date = current_date - datetime.timedelta(days=1)  # Yesterday
    start_date = end_date - datetime.timedelta(days=6)    # 7 days total including end date
    
    start_date_str = start_date.strftime("%Y-%m-%dT00:00:00")
    end_date_str = end_date.strftime("%Y-%m-%dT00:00:00")
    
    return start_date_str, end_date_str

# Load prompt template from file
with open(os.path.join(os.path.dirname(__file__), "template.txt"), "r") as f:
    PROMPT_TEMPLATE = f.read()

@celery_app.task
def fetch_vulnerabilities():
    cache_key = "nvd_high_severity_cves"
    cached = redis_client.get(cache_key)
    if cached:
        logger.info("Retrieved cached high-severity CVEs from Redis")
        return json.loads(cached)
    
    # Get the date range from helper function
    start_date, end_date = get_last_seven_days_range()

    base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    params = {
        "resultsPerPage": 10,
        "cvssV3Severity": "HIGH",
        "pubStartDate": start_date,
        "pubEndDate": end_date,
    }
    logger.info(f"Fetching high-severity CVEs from NVD with params: {params}")
    for attempt in range(3):
        try:
            response = requests.get(base_url, params=params, timeout=60)
            response.raise_for_status()
            vulns = response.json().get("vulnerabilities", [])
            logger.info(f"Fetched {len(vulns)} high-severity CVEs from NVD")
            redis_client.setex(cache_key, 3600, json.dumps(vulns))
            return vulns
        except requests.exceptions.RequestException as e:
            logger.error(f"Attempt {attempt + 1} Failed to fetch vulnerabilities from NVD: {str(e)}")
            if attempt == 2:
                    logger.error(f"Max retries reached to fetch vulnerabilities from NVD")
            raise

@celery_app.task
def process_vulnerabilities(vuln_data):
    processed = []
    for vuln in vuln_data:
        cve_id = vuln["cve"]["id"]
        description = vuln["cve"]["descriptions"][0]["value"]
        prompt = PROMPT_TEMPLATE.format(cve_id=cve_id, description=description)
        processed.append({"cve_id": cve_id, "prompt": prompt})
    logger.info(f"Processed {len(processed)} vulnerabilities into prompts")
    return processed

@celery_app.task
def generate_nuclei_templates(processed_data):
    templates = []
    ollama_url = "http://ollama:11434/api/generate"
    logger.info(f"LLM Model: {conf.llm_model}")
    
    for item in processed_data:
        payload = {
            "model": conf.llm_model,
            "prompt": item["prompt"],
            "stream": False
        }
        logger.info(f"Sending prompt for {item['cve_id']}: {item['prompt']}")
        for attempt in range(3):
            try:
                response = requests.post(ollama_url, json=payload, timeout=200)
                response.raise_for_status()
                response_data = response.json()
                template = response_data.get("response", "")
                eval_tokens = response_data.get("eval_count", 0)
                logger.info(f"Generated template for {item['cve_id']}: {template[:50]}... (Tokens: {eval_tokens})")
                if template:
                    templates.append({"cve_id": item["cve_id"], "template": template})
                else:
                    logger.warning(f"No template content for {item['cve_id']}")
                break
            except requests.exceptions.RequestException as e:
                logger.error(f"Attempt {attempt + 1} failed for {item['cve_id']}: {str(e)}")
                if attempt == 2:
                    logger.error(f"Max retries reached for {item['cve_id']}")
                time.sleep(5)
        time.sleep(2)
    logger.info(f"Generated {len(templates)} templates")
    return templates

@celery_app.task
def store_templates(templates):
    template_dir = "/app/templates"
    logger.info(f"Storing {len(templates)} templates in {template_dir}")
    try:
        os.makedirs(template_dir, exist_ok=True)
        for item in templates:
            if not item.get("template"):
                logger.warning(f"No template content for {item['cve_id']}, skipping")
                continue
            file_path = os.path.join(template_dir, f"{item['cve_id']}.yaml")
            with open(file_path, "w") as f:
                f.write(item["template"])
            logger.info(f"Wrote template to {file_path}")
    except Exception as e:
        logger.error(f"Error storing templates: {str(e)}")
        raise

@celery_app.task
def fingerprint_target(ip_address):
    """Fingerprint the target IP using an Nmap-based service to detect the OS."""
    try:
        response = fingerprint_controller.fingerprint_target(ip_address)
        if not response:
            raise ValueError("OS not detected")
        logger.info(f"Fingerprinting completed for {ip_address}: {response}")
        return response
    except requests.RequestException as e:
        logger.error(f"Fingerprinting failed for {ip_address}: {str(e)}")
        raise

@celery_app.task
def generate_templates():
    logger.info("Starting generate_templates pipeline")
    # Chain tasks asynchronously
    workflow = chain(
        fetch_vulnerabilities.s(),
        process_vulnerabilities.s(),
        generate_nuclei_templates.s(),
        store_templates.s()
    )
    workflow.apply_async()
    logger.info("Generate_templates pipeline queued")

@celery_app.task
def scan_pipeline(ip_address):
    logger.info("Starting Fingerprint the target")
    """Chain the fingerprinting, workflow generation, and scanning tasks."""
    task_chain = chain (
        fingerprint_target.s(ip_address),
        # generate_workflow.s(),
        # run_nuclei_scan.s(ip_address),
    )
    return task_chain.apply_async()