# src/schemas/requests.py
from pydantic import BaseModel
from typing import Optional, Dict, Any

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    session_id: str
    message: str
    context: Optional[Dict[str, Any]] = None

    def to_agent_request(self):
        """Convert to AgentRequest"""
        from src.agents.base_node import AgentRequest
        return AgentRequest(
            session_id=self.session_id,
            user_input=self.message,
            context=self.context
        )