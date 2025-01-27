from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn, sentry_sdk, os
from routes.NucleiRoutes import router as nuclei_router
from controllers.NucleiController import NucleiController

nco = NucleiController()

load_dotenv()

key = os.getenv("SENTRY_DSN")

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
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    nco.pull_nuclei_image()
    yield

app = FastAPI(
    lifespan=lifespan,
    title="Nuclei API",
    description="API for running Nuclei scans using Docker.",
    version="1.0.0"
)

# Register routes
app.include_router(nuclei_router, prefix="/nuclei", tags=["Nuclei"])

@app.get("/")
async def ping():
    return {"ping": "pong!"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0" , port=8080, reload=True)