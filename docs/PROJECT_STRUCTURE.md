# Project Structure

## Directory Layout

```
speech-coach/
├── app/                              # Main application package
│   ├── __init__.py
│   ├── main.py                       # FastAPI application entry point
│   ├── api/                          # API routes
│   │   ├── deps.py                   # Dependency injection
│   │   └── routes/                   # Route handlers
│   │       ├── analysis.py           # Speech analysis endpoints
│   │       ├── chat.py               # Chat endpoints
│   │       └── health.py             # Health check endpoints
│   ├── core/                         # Core application logic
│   │   ├── config.py                 # Configuration management
│   │   ├── exceptions.py             # Custom exceptions
│   │   ├── lifespan.py               # Application lifecycle
│   │   ├── logging_config.py         # Logging setup
│   │   └── validators.py             # File validators
│   ├── models/                       # Pydantic data models
│   │   ├── analysis.py               # Analysis result models
│   │   ├── gigachat.py               # GigaChat response models
│   │   ├── gigachat_advanced.py      # Advanced GigaChat models
│   │   ├── timed_analysis.py         # Timed analysis models
│   │   ├── timed_models.py           # Detailed timing models
│   │   ├── transcriber.py            # Transcription models
│   │   └── transcript.py             # Transcript models
│   ├── services/                     # Business logic services
│   │   ├── analyzer.py               # Basic speech analysis
│   │   ├── analyzer_advanced.py      # Advanced speech analysis
│   │   ├── audio_extractor.py        # Audio extraction
│   │   ├── audio_extractor_advanced.py # Advanced audio extraction
│   │   ├── cache.py                  # Caching service
│   │   ├── contextual_filler_analyzer.py # Contextual filler detection
│   │   ├── gigachat.py               # GigaChat API client
│   │   ├── gigachat_advanced.py      # Advanced GigaChat integration
│   │   ├── metrics_collector.py      # Metrics collection
│   │   ├── pipeline.py               # Analysis pipeline
│   │   ├── pipeline_advanced.py      # Advanced analysis pipeline
│   │   ├── transcriber.py            # Speech-to-text service
│   │   └── vad.py                    # Voice activity detection
│   └── templates/                    # HTML templates
│       └── chat.html                 # Chat UI template
├── tests/                            # Test suite
│   ├── conftest.py                   # Pytest configuration
│   ├── test_analyzer.py              # Analyzer tests
│   ├── test_cache.py                 # Caching tests
│   ├── test_chat_routes.py           # Chat route tests
│   ├── test_contextual_filler_analyzer.py # Filler analyzer tests
│   ├── test_logic.py                 # Logic tests
│   └── demo_chat.py                  # Chat demonstration
├── .env.example                      # Environment variables example
├── .gitignore                        # Git ignore patterns
├── cleanup.sh                        # Cleanup script
├── REFACTORING_SUMMARY.md            # Refactoring documentation
├── requirements.txt                  # Production dependencies
├── requirements-ci.txt               # Development/CI dependencies
├── README.md                         # Main project documentation
├── README_CHAT.md                    # Chat functionality documentation
├── CHAT_API.md                       # Chat API documentation
└── LICENSE                           # Project license
```

## Key Components

### API Routes (`app/api/routes/`)
- **analysis.py**: `/api/v1/analyze` - Main speech analysis endpoint
- **chat.py**: `/chat` - GigaChat integration endpoints
- **health.py**: `/health` - Health check endpoints

### Services (`app/services/`)
Core business logic:
- **analyzer.py**: Basic speech metrics calculation
- **analyzer_advanced.py**: Detailed timing and advanced metrics
- **transcriber.py**: Speech recognition using Whisper
- **gigachat.py**: GigaChat API client
- **pipeline.py**: Orchestrates analysis workflow

### Models (`app/models/`)
Pydantic models for:
- Request/response validation
- Data serialization
- Type safety

### Core (`app/core/`)
Application infrastructure:
- **config.py**: Centralized configuration
- **exceptions.py**: Custom exception hierarchy
- **logging_config.py**: Structured logging setup
- **validators.py**: File validation utilities

## Configuration

### Environment Variables
See `.env.example` for all available configuration options:
- API keys and authentication
- Model parameters
- Performance tuning
- Logging settings

### Key Settings
- `WHISPER_MODEL`: Speech recognition model size (tiny, base, small, medium, large)
- `GIGACHAT_ENABLED`: Enable/disable GigaChat integration
- `MAX_FILE_SIZE_MB`: Maximum upload file size
- `CACHE_TTL`: Caching time-to-live in seconds

## Testing

Run tests:
```bash
pytest tests/
```

Run specific test:
```bash
pytest tests/test_analyzer.py -v
```

Run with coverage:
```bash
pytest --cov=app tests/
```

## Development

Install development dependencies:
```bash
pip install -r requirements.txt requirements-ci.txt
```

Run linting:
```bash
flake8 app/
black app/
```

Type checking:
```bash
mypy app/
```

## Production Deployment

1. Create `.env` from `.env.example`
2. Set required values (especially `GIGACHAT_API_KEY` if using GigaChat)
3. Run migrations/setup if needed
4. Start server: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

See main README.md for detailed deployment instructions.
