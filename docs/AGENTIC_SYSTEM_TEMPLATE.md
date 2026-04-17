# Agentic System Architecture Template

## Overview

This document provides a reusable architectural template for building agentic AI systems. It establishes patterns for organizing multi-agent architectures, service integrations, and scalable AI applications that can be adapted across different domains.

## Core Architectural Principles

### 1. **Separation of Concerns**
- **Agents**: Business logic and AI decision-making
- **Services**: External API integrations and infrastructure
- **API**: Request/response handling and routing
- **Config**: Environment and settings management
- **Utils**: Shared utilities and helpers

### 2. **Agent Orchestration Pattern**
- Central orchestrator for request routing
- Specialized agents for domain-specific tasks
- State management across conversations
- Error handling and fallback mechanisms

### 3. **Service Integration Layer**
- Abstract external dependencies
- Consistent error handling
- Retry logic and circuit breakers
- Configuration-driven service selection

## Directory Structure Template

```
project-name/
├── main.py                    # CLI entry point
├── pyproject.toml            # Project configuration
├── requirements.txt          # Dependencies
├── README.md                 # Project documentation
├── Dockerfile                # Containerization
├── docker-compose.yml        # Multi-service setup
├── .env.example              # Environment template
└── src/                      # Main application package
    ├── __init__.py
    ├── main.py              # FastAPI app instance
    ├── agents/              # AI Agent implementations
    │   ├── __init__.py
    │   ├── base_agent.py    # Abstract agent base class
    │   ├── orchestrator.py  # Main coordinator agent
    │   └── [domain]_agent.py # Specialized agents
    ├── api/                 # API route handlers
    │   ├── __init__.py
    │   ├── health.py        # Health checks
    │   ├── chat.py          # Main interaction endpoint
    │   └── [feature].py     # Feature-specific endpoints
    ├── config/              # Configuration management
    │   ├── __init__.py
    │   ├── settings.py      # Pydantic settings
    │   └── [service]_config.py # Service-specific config
    ├── prompts/             # AI prompt templates
    │   ├── __init__.py
    │   └── templates.py     # Reusable prompt templates
    ├── schemas/             # Data models
    │   ├── __init__.py
    │   ├── requests.py      # Request models
    │   └── responses.py     # Response models
    ├── services/            # External service integrations
    │   ├── __init__.py
    │   ├── base_service.py  # Abstract service base class
    │   ├── llm_service.py   # Language model integration
    │   ├── vector_service.py # Vector database
    │   └── [external]_service.py # Other integrations
    ├── utils/               # Utility functions
    │   ├── __init__.py
    │   ├── logging.py       # Logging configuration
    │   └── helpers.py       # Common utilities
    └── middleware/          # Custom middleware
        ├── __init__.py
        └── [middleware].py
```

## Component Patterns

### Agent Base Class Pattern

```python
# src/agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel

class AgentRequest(BaseModel):
    """Base request model for all agents"""
    session_id: str
    user_input: str
    context: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    """Base response model for all agents"""
    content: str
    metadata: Optional[Dict[str, Any]] = None
    next_agent: Optional[str] = None

class BaseAgent(ABC):
    """Abstract base class for all agents"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def process(self, request: AgentRequest) -> AgentResponse:
        """Process a request and return a response"""
        pass

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """Return list of agent capabilities"""
        pass
```

### Orchestrator Pattern

```python
# src/agents/orchestrator.py
from typing import Dict, Type
from .base_agent import BaseAgent, AgentRequest, AgentResponse

class AgentOrchestrator:
    """Routes requests to appropriate agents"""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.routing_rules: Dict[str, str] = {}

    def register_agent(self, name: str, agent: BaseAgent):
        """Register an agent with the orchestrator"""
        self.agents[name] = agent

    def add_routing_rule(self, condition: str, agent_name: str):
        """Add routing rule based on request characteristics"""
        self.routing_rules[condition] = agent_name

    async def route_request(self, request: AgentRequest) -> AgentResponse:
        """Route request to appropriate agent"""
        target_agent = self._determine_target_agent(request)
        return await self.agents[target_agent].process(request)

    def _determine_target_agent(self, request: AgentRequest) -> str:
        """Determine which agent should handle the request"""
        # Implement routing logic based on:
        # - Request content analysis
        # - User context
        # - Agent availability
        # - Load balancing
        pass
```

### Service Integration Pattern

```python
# src/services/base_service.py
from abc import ABC, abstractmethod
from typing import Any, Optional
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

class ServiceError(Exception):
    """Base exception for service errors"""
    pass

class BaseService(ABC):
    """Abstract base class for external services"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None

    @abstractmethod
    async def initialize(self):
        """Initialize the service client"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if service is healthy"""
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _make_request(self, operation: str, **kwargs) -> Any:
        """Make request with retry logic"""
        try:
            return await self._execute_operation(operation, **kwargs)
        except Exception as e:
            raise ServiceError(f"Service operation failed: {e}")

    @abstractmethod
    async def _execute_operation(self, operation: str, **kwargs) -> Any:
        """Execute specific service operation"""
        pass
```

### Configuration Pattern

```python
# src/config/settings.py
from pydantic import BaseSettings, Field
from typing import List, Optional

class LLMSettings(BaseSettings):
    """LLM service configuration"""
    provider: str = Field(default="openai", env="LLM_PROVIDER")
    api_key: str = Field(..., env="LLM_API_KEY")
    model: str = Field(default="gpt-4", env="LLM_MODEL")
    temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")

class VectorDBSettings(BaseSettings):
    """Vector database configuration"""
    provider: str = Field(default="pinecone", env="VECTOR_PROVIDER")
    api_key: str = Field(..., env="VECTOR_API_KEY")
    index_name: str = Field(..., env="VECTOR_INDEX_NAME")
    dimension: int = Field(default=1536, env="VECTOR_DIMENSION")

class AppSettings(BaseSettings):
    """Main application settings"""
    app_name: str = Field(default="Agentic System", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    version: str = "1.0.0"

    # Service configurations
    llm: LLMSettings = LLMSettings()
    vector_db: VectorDBSettings = VectorDBSettings()

    # API settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000"],
        env="ALLOWED_ORIGINS"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = AppSettings()
```

