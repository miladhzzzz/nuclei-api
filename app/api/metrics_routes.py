from fastapi import APIRouter, Request
from fastapi.responses import Response
from prometheus_client import (
    generate_latest, 
    CONTENT_TYPE_LATEST,
    Counter, 
    Histogram, 
    Gauge, 
    Summary,
    CollectorRegistry,
    multiprocess,
    REGISTRY
)
import time
import redis
import psutil
import os
from typing import Dict, Any
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Redis client for metrics
redis_client = redis.Redis(
    host="redis",
    port=6379,
    db=0,
    decode_responses=True
)

# FastAPI Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_request_size_bytes = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

http_response_size_bytes = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)

# Celery Metrics
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']
)

celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name']
)

celery_workers_active = Gauge(
    'celery_workers_active',
    'Number of active Celery workers'
)

celery_queue_size = Gauge(
    'celery_queue_size',
    'Number of tasks in Celery queue',
    ['queue_name']
)

# Nuclei Scan Metrics
nuclei_scans_total = Counter(
    'nuclei_scans_total',
    'Total Nuclei scans',
    ['target_type', 'template_type', 'status']
)

nuclei_scan_duration_seconds = Histogram(
    'nuclei_scan_duration_seconds',
    'Nuclei scan duration in seconds',
    ['target_type', 'template_type']
)

nuclei_vulnerabilities_found = Counter(
    'nuclei_vulnerabilities_found',
    'Total vulnerabilities found by Nuclei',
    ['severity', 'template_id']
)

# Template Generation Metrics
template_generation_total = Counter(
    'template_generation_total',
    'Total template generation attempts',
    ['cve_id', 'status']
)

template_validation_total = Counter(
    'template_validation_total',
    'Total template validation attempts',
    ['cve_id', 'status']
)

template_refinement_total = Counter(
    'template_refinement_total',
    'Total template refinement attempts',
    ['cve_id']
)

# Pipeline Metrics
pipeline_execution_total = Counter(
    'pipeline_execution_total',
    'Total pipeline executions',
    ['pipeline_type', 'status']
)

pipeline_duration_seconds = Histogram(
    'pipeline_duration_seconds',
    'Pipeline execution duration in seconds',
    ['pipeline_type']
)

# Redis Metrics
redis_operations_total = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['operation', 'status']
)

redis_memory_usage_bytes = Gauge(
    'redis_memory_usage_bytes',
    'Redis memory usage in bytes'
)

redis_connected_clients = Gauge(
    'redis_connected_clients',
    'Number of connected Redis clients'
)

# System Metrics
system_cpu_usage_percent = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

system_memory_usage_bytes = Gauge(
    'system_memory_usage_bytes',
    'System memory usage in bytes'
)

system_disk_usage_bytes = Gauge(
    'system_disk_usage_bytes',
    'System disk usage in bytes',
    ['mount_point']
)

# Docker Metrics
docker_containers_running = Gauge(
    'docker_containers_running',
    'Number of running Docker containers'
)

docker_containers_total = Gauge(
    'docker_containers_total',
    'Total number of Docker containers'
)

# Custom Business Metrics
active_scans = Gauge(
    'active_scans',
    'Number of currently active scans'
)

templates_available = Gauge(
    'templates_available',
    'Number of available templates',
    ['template_type']
)

api_errors_total = Counter(
    'api_errors_total',
    'Total API errors',
    ['error_type', 'endpoint']
)

# Middleware function for request metrics (to be applied to main app)
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Avoid consuming the request stream in middleware; using Content-Length
    # prevents POST/PUT handlers from hanging when they need to parse body.
    request_size = int(request.headers.get("content-length", "0") or 0)
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Get response size
    response_size = int(response.headers.get("content-length", "0") or 0)
    
    # Record metrics
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    http_request_size_bytes.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(request_size)
    
    http_response_size_bytes.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(response_size)
    
    # Record errors
    if response.status_code >= 400:
        api_errors_total.labels(
            error_type=f"{response.status_code}",
            endpoint=request.url.path
        ).inc()
    
    return response

