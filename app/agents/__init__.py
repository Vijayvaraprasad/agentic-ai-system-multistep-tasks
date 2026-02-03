"""
Agent factory and initialization module.
Provides centralized access to all agent instances.
"""

from app.agents.retriever import RetrieverAgent
from app.agents.analyzer import AnalyzerAgent
from app.agents.writer import WriterAgent


class AgentFactory:
    """Factory for creating and managing agent instances."""

    _retriever: RetrieverAgent = None
    _analyzer: AnalyzerAgent = None
    _writer: WriterAgent = None

    @classmethod
    def get_retriever(cls) -> RetrieverAgent:
        """Get or create retriever agent instance."""
        if cls._retriever is None:
            cls._retriever = RetrieverAgent()
        return cls._retriever

    @classmethod
    def get_analyzer(cls) -> AnalyzerAgent:
        """Get or create analyzer agent instance."""
        if cls._analyzer is None:
            cls._analyzer = AnalyzerAgent()
        return cls._analyzer

    @classmethod
    def get_writer(cls) -> WriterAgent:
        """Get or create writer agent instance."""
        if cls._writer is None:
            cls._writer = WriterAgent()
        return cls._writer

    @classmethod
    def get_agent(cls, agent_type: str):
        """
        Get agent by type.
        
        Args:
            agent_type: Type of agent ("retriever", "analyzer", "writer")
            
        Returns:
            Agent instance
            
        Raises:
            ValueError: If agent type is unknown
        """
        if agent_type == "retriever":
            return cls.get_retriever()
        elif agent_type == "analyzer":
            return cls.get_analyzer()
        elif agent_type == "writer":
            return cls.get_writer()
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