## API Structure Patterns

### Health Check Endpoint

```python
# src/api/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.settings import settings
from src.services.base_service import BaseService

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "version": settings.version}

@router.get("/ready")
async def readiness_check(
    llm_service: BaseService = Depends(),
    vector_service: BaseService = Depends()
):
    """Readiness check - verifies all dependencies"""
    checks = {
        "llm_service": await llm_service.health_check(),
        "vector_service": await vector_service.health_check(),
    }

    if all(checks.values()):
        return {"status": "ready", "checks": checks}
    else:
        return {"status": "not ready", "checks": checks}, 503
```

### Main Chat Endpoint

```python
# src/api/chat.py
from fastapi import APIRouter, HTTPException, Depends
from src.agents.orchestrator import AgentOrchestrator
from src.schemas.requests import ChatRequest
from src.schemas.responses import ChatResponse

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    orchestrator: AgentOrchestrator = Depends()
):
    """Main chat endpoint"""
    try:
        agent_request = request.to_agent_request()
        agent_response = await orchestrator.route_request(agent_request)
        return ChatResponse.from_agent_response(agent_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    orchestrator: AgentOrchestrator = Depends()
):
    """Streaming chat endpoint"""
    # Implementation for streaming responses
    pass
```

## Testing Structure

```
tests/
├── __init__.py
├── conftest.py              # Test configuration and fixtures
├── unit/                    # Unit tests
│   ├── __init__.py
│   ├── test_agents.py       # Agent unit tests
│   ├── test_services.py     # Service unit tests
│   └── test_utils.py        # Utility tests
├── integration/             # Integration tests
│   ├── __init__.py
│   ├── test_agent_orchestration.py
│   └── test_service_integration.py
└── e2e/                     # End-to-end tests
    ├── __init__.py
    └── test_full_workflow.py
```

## Deployment Patterns

### Dockerfile Template

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose Template

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "${PORT:-8000}:8000"
    environment:
      - REDIS_URL=redis://redis:6379
    env_file:
      - .env
    depends_on:
      - redis
    volumes:
      - .:/app
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

## Environment Configuration Template

```bash
# Application
APP_NAME=Agentic System
DEBUG=false
VERSION=1.0.0

# API
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# LLM Service
LLM_PROVIDER=openai
LLM_API_KEY=your_llm_api_key
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.7

# Vector Database
VECTOR_PROVIDER=pinecone
VECTOR_API_KEY=your_vector_api_key
VECTOR_INDEX_NAME=agent-knowledge
VECTOR_DIMENSION=1536

# Redis
REDIS_URL=redis://localhost:6379

# Other Services
# Add service-specific environment variables here
```

## Key Design Patterns

### 1. **Dependency Injection**
- Use FastAPI's dependency system for service injection
- Enables easy testing and service swapping
- Supports configuration-driven service selection

### 2. **Observer Pattern for Agents**
- Agents can subscribe to events from other agents
- Enables complex multi-agent workflows
- Supports dynamic agent composition

### 3. **Circuit Breaker Pattern**
- Protect against cascading failures
- Implement in service layer for external APIs
- Use libraries like `tenacity` for retry logic

### 4. **Configuration as Code**
- Use Pydantic for runtime configuration validation
- Environment variable binding
- Type safety for configuration

### 5. **Middleware for Cross-Cutting Concerns**
- Logging middleware for request tracing
- Authentication middleware
- Rate limiting middleware
- Error handling middleware

## Scaling Considerations

### Horizontal Scaling
- Stateless agents and services
- External session storage (Redis)
- Load balancing at infrastructure level

### Vertical Scaling
- Optimize agent processing
- Batch operations where possible
- Async processing for long-running tasks

### Service Scaling
- Circuit breakers for service protection
- Connection pooling
- Resource limits and quotas

## Monitoring and Observability

### Metrics to Track
- Agent processing latency
- Service health status
- Error rates by agent/service
- Request throughput
- Resource utilization

### Logging Strategy
- Structured logging with context
- Request ID tracing across services
- Agent decision logging
- Error tracking with stack traces

## Security Considerations

### API Security
- Input validation and sanitization
- Rate limiting
- Authentication and authorization
- CORS configuration

### Service Security
- API key rotation
- Secure credential storage
- Network isolation
- Service mesh for inter-service communication

## Development Workflow

1. **Setup**: Clone template, configure environment
2. **Development**: Implement agents and services
3. **Testing**: Write unit and integration tests
4. **Integration**: Add new agents to orchestrator
5. **Deployment**: Containerize and deploy
6. **Monitoring**: Set up observability

## Customization Guidelines

### Adding New Agents
1. Extend `BaseAgent` class
2. Implement required methods
3. Register with orchestrator
4. Add routing rules
5. Update tests

### Adding New Services
1. Extend `BaseService` class
2. Implement service-specific logic
3. Add configuration settings
4. Update dependency injection
5. Add health checks

### Extending API
1. Create new router in `api/`
2. Add request/response models
3. Include router in main app
4. Add tests
5. Update documentation

This template provides a solid foundation for building scalable, maintainable agentic systems that can be adapted to various domains and use cases.</content>
<parameter name="filePath">c:\SCG\aristotle_jane\aristotle-ai-service\AGENTIC_SYSTEM_TEMPLATE.md