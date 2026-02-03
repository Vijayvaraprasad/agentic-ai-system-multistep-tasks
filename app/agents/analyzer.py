"""
Analyzer Agent: Breaks down complex tasks into structured execution steps.
Creates a deterministic execution plan from user input.
"""

import asyncio
import json
from typing import Dict, Any, List
from app.models import ExecutionStep, ExecutionPlan, StepStatus


class AnalyzerAgent:
    """
    Analyzes a complex task and creates a structured execution plan.
    Determines which agents should handle which steps.
    """

    def __init__(self):
        """Initialize the analyzer agent."""
        self.step_counter = 0

    def _generate_step_id(self) -> str:
        """Generate a unique step ID."""
        self.step_counter += 1
        return f"step_{self.step_counter:03d}"

    async def analyze(self, task_input: str, task_id: str) -> ExecutionPlan:
        """
        Analyze the task and create an execution plan.
        
        Args:
            task_input: The user's task description
            task_id: Unique identifier for the task
            
        Returns:
            ExecutionPlan with structured steps
        """
        # Simulate analysis latency
        await asyncio.sleep(0.2)

        plan = ExecutionPlan(task_id=task_id)

        # Step 1: Retrieve context
        plan.steps.append(
            ExecutionStep(
                step_id=self._generate_step_id(),
                agent_type="retriever",
                description="Retrieve relevant context for the task",
                input_data={"query": task_input},
                status=StepStatus.PENDING,
            )
        )

        # Step 2: Analyze and plan
        plan.steps.append(
            ExecutionStep(
                step_id=self._generate_step_id(),
                agent_type="analyzer",
                description="Create detailed execution strategy",
                input_data={"task": task_input, "context_key": "retrieved_context"},
                status=StepStatus.PENDING,
            )
        )

        # Step 3: Generate output
        plan.steps.append(
            ExecutionStep(
                step_id=self._generate_step_id(),
                agent_type="writer",
                description="Generate final output based on analysis",
                input_data={"task": task_input, "analysis_key": "execution_strategy"},
                status=StepStatus.PENDING,
            )
        )

        return plan

    async def execute(self, step: ExecutionStep, context: Dict[str, Any]) -> str:
        """
        Execute the analysis step.
        
        Args:
            step: The execution step
            context: Context from previous steps
            
        Returns:
            Analysis result as JSON string
        """
        task = step.input_data.get("task", "")
        retrieved_context = context.get("retrieved_context", "")

        # Simulate analysis work
        await asyncio.sleep(0.15)

        analysis = {
            "task_summary": task[:100],
            "complexity_level": "medium",
            "required_agents": ["retriever", "analyzer", "writer"],
            "estimated_steps": 3,
            "context_used": bool(retrieved_context),
            "strategy": "Sequential execution with context enrichment",
        }

        result = json.dumps(analysis, indent=2)
        step.output = result
        step.status = StepStatus.COMPLETED

        return result
