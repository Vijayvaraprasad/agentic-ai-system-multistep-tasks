"""
FastAPI application with async endpoints and streaming responses.
Provides REST API for task submission and execution monitoring.
"""

from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging
import json

from app.core import get_orchestrator
from app.models import TaskStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agentic AI System",
    description="Multi-agent task execution system with streaming",
    version="1.0.0",
)


class TaskRequest(BaseModel):
    """Request model for task submission."""
    task_description: str


class TaskResponse(BaseModel):
    """Response model for task creation."""
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    """Response model for task status."""
    task_id: str
    status: str
    user_input: str
    final_output: Optional[str] = None
    error_message: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator on startup."""
    orchestrator = get_orchestrator()
    logger.info("Orchestrator initialized")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "agentic-ai-system"}


@app.post("/tasks", response_model=TaskResponse)
async def create_task(request: TaskRequest):
    """
    Create a new task.
    
    Args:
        request: TaskRequest with task_description
        
    Returns:
        TaskResponse with task_id and initial status
    """
    if not request.task_description or len(request.task_description.strip()) == 0:
        raise HTTPException(status_code=400, detail="Task description cannot be empty")

    orchestrator = get_orchestrator()
    task_id = await orchestrator.create_task(request.task_description)

    logger.info(f"Task created: {task_id}")
    return TaskResponse(task_id=task_id, status=TaskStatus.PENDING.value)


@app.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the current status of a task.
    
    Args:
        task_id: The task ID
        
    Returns:
        TaskStatusResponse with current task state
    """
    orchestrator = get_orchestrator()
    task_state = orchestrator.get_task_state(task_id)

    if not task_state:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return TaskStatusResponse(
        task_id=task_id,
        status=task_state.status.value,
        user_input=task_state.user_input,
        final_output=task_state.final_output,
        error_message=task_state.error_message,
    )


@app.post("/tasks/{task_id}/execute")
async def execute_task(task_id: str, background_tasks: BackgroundTasks):
    """
    Execute a task and stream events.
    
    Args:
        task_id: The task ID
        background_tasks: FastAPI background tasks
        
    Returns:
        StreamingResponse with JSON events
    """
    orchestrator = get_orchestrator()
    task_state = orchestrator.get_task_state(task_id)

    if not task_state:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    async def event_generator():
        """Generate streaming events for task execution."""
        try:
            async for event in orchestrator.execute_task(task_id):
                # Stream each event as JSON with newline delimiter
                yield event.to_json() + "\n"
        except Exception as e:
            logger.error(f"Error during task execution: {e}")
            error_event = {
                "event_type": "error",
                "task_id": task_id,
                "data": {"error": str(e)},
            }
            yield json.dumps(error_event) + "\n"

    return StreamingResponse(
        event_generator(),
        media_type="application/x-ndjson",
        headers={"X-Task-ID": task_id},
    )


@app.get("/tasks")
async def list_tasks():
    """
    List all tasks.
    
    Returns:
        List of task summaries
    """
    orchestrator = get_orchestrator()
    tasks = []

    for task_id, task_state in orchestrator.task_states.items():
        tasks.append({
            "task_id": task_id,
            "status": task_state.status.value,
            "user_input": task_state.user_input[:100],
            "created_at": task_state.created_at.isoformat(),
        })

    return {"tasks": tasks, "total": len(tasks)}


@app.get("/")
async def root():
    """Root endpoint with API documentation."""
    return {
        "service": "Agentic AI System",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "create_task": "POST /tasks",
            "get_task_status": "GET /tasks/{task_id}/status",
            "execute_task": "POST /tasks/{task_id}/execute",
            "list_tasks": "GET /tasks",
            "docs": "/docs",
        },
    }
