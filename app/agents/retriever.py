"""
Retriever Agent: Fetches relevant context from knowledge sources.
Simulates retrieval from a knowledge base or external source.
"""

import asyncio
from typing import Dict, Any, List
from app.models import ExecutionStep, StepStatus


class RetrieverAgent:
    """
    Retrieves relevant context for a given query.
    In production, this would connect to a vector DB, search engine, or API.
    """

    def __init__(self):
        """Initialize the retriever agent with mock knowledge base."""
        self.knowledge_base = {
            "task_execution": [
                "Tasks are broken into atomic steps",
                "Each step has a clear input and output",
                "Steps can be executed sequentially or in parallel",
            ],
            "ai_systems": [
                "AI systems require orchestration layers",
                "Agents specialize in specific tasks",
                "Streaming enables real-time feedback",
            ],
            "async_programming": [
                "Async/await enables concurrent execution",
                "Queues manage task distribution",
                "Backpressure prevents system overload",
            ],
        }

    async def retrieve(self, query: str, step: ExecutionStep) -> str:
        """
        Retrieve relevant context for the given query.
        
        Args:
            query: The search query
            step: The execution step being processed
            
        Returns:
            Retrieved context as a string
        """
        # Simulate I/O latency
        await asyncio.sleep(0.1)

        # Simple keyword matching against knowledge base
        relevant_docs = []
        query_lower = query.lower()

        for category, docs in self.knowledge_base.items():
            if any(keyword in query_lower for keyword in category.split("_")):
                relevant_docs.extend(docs)

        # If no specific match, return general context
        if not relevant_docs:
            relevant_docs = [
                "Context retrieval system is operational",
                "Multiple knowledge sources are available",
            ]

        context = "\n".join(f"- {doc}" for doc in relevant_docs[:3])
        step.output = context
        step.status = StepStatus.COMPLETED

        return context

    async def execute(self, step: ExecutionStep) -> str:
        """
        Execute the retrieval step.
        
        Args:
            step: The execution step containing query in input_data
            
        Returns:
            Retrieved context
        """
        query = step.input_data.get("query", "")
        return await self.retrieve(query, step)
