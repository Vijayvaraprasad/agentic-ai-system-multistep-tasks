"""
Data models for the Agentic AI System.
Defines TaskState, ExecutionPlan, and event structures.
"""

from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime
import json


class TaskStatus(str, Enum):
    """Enumeration of task statuses throughout execution lifecycle."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(str, Enum):
    """Enumeration of individual step statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class EventType(str, Enum):
    """Enumeration of streaming event types."""
    STEP_STARTED = "step_started"
    PARTIAL_OUTPUT = "partial_output"
    STEP_COMPLETED = "step_completed"
    TASK_COMPLETED = "task_completed"
    ERROR = "error"


@dataclass
class ExecutionStep:
    """Represents a single step in the execution plan."""
    step_id: str
    agent_type: str  # "retriever", "analyzer", "writer"
    description: str
    input_data: Dict[str, Any]
    status: StepStatus = StepStatus.PENDING
    output: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary for serialization."""
        return {
            "step_id": self.step_id,
            "agent_type": self.agent_type,
            "description": self.description,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "retry_count": self.retry_count,
        }


@dataclass
class ExecutionPlan:
    """Represents the complete execution plan for a task."""
    task_id: str
    steps: List[ExecutionStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "steps": [step.to_dict() for step in self.steps],
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class TaskState:
    """Tracks the complete state of a task execution."""
    task_id: str
    user_input: str
    status: TaskStatus = TaskStatus.PENDING
    execution_plan: Optional[ExecutionPlan] = None
    current_step_index: int = 0
    final_output: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task state to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "user_input": self.user_input,
            "status": self.status.value,
            "execution_plan": self.execution_plan.to_dict() if self.execution_plan else None,
            "current_step_index": self.current_step_index,
            "final_output": self.final_output,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class StreamEvent:
    """Represents a single streaming event sent to the client."""
    event_type: EventType
    task_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Convert event to JSON string for streaming."""
        return json.dumps({
            "event_type": self.event_type.value,
            "task_id": self.task_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        })
