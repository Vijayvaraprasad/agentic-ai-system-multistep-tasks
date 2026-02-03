"""
Task orchestrator: Manages task execution flow and agent coordination.
Implements queue-based execution with backpressure and retry logic.
"""

import asyncio
import uuid
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import logging

from app.models import (
    TaskState,
    TaskStatus,
    ExecutionPlan,
    ExecutionStep,
    StepStatus,
    StreamEvent,
    EventType,
)
from app.agents import AgentFactory

logger = logging.getLogger(__name__)


class TaskOrchestrator:
    """
    Orchestrates multi-agent task execution.
    Manages execution queue, retries, backpressure, and streaming.
    """

    def __init__(self, max_queue_size: int = 100, max_retries: int = 3):
        """
        Initialize the orchestrator.
        
        Args:
            max_queue_size: Maximum size of execution queue (backpressure)
            max_retries: Maximum retries per step
        """
        self.max_queue_size = max_queue_size
        self.max_retries = max_retries
        self.task_states: Dict[str, TaskState] = {}
        self.execution_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.agent_factory = AgentFactory()

    async def create_task(self, user_input: str) -> str:
        """
        Create a new task and return its ID.
        
        Args:
            user_input: The user's task description
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        task_state = TaskState(task_id=task_id, user_input=user_input)
        self.task_states[task_id] = task_state
        logger.info(f"Created task {task_id}")
        return task_id

    async def analyze_task(self, task_id: str) -> ExecutionPlan:
        """
        Analyze the task and create execution plan.
        
        Args:
            task_id: The task ID
            
        Returns:
            ExecutionPlan
        """
        task_state = self.task_states[task_id]
        task_state.status = TaskStatus.ANALYZING

        analyzer = self.agent_factory.get_analyzer()
        plan = await analyzer.analyze(task_state.user_input, task_id)

        task_state.execution_plan = plan
        task_state.updated_at = datetime.utcnow()

        logger.info(f"Task {task_id} analyzed with {len(plan.steps)} steps")
        return plan

    async def _execute_step_with_retry(
        self, step: ExecutionStep, context: Dict[str, Any]
    ) -> bool:
        """
        Execute a step with exponential backoff retry logic.
        
        Args:
            step: The step to execute
            context: Context from previous steps
            
        Returns:
            True if successful, False if all retries exhausted
        """
        agent = self.agent_factory.get_agent(step.agent_type)

        while step.retry_count < step.max_retries:
            try:
                step.status = StepStatus.RUNNING
                logger.info(f"Executing step {step.step_id} (attempt {step.retry_count + 1})")

                if step.agent_type == "retriever":
                    result = await agent.execute(step)
                    context["retrieved_context"] = result
                elif step.agent_type == "analyzer":
                    result = await agent.execute(step, context)
                    context["execution_strategy"] = result
                elif step.agent_type == "writer":
                    result = await agent.execute(step, context)
                    context["final_output"] = result
                else:
                    raise ValueError(f"Unknown agent type: {step.agent_type}")

                step.status = StepStatus.COMPLETED
                step.output = result
                logger.info(f"Step {step.step_id} completed successfully")
                return True

            except Exception as e:
                step.retry_count += 1
                step.error = str(e)

                if step.retry_count < step.max_retries:
                    step.status = StepStatus.RETRYING
                    # Exponential backoff: 0.1s, 0.2s, 0.4s
                    backoff_delay = 0.1 * (2 ** (step.retry_count - 1))
                    logger.warning(
                        f"Step {step.step_id} failed, retrying in {backoff_delay}s: {e}"
                    )
                    await asyncio.sleep(backoff_delay)
                else:
                    step.status = StepStatus.FAILED
                    logger.error(f"Step {step.step_id} failed after {step.max_retries} retries: {e}")
                    return False

        return False

    async def execute_task(self, task_id: str) -> AsyncGenerator[StreamEvent, None]:
        """
        Execute the task and stream events.
        
        Args:
            task_id: The task ID
            
        Yields:
            StreamEvent objects for streaming to client
        """
        task_state = self.task_states[task_id]

        try:
            # Analyze task
            plan = await self.analyze_task(task_id)
            task_state.status = TaskStatus.EXECUTING

            context: Dict[str, Any] = {}

            # Execute each step
            for step_index, step in enumerate(plan.steps):
                task_state.current_step_index = step_index

                # Emit step started event
                yield StreamEvent(
                    event_type=EventType.STEP_STARTED,
                    task_id=task_id,
                    data={
                        "step_id": step.step_id,
                        "step_number": step_index + 1,
                        "total_steps": len(plan.steps),
                        "description": step.description,
                        "agent_type": step.agent_type,
                    },
                )

                # Execute step with retry logic
                success = await self._execute_step_with_retry(step, context)

                if success:
                    # Emit partial output event
                    yield StreamEvent(
                        event_type=EventType.PARTIAL_OUTPUT,
                        task_id=task_id,
                        data={
                            "step_id": step.step_id,
                            "output": step.output[:500] if step.output else "",
                        },
                    )

                    # Emit step completed event
                    yield StreamEvent(
                        event_type=EventType.STEP_COMPLETED,
                        task_id=task_id,
                        data={
                            "step_id": step.step_id,
                            "status": "completed",
                        },
                    )
                else:
                    # Step failed after retries
                    task_state.status = TaskStatus.FAILED
                    task_state.error_message = f"Step {step.step_id} failed: {step.error}"
                    task_state.updated_at = datetime.utcnow()

                    yield StreamEvent(
                        event_type=EventType.ERROR,
                        task_id=task_id,
                        data={
                            "step_id": step.step_id,
                            "error": step.error,
                            "retry_count": step.retry_count,
                        },
                    )
                    return

            # All steps completed successfully
            task_state.status = TaskStatus.COMPLETED
            task_state.final_output = context.get("final_output", "")
            task_state.updated_at = datetime.utcnow()

            yield StreamEvent(
                event_type=EventType.TASK_COMPLETED,
                task_id=task_id,
                data={
                    "status": "completed",
                    "final_output": task_state.final_output[:1000],
                    "total_steps": len(plan.steps),
                },
            )

        except Exception as e:
            task_state.status = TaskStatus.FAILED
            task_state.error_message = str(e)
            task_state.updated_at = datetime.utcnow()
            logger.error(f"Task {task_id} execution failed: {e}")

            yield StreamEvent(
                event_type=EventType.ERROR,
                task_id=task_id,
                data={"error": str(e)},
            )

    def get_task_state(self, task_id: str) -> Optional[TaskState]:
        """
        Get the current state of a task.
        
        Args:
            task_id: The task ID
            
        Returns:
            TaskState or None if not found
        """
        return self.task_states.get(task_id)
