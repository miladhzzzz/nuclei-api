from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn, sentry_sdk, os
from fastapi.middleware.cors import CORSMiddleware
from routes.NucleiRoutes import router as nuclei_router
from controllers.NucleiController import NucleiController

nco = NucleiController()

load_dotenv()

key = os.getenv("SENTRY_DSN")
port = os.getenv("APP_PORT")
env = os.getenv("ENVIRONMENT")
release_env = os.getenv("RELEASE")

sentry_sdk.init(
    dsn=key,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    _experiments={
        # Set continuous_profiling_auto_start to True
        # to automatically start the profiler on when
        # possible.
        "continuous_profiling_auto_start": True,
    },
    environment=env,
    release=release_env,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    nco.pull_nuclei_image()
    yield

app = FastAPI(
    lifespan=lifespan,
    title="Nuclei API",
    description="API for running Nuclei scans using Docker.",
    version="0.1.1",
    openapi_url=None,
    debug=False
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_methods=["*"],  # Allow all HTTP methods, including OPTIONS
    allow_headers=["*"],  # Allow all headers
)

# Register routes
app.include_router(nuclei_router, prefix="/nuclei", tags=["Nuclei"])

# This is for healthchecks disable if you dont want to do health checks
@app.get("/")
async def ping():
    return {"ping": "pong!"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0" , port=int(port))