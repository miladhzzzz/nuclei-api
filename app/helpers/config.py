import os
from urllib.parse import urlparse
from dotenv import load_dotenv

# config class for reading env file and turning it to an object
load_dotenv()

class Config():

    def __init__(self) -> None:
        self.nuclei_upload_template_path = os.getenv("NUCLEI_CUSTOM_TEMPLATE_UPLOAD_PATH", "/root/nuclei-templates/custom")
        self.nuclei_template_path = os.getenv("NUCLEI_TEMPLATE_PATH", "/root/nuclei-templates")
        self.nuclei_image = os.getenv("NUCLEI_IMAGE", "projectdiscovery/nuclei:latest")
        self.nuclei_container_template_path = os.getenv("NUCLEI_CONTAINER_TEMPLATE_PATH", "/root/nuclei-templates")
        self.template_dir = os.getenv("TEMPLATE_DIR", "/app/templates")

        self.app_port = int(os.getenv("APP_PORT", "8080"))
        self.app_host = os.getenv("APP_HOST", "0.0.0.0")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.app_title = os.getenv("APP_TITLE", "Nuclei API")
        self.app_description = os.getenv("APP_DESCRIPTION", "API for running Nuclei scans using Docker.")
        self.app_version = os.getenv("APP_VERSION", "0.1.1")
        openapi_raw = os.getenv("APP_OPENAPI_URL", "/openapi.json")
        self.app_openapi_url = None if openapi_raw.strip().lower() in {"none", "null", ""} else openapi_raw
        self.app_debug = os.getenv("APP_DEBUG", "false").strip().lower() in {"1", "true", "yes", "on"}

        self.sentry_dsn = os.getenv("SENTRY_DSN")
        self.sentry_traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "1.0"))
        self.env = os.getenv("ENVIRONMENT", "local")
        self.release = os.getenv("RELEASE", "0.1.1")

        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        parsed_redis = urlparse(self.redis_url)
        self.redis_host = parsed_redis.hostname or "redis"
        self.redis_port = parsed_redis.port or 6379
        self.redis_db = int((parsed_redis.path or "/0").lstrip("/") or "0")

        self.llm_model = os.getenv("LLM_MODEL", "deepseek-coder:1.3b")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434/api/generate")
        self.ollama_timeout = int(os.getenv("OLLAMA_TIMEOUT", "2000"))

        self.fingerprint_url = os.getenv("FINGERPRINT_URL", "http://nuclei-fingerprint:3000/")
        self.fingerprint_quick_scan_type = os.getenv("FINGERPRINT_QUICK_SCAN_TYPE", "quickOsAndPorts")
        self.fingerprint_aggressive_scan_type = os.getenv("FINGERPRINT_AGGRESSIVE_SCAN_TYPE", "aggressiveOsAndPort")
        self.fingerprint_quick_timeout = int(os.getenv("FINGERPRINT_QUICK_TIMEOUT", "2000"))
        self.fingerprint_aggressive_timeout = int(os.getenv("FINGERPRINT_AGGRESSIVE_TIMEOUT", "3000"))

        self.shodan_api_key = os.getenv("SHODAN_API_KEY")
