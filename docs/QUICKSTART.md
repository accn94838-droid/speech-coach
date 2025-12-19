# 🚀 Quick Start Guide

Get started with Speech Coach in 5 minutes.

## Prerequisites

- Python 3.8+
- FFmpeg installed
- Git

## Installation Steps

### 1. Clone Repository
```bash
git clone https://github.com/xXxDanya2007xXx/speech-coach.git
cd speech-coach
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt requirements-ci.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
mkdir -p logs cache
```

### 5. Run Server
```bash
uvicorn app.main:app --reload
```

**✅ API is now available at**: http://localhost:8000

Access interactive documentation: http://localhost:8000/docs

---

## Common Commands

### Development
```bash
# Start server with auto-reload
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v

# Code quality checks
mypy app/          # Type checking
flake8 app/        # Style linting
black app/         # Code formatting
```

### Production
```bash
# Run with Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run with Gunicorn (recommended)
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

---

## Basic Configuration

Create `.env` with key settings:

```ini
# Speech Recognition
WHISPER_MODEL=small         # tiny, base, small, medium, large
WHISPER_DEVICE=cpu          # cpu, cuda, mps

# Optional: GigaChat AI Analysis
GIGACHAT_ENABLED=false
GIGACHAT_API_KEY=your_key

# Logging
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/app.log

# Performance
MAX_FILE_SIZE_MB=100
MAX_CONCURRENT_ANALYSES=3
CACHE_TTL=3600
```

See `.env.example` for all configuration options.

---

## API Endpoints

### Speech Analysis
- `POST /api/v1/analyze` - Quick analysis
- `POST /api/v1/analyze/detailed` - Detailed with timings
- `GET /api/v1/analyze/formats` - Supported formats

### Chat Interface (Optional)
- `GET /chat/ui` - Chat UI
- `POST /chat` - Send message
- `POST /chat/analyze-followup` - Follow-up analysis

### Health & Metrics
- `GET /health` - Server status
- `GET /api/v1/metrics` - Performance metrics

**Full API docs**: http://localhost:8000/docs

---

## First Analysis

### Using cURL
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@video.mp4"
```

### Using Python
```python
import httpx

with open("video.mp4", "rb") as f:
    response = httpx.post(
        "http://localhost:8000/api/v1/analyze",
        files={"file": f}
    )
    print(response.json())
```

---

## Troubleshooting

### FFmpeg Not Found
```bash
# Install FFmpeg
brew install ffmpeg       # macOS
apt-get install ffmpeg    # Ubuntu
choco install ffmpeg      # Windows (PowerShell)
```

### Port 8000 Already in Use
```bash
uvicorn app.main:app --port 8001
```

### Import Errors
```bash
pip install -r requirements.txt --force-reinstall
```

### GigaChat Connection Issues
```bash
# Verify environment setup
env | grep GIGACHAT

# Test connectivity
curl https://gigachat.devices.sberbank.ru/api/v1
```

---

## Next Steps

- 📖 Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- 👨‍💻 See [DEVELOPMENT.md](DEVELOPMENT.md) for development guide
- 🔐 Check [SECURITY.md](SECURITY.md) for security practices
- 📚 View [API.md](API.md) for complete API documentation
- 🚀 Follow [DEPLOYMENT.md](DEPLOYMENT.md) for production setup

---

## Getting Help

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Review logs: `tail -f logs/app.log`
- Run tests: `pytest tests/ -v`
- Open GitHub issues for bugs
