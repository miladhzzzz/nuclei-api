import datetime
import os
import logging
import redis
import yaml
from pathlib import Path
from typing import List, Dict, Tuple, Any
from celery_config import celery_app
from helpers import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

conf = config.Config()
redis_client = redis.Redis(
    host="redis",
    port=6379,
    db=0,
    decode_responses=True
)
TEMPLATE_DIR = Path("/app/templates")
OLLAMA_URL_DEFAULT = "http://ollama:11434/api/generate"
OLLAMA_TIMEOUT = 2000

try:
    with open(os.path.join(os.path.dirname(__file__), "../celery_tasks/template.txt"), "r") as f:
        PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    logger.error("Prompt template file not found")
    PROMPT_TEMPLATE = "Generate a Nuclei template for {cve_id} with description: {description}"

def get_last_seven_days_range() -> Tuple[str, str]:
    current_date = datetime.datetime.utcnow()
    end_date = current_date - datetime.timedelta(days=1)
    start_date = end_date - datetime.timedelta(days=6)
    return (
        start_date.strftime("%Y-%m-%dT00:00:00Z"),
        end_date.strftime("%Y-%m-%dT00:00:00Z")
    )

def clean_yaml_content(raw_content: str) -> str:
    """
    Clean and extract YAML content from LLM response.
    
    Args:
        raw_content: Raw response from LLM
        
    Returns:
        Cleaned YAML content
    """
    try:
        # Remove markdown code blocks
        content = raw_content.strip()
        
        # Remove ```yaml and ``` markers
        if content.startswith("```yaml"):
            content = content[7:].strip()
        elif content.startswith("```"):
            content = content[3:].strip()
            
        if content.endswith("```"):
            content = content[:-3].strip()
            
        # Remove any leading/trailing whitespace
        content = content.strip()
        
        # Basic YAML validation
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            logger.warning(f"YAML validation failed: {e}")
            # Try to fix common issues
            content = fix_common_yaml_issues(content)
            
        return content
        
    except Exception as e:
        logger.error(f"Error cleaning YAML content: {e}")
        return raw_content

def fix_common_yaml_issues(content: str) -> str:
    """
    Fix common YAML formatting issues.
    
    Args:
        content: Raw YAML content
        
    Returns:
        Fixed YAML content
    """
    try:
        # Fix common issues
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Remove comments that might cause issues
            if '#' in line and not line.strip().startswith('#'):
                line = line.split('#')[0].rstrip()
            
            # Fix common indentation issues
            if line.strip() and not line.startswith(' '):
                # Add proper indentation for list items
                if line.strip().startswith('-'):
                    line = '  ' + line
                    
            fixed_lines.append(line)
            
        return '\n'.join(fixed_lines)
        
    except Exception as e:
        logger.error(f"Error fixing YAML issues: {e}")
        return content

def validate_yaml_structure(content: str) -> Tuple[bool, str]:
    """
    Validate YAML structure and basic Nuclei template requirements.
    
    Args:
        content: YAML content to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Parse YAML
        data = yaml.safe_load(content)
        
        if not isinstance(data, dict):
            return False, "Template must be a YAML object"
            
        # Check required fields
        if 'id' not in data:
            return False, "Template must have an 'id' field"
            
        if 'info' not in data:
            return False, "Template must have an 'info' field"
            
        if 'requests' not in data:
            return False, "Template must have a 'requests' field"
            
        # Validate info section
        info = data.get('info', {})
        if not isinstance(info, dict):
            return False, "Info section must be an object"
            
        # Validate requests section
        requests = data.get('requests', [])
        if not isinstance(requests, list):
            return False, "Requests section must be a list"
            
        if not requests:
            return False, "Requests section cannot be empty"
            
        return True, ""
        
    except yaml.YAMLError as e:
        return False, f"Invalid YAML: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"


