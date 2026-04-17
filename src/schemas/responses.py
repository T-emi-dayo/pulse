# src/schemas/responses.py
from pydantic import BaseModel
from typing import Optional, Dict, Any

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    content: str
    metadata: Optional[Dict[str, Any]] = None
    next_agent: Optional[str] = None

    @classmethod
    def from_agent_response(cls, agent_response):
        """Convert from AgentResponse"""
        return cls(
            content=agent_response.content,
            metadata=agent_response.metadata,
            next_agent=agent_response.next_agent
        )