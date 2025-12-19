# 🛠️ Development Guide

Guide for developers contributing to Speech Coach project.

## Prerequisites

- Python 3.9+
- FFmpeg (for audio extraction)
- pip (Python package manager)
- Git
- Docker (optional, for containerized development)

## Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/speech-coach.git
cd speech-coach
```

### 2. Create Virtual Environment

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Using conda
conda create -n speech-coach python=3.9
conda activate speech-coach
```

### 3. Install Dependencies

```bash
# Development dependencies (includes testing tools)
pip install -r requirements.txt

# Optional: GPU support for faster transcription
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 4. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env  # or your preferred editor
```

### 5. Verify Installation

```bash
# Run health check
python -m pytest tests/ -v

# Start development server
python -m uvicorn app.main:app --reload --port 8000
```

---

## Project Structure

```
speech-coach/
├── app/                    # Main application
│   ├── api/               # API routes
│   ├── core/              # Core application logic
│   ├── models/            # Pydantic models
│   ├── services/          # Business logic
│   ├── templates/         # HTML templates
│   └── main.py            # FastAPI app
├── tests/                 # Test suite
├── docs/                  # Documentation
├── .gitignore             # Git ignore rules
├── .env.example           # Environment template
├── requirements.txt       # Python dependencies
└── README.md              # Project overview
```

---

## Running the Application

### Development Mode

```bash
# Auto-reload on file changes
python -m uvicorn app.main:app --reload --port 8000

# With verbose logging
python -m uvicorn app.main:app --reload --port 8000 --log-level debug
```

### Production Mode

```bash
# Using gunicorn (production ASGI server)
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --port 8000

# Using uvicorn with multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker

```bash
# Build image
docker build -t speech-coach:latest .

# Run container
docker run -p 8000:8000 -v $(pwd)/.env:/app/.env speech-coach:latest

# Development with hot-reload
docker-compose -f docker-compose.yml up
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_analyzer.py -v

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run tests matching pattern
pytest -k "filler" -v

# Run async tests
pytest tests/ -v --asyncio-mode=auto
```

### Writing Tests

#### Basic Test Structure

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

#### Async Test Example

```python
import pytest
from app.services.transcriber import Transcriber

@pytest.mark.asyncio
async def test_transcription():
    transcriber = Transcriber()
    result = await transcriber.transcribe("path/to/audio.wav")
    assert result is not None
    assert "text" in result
```

#### Using Fixtures

```python
@pytest.fixture
def sample_audio_file():
    return "tests/fixtures/sample_audio.wav"

@pytest.fixture
def sample_video_file():
    return "tests/fixtures/sample_video.mp4"

def test_analysis_with_fixtures(sample_video_file, client):
    with open(sample_video_file, "rb") as f:
        response = client.post("/analyze", files={"file": f})
    assert response.status_code == 200
```

### Test Files

```
tests/
├── conftest.py                              # Fixtures and configuration
├── test_analyzer.py                         # Analyzer tests
├── test_cache.py                            # Cache tests
├── test_chat.py                             # Chat routes tests
├── test_contextual_filler_analyzer.py       # Filler detection tests
├── test_logic.py                            # Core logic tests
└── fixtures/                                # Test data
    ├── sample_audio.wav
    ├── sample_video.mp4
    └── expected_results.json
```

---

## Code Style & Standards

### Python Code Style

Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with these tools:

#### Formatting

```bash
# Format code with Black
black app/ tests/

# Check formatting without modifying
black --check app/ tests/

# Format with line length 100
black --line-length 100 app/ tests/
```

#### Linting

```bash
# Lint with flake8
flake8 app/ tests/

# Lint with specific configuration
flake8 app/ tests/ --max-line-length=100 --ignore=E203,E266,E501,W503
```

#### Type Checking

```bash
# Check types with mypy
mypy app/

# Check with strict mode
mypy app/ --strict
```

### Code Quality Checklist

- [ ] Follows PEP 8 style guide
- [ ] Passes flake8 linting
- [ ] Type hints on all functions
- [ ] Docstrings for all public functions
- [ ] Comprehensive error handling
- [ ] No hardcoded secrets or credentials
- [ ] No `print()` statements (use logging)
- [ ] Handles edge cases
- [ ] Follows DRY principle
- [ ] Tests written and passing

### Naming Conventions

```python
# Functions and variables: snake_case
def analyze_speech_pattern():
    file_path = "data/audio.wav"

# Classes: PascalCase
class SpeechAnalyzer:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_FILE_SIZE = 100_000_000
DEFAULT_MODEL_SIZE = "base"

# Private methods: _leading_underscore
def _internal_helper():
    pass

# "Dunder" only for special methods
def __init__(self):
    pass
```

### Docstring Format

```python
def analyze_audio(file_path: str, model: str = "base") -> dict:
    """
    Analyze audio file for speech metrics.

    Args:
        file_path: Path to audio file (WAV, MP3, OGG)
        model: Whisper model size (tiny, base, small, medium, large)

    Returns:
        Dictionary with analysis results:
            - duration_sec: Total duration in seconds
            - words_per_minute: Speaking rate
            - filler_words: Count of filler words detected
            - pauses: Information about pauses

    Raises:
        FileNotFoundError: If file does not exist
        UnsupportedFileTypeError: If file format not supported
        AnalysisError: If analysis fails

    Example:
        >>> result = analyze_audio("speech.wav")
        >>> print(result["words_per_minute"])
        125.3
    """
