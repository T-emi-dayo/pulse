# Pulse - Agentic AI System

An agentic AI system built with FastAPI, following a modular architecture for scalable multi-agent applications.

## Features

- **Modular Agent Architecture**: Extensible agent system with orchestrator pattern
- **FastAPI Backend**: High-performance async API with automatic documentation
- **Service Integration Layer**: Abstract external service dependencies
- **Configuration Management**: Pydantic-based settings with environment variable support
- **Docker Support**: Containerized deployment with docker-compose

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd pulse
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Install dependencies**:
   ```bash
   pip install -e .
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

   Or with docker:
   ```bash
   docker-compose up
   ```

4. **Access the API**:
   - API docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/api/v1/health

## Project Structure

```
pulse/
├── main.py                    # CLI entry point
├── pyproject.toml            # Project configuration
├── Dockerfile                # Containerization
├── docker-compose.yml        # Multi-service setup
├── .env.example              # Environment template
└── src/                      # Main application package
    ├── agents/              # AI Agent implementations
    ├── api/                 # API route handlers
    ├── config/              # Configuration management
    ├── prompts/             # AI prompt templates
    ├── schemas/             # Data models
    ├── services/            # External service integrations
    ├── utils/               # Utility functions
    └── middleware/          # Custom middleware
```

## Development

### Adding New Agents

1. Create a new agent class extending `BaseAgent`
2. Implement the `process` and `get_capabilities` methods
3. Register the agent with the orchestrator in the main app

### Adding New Services

1. Create a new service class extending `BaseService`
2. Implement service-specific initialization and operations
3. Add configuration settings in `settings.py`

### Running Tests

```bash
pytest
```

## Configuration

Copy `.env.example` to `.env` and configure:

- **LLM Settings**: API keys and model configuration
- **Vector DB**: Vector database connection settings
- **API Settings**: Host, port, CORS origins

## Deployment

### Docker

```bash
docker-compose up -d
```

### Manual

```bash
pip install -e .
python main.py --host 0.0.0.0 --port 8000
```

## License

[Add your license here]