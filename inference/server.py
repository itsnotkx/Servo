"""FastAPI server for the right-sizing inference workflow."""

import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .core.orchestrator import WorkflowOrchestrator
from .models.classification import ClassificationResult, ProcessingResult


# Global orchestrator instance
orchestrator: WorkflowOrchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize orchestrator on startup."""
    global orchestrator
    orchestrator = WorkflowOrchestrator()
    yield
    # Cleanup if needed
    pass


app = FastAPI(
    title="Right-Sizing Inference API",
    description="API for classifying, routing, and chunking prompts.",
    version="0.2.0",
    lifespan=lifespan,
)


# Request models
class ClassifyRequest(BaseModel):
    prompt: str
    use_quick: bool = False


class ProcessRequest(BaseModel):
    prompt: str
    use_quick_classify: bool = False
    
    
class RouteRequest(BaseModel):
    classification: ClassificationResult


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/classify", response_model=ClassificationResult)
async def classify_prompt(request: ClassifyRequest):
    """Classify a prompt's complexity."""
    try:
        return orchestrator.classify_only(request.prompt, request.use_quick)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process", response_model=ProcessingResult)
async def process_prompt(request: ProcessRequest):
    """Full processing pipeline: classify -> route -> (optional) chunk."""
    try:
        return orchestrator.process(request.prompt, request.use_quick_classify)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/route")
async def route_classification(request: RouteRequest):
    """Route a classification result to a model."""
    try:
        target_model = orchestrator.route_only(request.classification)
        return {"target_model": target_model}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tiers")
async def list_tiers() -> Dict[str, Any]:
    """List available model tiers and their configured models."""
    try:
        return {"tiers": orchestrator.router.list_tiers()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    
    uvicorn.run(app, host=host, port=port)
