from contextlib import asynccontextmanager
from helpers.config import Config
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn, sentry_sdk, os, logging
from fastapi.middleware.cors import CORSMiddleware
from api.NucleiRoutes import router as nuclei_router
from api.PipelineRoutes import router as pipeline_router
from controllers.NucleiController import NucleiController
from api import mcp_routes
from api import metrics_routes

# Configure logging globally
logging.basicConfig(
    level=getattr(logging, Config().log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

nco = NucleiController()
conf = Config()

sentry_sdk.init(
    dsn=conf.sentry_dsn,
    traces_sample_rate=conf.sentry_traces_sample_rate,
    _experiments={
        "continuous_profiling_auto_start": True,
    },
    environment=conf.env,
    release=conf.release,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    nco.pull_nuclei_image()
    yield

app = FastAPI(
    lifespan=lifespan,
    title=conf.app_title,
    description=conf.app_description,
    version=conf.app_version,
    openapi_url=conf.app_openapi_url,
    debug=conf.app_debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add metrics middleware
app.middleware("http")(metrics_routes.metrics_middleware)

# Register routes
app.include_router(nuclei_router, prefix="/nuclei", tags=["Nuclei"])
app.include_router(pipeline_router, prefix="/pipeline", tags=["Celery Pipeline"])
app.include_router(mcp_routes.router)
app.include_router(metrics_routes.router, tags=["Metrics"])

# Global exception handler for user-friendly error responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception at {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error. Please contact support if this persists.",
            "detail": str(exc),
            "path": request.url.path
        },
    )

@app.get("/")
async def ping():
    return {"ping": "pong!"}

if __name__ == "__main__":
    uvicorn.run("main:app", host=conf.app_host, port=conf.app_port)
