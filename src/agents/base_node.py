# src/agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel
from src.config import settings
from src.services.AIService import AIService
from src.prompts.templates import get_prompt_template
from src.schemas.state import AgentState

# class AgentRequest(BaseModel):
#     """Base request model for all agents"""
#     session_id: str
#     user_input: str
#     context: Optional[Dict[str, Any]] = None

# class AgentResponse(BaseModel):
#     """Base response model for all agents"""
#     content: str
#     metadata: Optional[Dict[str, Any]] = None
#     next_agent: Optional[str] = None

class BaseNode(ABC):
    """Abstract base class for all nodes"""

    def __init__(self):
        # self.settings = settings
        self.ai_service = AIService()
        self.state = AgentState

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """Return list of node capabilities"""
        pass
    
    def get_prompt(self, prompt_name: str) -> str:
        """Helper to fetch prompt templates by name"""
        return get_prompt_template(prompt_name)