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
                "refinements_started": 0,
                "refinements_successful": 0,
                "refinements_failed": 0,
                "failed_validations": 0,
                "average_validation_duration_ms": 0.0,
                "refinement_success_rate": 0.0
            }

        # Convert string values to integers and calculate averages
        templates_validated = int(metrics.get("templates_validated", 0))
        total_duration = int(metrics.get("total_validation_duration", 0))  # in ms
        avg_duration = total_duration / max(templates_validated, 1) if total_duration > 0 else 0.0
        
        # Calculate refinement success rate
        refinements_started = int(metrics.get("refinements_started", 0))
        refinements_successful = int(metrics.get("refinements_successful", 0))
        refinement_success_rate = (refinements_successful / max(refinements_started, 1)) * 100 if refinements_started > 0 else 0.0

        response = {
            "templates_generated": int(metrics.get("templates_generated", 0)),
            "templates_validated": templates_validated,
            "scan_successes": int(metrics.get("scan_successes", 0)),
            "refinements": int(metrics.get("refinements", 0)),
            "refinements_started": refinements_started,
            "refinements_successful": refinements_successful,
            "refinements_failed": int(metrics.get("refinements_failed", 0)),
            "failed_validations": int(metrics.get("failed_validations", 0)),
            "average_validation_duration_ms": round(avg_duration, 2),
            "refinement_success_rate": round(refinement_success_rate, 2)
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

@router.get("/refinement/history/{cve_id}", response_model=Dict[str, Any])
async def get_refinement_history(cve_id: str):
    """
    Fetch detailed refinement history for a specific CVE.
    Returns step-by-step refinement process with timestamps and details.
    """
    try:
        refinement_key = f"refinement_history:{cve_id}"
        history = redis_client.lrange(refinement_key, 0, -1)  # Get all history
        
        if not history:
            raise HTTPException(status_code=404, detail=f"No refinement history found for {cve_id}")
        
        # Parse JSON history entries
        parsed_history = []
        for entry in history:
            try:
                parsed_entry = json.loads(entry)
                parsed_history.append(parsed_entry)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse refinement history entry for {cve_id}")
                continue
        
        # Sort by timestamp (newest first)
        parsed_history.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        # Get current metrics for this CVE
        cve_metrics_key = f"template_metrics:{cve_id}"
        metrics = redis_client.hgetall(cve_metrics_key)
        
        response = {
            "cve_id": cve_id,
            "refinement_history": parsed_history,
            "current_metrics": {
                "attempts": int(metrics.get("attempts", 0)),
                "refinements": int(metrics.get("refinements", 0)),
                "refinements_started": int(metrics.get("refinements_started", 0)),
                "refinements_successful": int(metrics.get("refinements_successful", 0)),
                "refinements_failed": int(metrics.get("refinements_failed", 0)),
                "validated": bool(int(metrics.get("validated", 0))),
                "scan_success": bool(int(metrics.get("scan_success", 0))),
                "total_validation_time_ms": int(metrics.get("total_validation_time", 0))
            }
        }
        
        logger.info(f"Fetched refinement history for {cve_id}")
        return response
        
    except HTTPException:
        raise
    except redis.RedisError as e:
        logger.error(f"Failed to fetch refinement history for {cve_id} from Redis: {e}")
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching refinement history for {cve_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/refinement/analytics", response_model=Dict[str, Any])
async def get_refinement_analytics():
    """
    Fetch analytics about the refinement process across all templates.
    Returns insights about refinement patterns, success rates, and common issues.
    """
    try:
        # Get all template metrics
        template_keys = redis_client.keys("template_metrics:*")
        
        if not template_keys:
            return {
                "total_templates": 0,
                "templates_with_refinements": 0,
                "average_refinements_per_template": 0.0,
                "refinement_success_rate": 0.0,
                "common_validation_errors": [],
                "refinement_duration_stats": {
                    "average_duration_ms": 0.0,
                    "min_duration_ms": 0.0,
                    "max_duration_ms": 0.0
                }
            }
        
        total_refinements = 0
        successful_refinements = 0
        failed_refinements = 0
        templates_with_refinements = 0
        validation_errors = []
        durations = []
        
        for key in template_keys:
            metrics = redis_client.hgetall(key)
            refinements_started = int(metrics.get("refinements_started", 0))
            refinements_successful = int(metrics.get("refinements_successful", 0))
            refinements_failed = int(metrics.get("refinements_failed", 0))
            total_validation_time = int(metrics.get("total_validation_time", 0))
            
            if refinements_started > 0:
                templates_with_refinements += 1
                total_refinements += refinements_started
                successful_refinements += refinements_successful
                failed_refinements += refinements_failed
                
                if total_validation_time > 0:
                    durations.append(total_validation_time)
        
        # Calculate analytics
        total_templates = len(template_keys)
        avg_refinements = total_refinements / max(templates_with_refinements, 1)
        success_rate = (successful_refinements / max(total_refinements, 1)) * 100
        
        # Calculate duration statistics
        avg_duration = sum(durations) / max(len(durations), 1) if durations else 0
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        
        response = {
            "total_templates": total_templates,
            "templates_with_refinements": templates_with_refinements,
            "average_refinements_per_template": round(avg_refinements, 2),
            "refinement_success_rate": round(success_rate, 2),
            "total_refinements": total_refinements,
            "successful_refinements": successful_refinements,
            "failed_refinements": failed_refinements,
            "refinement_duration_stats": {
                "average_duration_ms": round(avg_duration, 2),
                "min_duration_ms": min_duration,
                "max_duration_ms": max_duration,
                "templates_with_duration_data": len(durations)
            }
        }
        
        logger.info("Fetched refinement analytics")
        return response
        
    except redis.RedisError as e:
        logger.error(f"Failed to fetch refinement analytics from Redis: {e}")
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching refinement analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

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
        # Delete all refinement history
        refinement_keys = redis_client.keys("refinement_history:*")
        if refinement_keys:
            redis_client.delete(*refinement_keys)
        logger.info("Reset all pipeline metrics and refinement history")
        return {"message": "Metrics and refinement history reset successfully"}
    except redis.RedisError as e:
        logger.error(f"Failed to reset metrics in Redis: {e}")
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")