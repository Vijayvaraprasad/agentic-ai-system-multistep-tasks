"""
Core module initialization.
Provides access to orchestrator and other core components.
"""

from app.core.orchestrator import TaskOrchestrator

# Global orchestrator instance
_orchestrator: TaskOrchestrator = None


def get_orchestrator() -> TaskOrchestrator:
    """Get or create the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TaskOrchestrator(max_queue_size=100, max_retries=3)
    return _orchestrator
