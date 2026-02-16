"""FastAPI server for the right-sizing inference workflow."""

import os
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from .configs.user_classification_profiles import ClassificationCategory, get_user_profile
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
    user_id: str
    prompt: str
    use_quick: bool = False


class ProcessRequest(BaseModel):
    user_id: str
    prompt: str
    use_quick_classify: bool = False
    
    
class RouteRequest(BaseModel):
    user_id: str
    classification: ClassificationResult


class HealthResponse(BaseModel):
    status: str


class RouteResponse(BaseModel):
    target_model: str


class TiersResponse(BaseModel):
    tiers: Dict[str, str]


class CategoriesResponse(BaseModel):
    user_id: str
    default_category_id: str
    categories: list[ClassificationCategory]


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/classify", response_model=ClassificationResult)
async def classify_prompt(request: ClassifyRequest):
    """Classify a prompt into a user-scoped category."""
    try:
        return orchestrator.classify_only(request.prompt, request.user_id, request.use_quick)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process", response_model=ProcessingResult)
async def process_prompt(request: ProcessRequest):
    """Full processing pipeline: classify -> route -> (optional) chunk."""
    try:
        return orchestrator.process(request.prompt, request.user_id, request.use_quick_classify)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/route", response_model=RouteResponse)
async def route_classification(request: RouteRequest):
    """Route a classification result to a model."""
    try:
        target_model = orchestrator.route_only(request.user_id, request.classification)
        return {"target_model": target_model}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tiers", response_model=TiersResponse)
async def list_tiers(user_id: str = Query(default="default_user")) -> TiersResponse:
    """Compatibility endpoint: list category ids mapped to model ids."""
    try:
        return {"tiers": orchestrator.router.list_tiers(user_id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/categories", response_model=CategoriesResponse)
async def list_categories(user_id: str = Query(...)) -> CategoriesResponse:
    """List all configured categories for a user."""
    try:
        profile = get_user_profile(user_id)
        return {
            "user_id": profile.user_id,
            "default_category_id": profile.default_category_id,
            "categories": [category.model_dump() for category in profile.categories],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    
    uvicorn.run(app, host=host, port=port)