```

---

## Debugging

### Using Print Statements (for simple cases)

```python
import logging

logger = logging.getLogger(__name__)

def analyze_speech(audio_path):
    logger.debug(f"Starting analysis for {audio_path}")
    # ... analysis code ...
    logger.info(f"Analysis completed: {len(words)} words detected")
```

### Using Python Debugger

```python
import pdb

def problematic_function():
    data = load_data()
    pdb.set_trace()  # Execution pauses here
    result = process_data(data)
    return result
```

### VS Code Debugging

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/app/main.py",
      "console": "integratedTerminal",
      "justMyCode": true,
      "args": ["--reload"],
      "env": {"PYTHONPATH": "${workspaceFolder}"}
    },
    {
      "name": "Python: Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/", "-v", "--tb=short"],
      "console": "integratedTerminal",
      "justMyCode": true
    }
  ]
}
```

---

## Common Development Tasks

### Adding a New API Endpoint

1. **Create the route handler** in `app/api/routes/new_feature.py`:

```python
from fastapi import APIRouter, UploadFile, File
from app.core.exceptions import SpeechCoachException

router = APIRouter(prefix="/api/v1", tags=["new-feature"])

@router.post("/new-endpoint")
async def new_endpoint(file: UploadFile = File(...)):
    """Handle new endpoint request."""
    try:
        # Process file
        result = await process_file(file)
        return result
    except Exception as e:
        raise SpeechCoachException(f"Error: {str(e)}")
```

2. **Register the router** in `app/main.py`:

```python
from app.api.routes import new_feature

app.include_router(new_feature.router)
```

3. **Write tests** in `tests/test_new_feature.py`:

```python
def test_new_endpoint(client):
    with open("tests/fixtures/sample.mp4", "rb") as f:
        response = client.post("/api/v1/new-endpoint", files={"file": f})
    assert response.status_code == 200
```

### Adding a New Service

1. **Create service** in `app/services/new_service.py`:

```python
class NewService:
    """Service for new functionality."""
    
    async def process_data(self, data: dict) -> dict:
        """Process data."""
        # Implementation
        return result
```

2. **Use dependency injection** in routes:

```python
from app.services.new_service import NewService

@router.post("/endpoint")
async def handler(
    service: NewService = Depends(get_new_service)
):
    result = await service.process_data(data)
    return result
```

### Adding a New Model

1. **Create model** in `app/models/new_model.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional

class NewModel(BaseModel):
    """Model for new data structure."""
    field1: str = Field(..., description="Field description")
    field2: int = Field(default=0, ge=0, description="Non-negative integer")
    field3: Optional[str] = None

    model_config = {"example": {...}}
```

2. **Use in routes**:

```python
@router.post("/endpoint", response_model=NewModel)
async def handler() -> NewModel:
    return NewModel(field1="value", field2=42)
```

---

## Git Workflow

### Branch Naming

```
feature/description      # New feature
bugfix/issue-number      # Bug fix
docs/description         # Documentation
refactor/description     # Refactoring
test/description         # Tests
```

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Example:
```
feat(analyzer): add contextual filler detection

- Implement context-aware filler word detection
- Add new ContextualFillerAnalyzer service
- Update analyzer tests

Closes #123
```

### Commit Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Tests
- `perf`: Performance improvement
- `chore`: Build, dependencies, configuration

---

## Troubleshooting

### Common Issues

#### Issue: Import errors

```
ModuleNotFoundError: No module named 'app'
```

**Solution**: Ensure you're running from project root and venv is activated:
```bash
cd speech-coach
source venv/bin/activate
```

#### Issue: FFmpeg not found

```
FileNotFoundError: ffmpeg not found
```

**Solution**: Install FFmpeg:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
choco install ffmpeg
```

#### Issue: Tests failing with audio files

**Solution**: Ensure test fixtures exist:
```bash
mkdir -p tests/fixtures
# Add sample audio files to tests/fixtures/
```

#### Issue: GigaChat API connection fails

**Solution**: Check environment variables:
```bash
# In .env file
GIGACHAT_API_KEY=your_api_key
GIGACHAT_API_URL=https://api.gigachat.ru/api/v1
GIGACHAT_VERIFY_SSL=true
```

---

## Performance Profiling

### Using cProfile

```bash
# Run with profiler
python -m cProfile -s cumtime -m pytest tests/test_analyzer.py

# Generate stats file
python -c "
import cProfile
import app.main
cProfile.run('app.main:app', 'stats')
"
```

### Memory Profiling

```bash
# Install memory_profiler
pip install memory-profiler

# Run with memory profiler
python -m memory_profiler app/main.py
```

---

## Continuous Integration

### GitHub Actions

See `.github/workflows/` for CI/CD configuration:

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
```

---

## Resource Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [pytest Documentation](https://docs.pytest.org/)
- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [Python Logging](https://docs.python.org/3/library/logging.html)
- [Whisper Documentation](https://github.com/openai/whisper)

---

**Last Updated**: December 19, 2025
**Version**: 1.0.0
