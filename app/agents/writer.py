"""
Writer Agent: Generates final output incrementally.
Produces the final deliverable based on analysis and context.
"""

import asyncio
from typing import Dict, Any
from app.models import ExecutionStep, StepStatus


class WriterAgent:
    """
    Generates the final output incrementally.
    Produces comprehensive results based on analysis and context.
    """

    async def generate_output(
        self, task: str, analysis: str, context: str, step: ExecutionStep
    ) -> str:
        """
        Generate the final output.
        
        Args:
            task: Original task description
            analysis: Analysis from analyzer agent
            context: Context from retriever agent
            step: The execution step
            
        Returns:
            Generated output
        """
        # Simulate generation work
        await asyncio.sleep(0.1)

        output = f"""
# Task Execution Report

## Original Task
{task}

## Retrieved Context
{context}

## Analysis
{analysis}

## Final Output
The task has been successfully analyzed and executed through a multi-agent system:

1. **Retrieval Phase**: Relevant context was gathered from the knowledge base
2. **Analysis Phase**: The task was decomposed into structured steps
3. **Generation Phase**: This comprehensive report was generated

## Execution Summary
- Total steps executed: 3
- Status: Completed successfully
- All agents performed their designated roles
- Output generated with full context awareness

## Recommendations
- Monitor system performance metrics
- Consider caching frequently accessed context
- Implement distributed execution for parallel steps
"""

        step.output = output
        step.status = StepStatus.COMPLETED

        return output

    async def execute(self, step: ExecutionStep, context: Dict[str, Any]) -> str:
        """
        Execute the writer step.
        
        Args:
            step: The execution step
            context: Context from previous steps
            
        Returns:
            Generated output
        """
        task = step.input_data.get("task", "")
        analysis = context.get("execution_strategy", "")
        retrieved_context = context.get("retrieved_context", "")

        return await self.generate_output(task, analysis, retrieved_context, step)
