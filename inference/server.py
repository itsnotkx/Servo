from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import logging

import inference
from inference.models.classification import ProcessingResult, ClassificationResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the inference engine on startup
    logger.info("Initializing inference engine...")
    inference.init()
    yield
    # Clean up (if needed) on shutdown
    pass

app = FastAPI(title="Servo Inference API", lifespan=lifespan)

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

# Request Models
class ProcessRequest(BaseModel):
    prompt: str
    workflow: str = "default"
    use_quick_classify: bool = False

class ClassifyRequest(BaseModel):
    prompt: str
    use_quick: bool = False

# Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Servo Inference API is running",
        "docs_url": "/docs",
        "endpoints": [
            "/process (POST)",
            "/classify (POST)",
            "/health (GET)",
            "/workflows (GET)"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.post("/process", response_model=ProcessingResult)
async def process_prompt(request: ProcessRequest):
    """
    Process a prompt through the full inference workflow.
    """
    logger.info(f"Received request: {request.model_dump()}")
    try:
        result = inference.process(
            prompt=request.prompt,
            workflow=request.workflow,
            use_quick_classify=request.use_quick_classify
        )
        return result
    except Exception as e:
        logger.error(f"Error processing prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/classify", response_model=ClassificationResult)
async def classify_prompt(request: ClassifyRequest):
    """
    Classify a prompt without routing.
    """
    try:
        result = inference.classify(
            prompt=request.prompt,
            use_quick=request.use_quick
        )
        return result
    except Exception as e:
        logger.error(f"Error classifying prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflows")
async def list_workflows():
    """List available workflows."""
    return {"workflows": inference.list_workflows()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("inference.server:app", host="0.0.0.0", port=8000, reload=True)
