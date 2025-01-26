from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn, datetime
from routes.NucleiRoutes import router as nuclei_router
from controllers.NucleiController import NucleiController

nco = NucleiController()

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
async def root():
    return {"message": "Welcome to the Nuclei API"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0" , port=8080, reload=True)