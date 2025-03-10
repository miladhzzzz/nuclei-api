import redis, json , logging
from typing import Optional , Dict , Any
from pathlib import Path
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi import APIRouter, HTTPException, Request

# Configure logging (consistent with tasks.py)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

router = APIRouter()
TEMPLATE_DIR = Path("/app/templates")

# Redis client (same config as tasks.py)
redis_client = redis.Redis(
    host="redis",
    port=6379,
    db=0,
    decode_responses=True
)

@router.get("/metrics", response_model=Dict[str, Any])
async def get_pipeline_metrics():
    """
    Fetch global pipeline metrics.
    Returns counts of templates generated, validated, scan successes, refinements, failures, and average duration.
    """
    try:
        metrics = redis_client.hgetall("pipeline_metrics")
        if not metrics:
            return {
                "templates_generated": 0,
                "templates_validated": 0,
                "scan_successes": 0,
                "refinements": 0,
                "failed_validations": 0,
                "average_validation_duration_ms": 0.0
            }

        # Convert string values to integers and calculate average duration
        templates_validated = int(metrics.get("templates_validated", 0))
        total_duration = int(metrics.get("total_validation_duration", 0))  # in ms
        avg_duration = total_duration / max(templates_validated, 1) if total_duration > 0 else 0.0

        response = {
            "templates_generated": int(metrics.get("templates_generated", 0)),
            "templates_validated": templates_validated,
            "scan_successes": int(metrics.get("scan_successes", 0)),
            "refinements": int(metrics.get("refinements", 0)),
            "failed_validations": int(metrics.get("failed_validations", 0)),
            "average_validation_duration_ms": round(avg_duration, 2)
        }
        logger.info("Fetched pipeline metrics")
        return response
    except redis.RedisError as e:
        logger.error(f"Failed to fetch pipeline metrics from Redis: {e}")
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")

@router.get("/metrics/template/{cve_id}", response_model=Dict[str, Any])
async def get_template_metrics(cve_id: str):
    """
    Fetch metrics for a specific CVE template.
    Returns attempts, refinements, validation status, and scan success status.
    """
    cve_metrics_key = f"template_metrics:{cve_id}"
    try:
        metrics = redis_client.hgetall(cve_metrics_key)
        if not metrics:
            # Check if template exists on disk as a fallback
            template_file = TEMPLATE_DIR / f"{cve_id}.yaml"
            if template_file.exists():
                response = {
                    "cve_id": cve_id,
                    "attempts": 0,
                    "refinements": 0,
                    "validated": False,
                    "scan_success": False,
                    "template_exists": True
                }
            else:
                raise HTTPException(status_code=404, detail=f"No metrics or template found for {cve_id}")
        else:
            response = {
                "cve_id": cve_id,
                "attempts": int(metrics.get("attempts", 0)),
                "refinements": int(metrics.get("refinements", 0)),
                "validated": bool(int(metrics.get("validated", 0))),
                "scan_success": bool(int(metrics.get("scan_success", 0))),
                "template_exists": (TEMPLATE_DIR / f"{cve_id}.yaml").exists()
            }
        logger.info(f"Fetched metrics for {cve_id}")
        return response
    except redis.RedisError as e:
        logger.error(f"Failed to fetch metrics for {cve_id} from Redis: {e}")
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")

@router.get("/metrics/templates", response_model=Dict[str, Any])
async def get_all_template_metrics():
    """
    Fetch aggregated metrics for all templates.
    Returns total counts and lists of successful/failed templates.
    """
    try:
        # Get all keys matching template_metrics:*
        template_keys = redis_client.keys("template_metrics:*")
        if not template_keys:
            return {
                "total_templates": 0,
                "total_validated": 0,
                "total_scan_success": 0,
                "total_refinements": 0,
                "successful_templates": [],
                "failed_templates": []
            }

        total_validated = 0
        total_scan_success = 0
        total_refinements = 0
        successful_templates = []
        failed_templates = []

        for key in template_keys:
            metrics = redis_client.hgetall(key)
            cve_id = key.split(":", 1)[1]
            validated = int(metrics.get("validated", 0))
            scan_success = int(metrics.get("scan_success", 0))
            refinements = int(metrics.get("refinements", 0))

            total_validated += validated
            total_scan_success += scan_success
            total_refinements += refinements

            if scan_success:
                successful_templates.append(cve_id)
            elif validated and not scan_success and int(metrics.get("attempts", 0)) >= 3:  # Max attempts reached
                failed_templates.append(cve_id)

        response = {
            "total_templates": len(template_keys),
            "total_validated": total_validated,
            "total_scan_success": total_scan_success,
            "total_refinements": total_refinements,
            "successful_templates": successful_templates,
            "failed_templates": failed_templates
        }
        logger.info("Fetched aggregated template metrics")
        return response
    except redis.RedisError as e:
        logger.error(f"Failed to fetch all template metrics from Redis: {e}")
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")

@router.post("/metrics/reset", response_model=Dict[str, str])
async def reset_metrics():
    """
    Reset all pipeline metrics in Redis.
    """
    try:
        # Delete global metrics
        redis_client.delete("pipeline_metrics")
        # Delete all template metrics
        template_keys = redis_client.keys("template_metrics:*")
        if template_keys:
            redis_client.delete(*template_keys)
        logger.info("Reset all pipeline metrics")
        return {"message": "Metrics reset successfully"}
    except redis.RedisError as e:
        logger.error(f"Failed to reset metrics in Redis: {e}")
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")