def update_system_metrics():
    """Update system-level metrics"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        system_cpu_usage_percent.set(cpu_percent)
        
        # Memory usage
        memory = psutil.virtual_memory()
        system_memory_usage_bytes.set(memory.used)
        
        # Disk usage
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                system_disk_usage_bytes.labels(
                    mount_point=partition.mountpoint
                ).set(usage.used)
            except PermissionError:
                continue
    except Exception as e:
        logger.error(f"Error updating system metrics: {e}")

def update_redis_metrics():
    """Update Redis metrics"""
    try:
        info = redis_client.info()
        
        # Memory usage
        redis_memory_usage_bytes.set(info.get('used_memory', 0))
        
        # Connected clients
        redis_connected_clients.set(info.get('connected_clients', 0))
        
        # Record Redis operations (this would need to be called from Redis operations)
        redis_operations_total.labels(
            operation='info',
            status='success'
        ).inc()
        
    except Exception as e:
        logger.error(f"Error updating Redis metrics: {e}")
        redis_operations_total.labels(
            operation='info',
            status='error'
        ).inc()

def update_celery_metrics():
    """Update Celery metrics"""
    try:
        # This would require Celery inspection API
        # For now, we'll set basic metrics
        celery_workers_active.set(1)  # This should be updated with actual worker count
        
        # Queue size (basic implementation)
        queue_size = redis_client.llen('celery')
        celery_queue_size.labels(queue_name='celery').set(queue_size)
        
    except Exception as e:
        logger.error(f"Error updating Celery metrics: {e}")

def update_business_metrics():
    """Update custom business metrics"""
    try:
        # Active scans (from Redis or database)
        active_scans_count = len(redis_client.keys('scan_*'))
        active_scans.set(active_scans_count)
        
        # Templates available
        template_count = len(redis_client.keys('template_*'))
        templates_available.labels(template_type='custom').set(template_count)
        
        # Pipeline metrics from Redis
        pipeline_metrics = redis_client.hgetall('pipeline_metrics')
        if pipeline_metrics:
            templates_generated = int(pipeline_metrics.get('templates_generated', 0))
            templates_validated = int(pipeline_metrics.get('templates_validated', 0))
            scan_successes = int(pipeline_metrics.get('scan_successes', 0))
            
            # Do not increment counters from aggregate Redis values during scrape.
            # Counter updates must happen at event time via record_* helpers.
            
    except Exception as e:
        logger.error(f"Error updating business metrics: {e}")

@router.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    try:
        # Update all metrics
        update_system_metrics()
        update_redis_metrics()
        update_celery_metrics()
        update_business_metrics()
        
        # Generate Prometheus format
        return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return f"Error generating metrics: {str(e)}", 500

@router.get("/health")
async def health_check():
    """Health check endpoint with basic metrics"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "services": {
                "redis": "healthy" if redis_client.ping() else "unhealthy",
                "system": "healthy",
                "api": "healthy"
            },
            "metrics": {
                "active_scans": active_scans._value.get(),
                "cpu_usage": system_cpu_usage_percent._value.get(),
                "memory_usage": system_memory_usage_bytes._value.get(),
                "redis_memory": redis_memory_usage_bytes._value.get()
            }
        }
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }, 500

# Helper functions for other parts of the application to record metrics
def record_nuclei_scan(target_type: str, template_type: str, status: str, duration: float = None):
    """Record Nuclei scan metrics"""
    nuclei_scans_total.labels(
        target_type=target_type,
        template_type=template_type,
        status=status
    ).inc()
    
    if duration:
        nuclei_scan_duration_seconds.labels(
            target_type=target_type,
            template_type=template_type
        ).observe(duration)

def record_template_generation(cve_id: str, status: str):
    """Record template generation metrics"""
    template_generation_total.labels(
        cve_id=cve_id,
        status=status
    ).inc()

def record_template_validation(cve_id: str, status: str):
    """Record template validation metrics"""
    template_validation_total.labels(
        cve_id=cve_id,
        status=status
    ).inc()

def record_celery_task(task_name: str, status: str, duration: float = None):
    """Record Celery task metrics"""
    celery_tasks_total.labels(
        task_name=task_name,
        status=status
    ).inc()
    
    if duration:
        celery_task_duration_seconds.labels(
            task_name=task_name
        ).observe(duration)

def record_vulnerability_found(severity: str, template_id: str):
    """Record vulnerability discovery metrics"""
    nuclei_vulnerabilities_found.labels(
        severity=severity,
        template_id=template_id
    ).inc() 
