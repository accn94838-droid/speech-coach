# ⚙️ Configuration Guide

Complete guide to configuring Speech Coach application.

## Environment Variables

Create a `.env` file in the project root with the following variables:

### Server Configuration

```bash
# Server Host
APP_HOST=0.0.0.0

# Server Port
APP_PORT=8000

# Environment (development, staging, production)
ENVIRONMENT=development

# Debug mode (disable in production)
DEBUG=False

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO
```

### Security Configuration

```bash
# CORS allowed origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# CORS allow credentials
CORS_ALLOW_CREDENTIALS=true

# API key for authentication (if needed)
API_KEY=your-secret-api-key-here

# Enable HTTPS
SSL_CERTFILE=/path/to/cert.pem
SSL_KEYFILE=/path/to/key.pem
SSL_VERIFY_SSL=true
```

### File Upload Configuration

```bash
# Max file size in bytes (100 MB default)
MAX_FILE_SIZE=104857600

# Allowed file extensions (comma-separated)
ALLOWED_EXTENSIONS=mp4,webm,avi,mov,wav,mp3,ogg,flac

# Temporary upload directory
UPLOAD_TEMP_DIR=/tmp/speech-coach-uploads

# Keep temporary files (for debugging)
KEEP_TEMP_FILES=false
```

### Speech Processing Configuration

```bash
# Whisper model size (tiny, base, small, medium, large)
WHISPER_MODEL_SIZE=base

# Whisper compute type (int8, int16, float16, float32)
WHISPER_COMPUTE_TYPE=float32

# Number of parallel processes
WHISPER_NUM_WORKERS=1

# Device (cpu, cuda, auto)
WHISPER_DEVICE=cpu

# Language code (en, ru, etc., or auto-detect)
WHISPER_LANGUAGE=ru

# Enable timestamp detection
WHISPER_TIMESTAMPS=true
```

### Audio Processing Configuration

```bash
# Target audio sample rate (Hz)
AUDIO_SAMPLE_RATE=16000

# Audio channels (1 for mono, 2 for stereo)
AUDIO_CHANNELS=1

# FFmpeg path (auto-detect if not set)
FFMPEG_PATH=ffmpeg

# Keep original audio (for debugging)
KEEP_ORIGINAL_AUDIO=false
```

### VAD (Voice Activity Detection) Configuration

```bash
# Enable VAD
VAD_ENABLED=true

# VAD aggressiveness (0-3, higher = more aggressive)
VAD_AGGRESSIVENESS=2

# Minimum speech duration (seconds)
VAD_MIN_SPEECH_DURATION=0.1

# Minimum silence duration (seconds)
VAD_MIN_SILENCE_DURATION=0.3
```

### Analysis Configuration

```bash
# Filler words list (semicolon-separated)
# Leave empty to use defaults
FILLER_WORDS=ээ;мм;ну;вот;и;типа;короче

# Minimum pause duration (seconds)
MIN_PAUSE_DURATION=1.0

# Speech rate calculation (words per minute)
CALCULATE_WPM=true

# Enable contextual analysis
CONTEXTUAL_ANALYSIS_ENABLED=true
```

### Cache Configuration

```bash
# Cache backend (memory, redis, file)
CACHE_BACKEND=file

# Cache directory (for file-based cache)
CACHE_DIR=/tmp/speech-coach-cache

# Cache TTL in seconds (time to live)
CACHE_TTL=3600

# Redis URL (if using Redis)
REDIS_URL=redis://localhost:6379/0

# Enable cache
CACHE_ENABLED=true

# Cache size limit (bytes)
CACHE_MAX_SIZE=1073741824  # 1GB
```

### GigaChat Configuration (Optional)

```bash
# GigaChat API key
GIGACHAT_API_KEY=your-gigachat-api-key

# GigaChat API URL
GIGACHAT_API_URL=https://api.gigachat.ru/api/v1

# GigaChat timeout (seconds)
GIGACHAT_TIMEOUT=30

# Enable SSL verification
GIGACHAT_VERIFY_SSL=true

# Enable GigaChat integration
GIGACHAT_ENABLED=false

# GigaChat model
GIGACHAT_MODEL=GigaChat

# GigaChat temperature (0.0 - 2.0)
GIGACHAT_TEMPERATURE=1.0

# GigaChat max tokens
GIGACHAT_MAX_TOKENS=131072

# GigaChat system prompt
GIGACHAT_SYSTEM_PROMPT="You are a helpful assistant that analyzes speech patterns."
```

### Database Configuration (Optional)

```bash
# Database URL
DATABASE_URL=sqlite:///./speech_coach.db

# Or PostgreSQL
# DATABASE_URL=postgresql://user:password@localhost/speech_coach

# Connection pool size
DATABASE_POOL_SIZE=5

# Pool recycle time (seconds)
DATABASE_POOL_RECYCLE=3600

# Echo SQL queries (for debugging)
DATABASE_ECHO=false
```

### Logging Configuration

```bash
# Log file path
LOG_FILE=/var/log/speech-coach/app.log

# Log file max size (bytes)
LOG_FILE_MAX_SIZE=10485760  # 10MB

# Number of backup log files to keep
LOG_FILE_BACKUP_COUNT=5

# Log format
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# Log to file
LOG_TO_FILE=true

# Log to console
LOG_TO_CONSOLE=true
```

### Monitoring Configuration

```bash
# Enable metrics collection
METRICS_ENABLED=true

# Metrics backend (prometheus, statsd, etc.)
METRICS_BACKEND=prometheus

# StatsD host (if using StatsD)
STATSD_HOST=localhost

# StatsD port
STATSD_PORT=8125

# Enable request timing metrics
METRICS_REQUEST_TIMING=true
```

---

## Configuration Files

### .env.example

Template for environment variables:

```bash
# Copy and rename to .env
# cp .env.example .env

# Server Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
ENVIRONMENT=development
DEBUG=False
LOG_LEVEL=INFO

# Security
CORS_ORIGINS=http://localhost:3000
CORS_ALLOW_CREDENTIALS=true

# File Upload
MAX_FILE_SIZE=104857600
ALLOWED_EXTENSIONS=mp4,webm,avi,mov,wav,mp3,ogg,flac

# Speech Processing
WHISPER_MODEL_SIZE=base
WHISPER_DEVICE=cpu
WHISPER_LANGUAGE=ru

# Analysis
CONTEXTUAL_ANALYSIS_ENABLED=true

# Cache
CACHE_BACKEND=file
CACHE_ENABLED=true

# Logging
LOG_LEVEL=INFO
```

### config.py

Main configuration file using Pydantic:

```python
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr
from typing import List

class Settings(BaseSettings):
    """Application settings."""
    
    # Server
    app_host: str = Field(default="0.0.0.0", description="Server host")
    app_port: int = Field(default=8000, description="Server port", ge=1, le=65535)
    environment: str = Field(default="development", description="Environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Security
    api_key: SecretStr = Field(default=SecretStr(""), description="API key")
    cors_origins: List[str] = Field(default=["http://localhost:3000"])
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

---

## Configuration by Environment

### Development

```bash
# .env.development
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=DEBUG
WHISPER_MODEL_SIZE=tiny
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
CACHE_BACKEND=memory
GIGACHAT_ENABLED=false
```

### Staging

```bash
# .env.staging
ENVIRONMENT=staging
DEBUG=False
LOG_LEVEL=INFO
WHISPER_MODEL_SIZE=base
CORS_ORIGINS=https://staging.example.com
CACHE_BACKEND=redis
REDIS_URL=redis://redis-staging:6379/0
GIGACHAT_ENABLED=true
```

### Production

```bash
# .env.production
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=WARNING
WHISPER_MODEL_SIZE=small
CORS_ORIGINS=https://example.com
SSL_CERTFILE=/etc/ssl/certs/cert.pem
SSL_KEYFILE=/etc/ssl/private/key.pem
CACHE_BACKEND=redis
REDIS_URL=redis://redis-prod:6379/0
GIGACHAT_ENABLED=true
CACHE_TTL=7200
```

---

## Docker Configuration

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV APP_HOST=0.0.0.0

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DEBUG=True
      - LOG_LEVEL=DEBUG
      - WHISPER_MODEL_SIZE=tiny
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./app:/app/app
      - ./.env:/app/.env
    depends_on:
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

volumes:
  redis-data:
```

---

## Security Best Practices

### Environment Variables

✅ **Do's**:
- Use `.env` file (never commit to git)
- Use `.env.example` as template (without secrets)
- Rotate API keys regularly
- Use `SecretStr` for sensitive values
- Set restrictive file permissions (600)

❌ **Don'ts**:
- Hardcode secrets in code
- Commit `.env` to version control
- Share credentials in messages/emails
- Use weak default values in production
- Log sensitive information

### CORS Configuration

```bash
# Development - Allow localhost
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Production - Restrict to specific domains
CORS_ORIGINS=https://example.com,https://www.example.com

# Never use wildcards in production
# CORS_ORIGINS=*  # ❌ UNSAFE
```

### File Upload Security

```bash
# Limit file size
MAX_FILE_SIZE=104857600  # 100 MB

# Restrict file types
ALLOWED_EXTENSIONS=mp4,webm,avi,mov,wav,mp3,ogg,flac

# Clean up temporary files
KEEP_TEMP_FILES=false

# Use secure temp directory
UPLOAD_TEMP_DIR=/tmp/speech-coach-uploads
```

---

## Performance Tuning

### Whisper Model Selection

| Model | Size | Speed | Quality | VRAM |
|-------|------|-------|---------|------|
| tiny | 39M | ⚡⚡⚡ | ⭐ | 390MB |
| base | 140M | ⚡⚡ | ⭐⭐ | 500MB |
| small | 244M | ⚡ | ⭐⭐⭐ | 1GB |
| medium | 769M | Medium | ⭐⭐⭐⭐ | 2.5GB |
| large | 1.5B | Slow | ⭐⭐⭐⭐⭐ | 4GB |

```bash
# Development (fast): tiny or base
WHISPER_MODEL_SIZE=base

# Production (quality): small or medium
WHISPER_MODEL_SIZE=small
```

### Caching Strategy

```bash
# Development - Use memory cache (fast, no persistence)
CACHE_BACKEND=memory
CACHE_TTL=3600

# Production - Use Redis (persistent, shared)
CACHE_BACKEND=redis
REDIS_URL=redis://redis:6379/0
CACHE_TTL=7200
```

### Worker Configuration

```bash
# Single worker (good for development)
WHISPER_NUM_WORKERS=1

# Multiple workers (use all CPU cores)
WHISPER_NUM_WORKERS=4

# GPU acceleration
WHISPER_DEVICE=cuda
```

---

## Troubleshooting Configuration

### Issue: "FileNotFoundError: ffmpeg not found"

**Solution**: Install FFmpeg and add to PATH:

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Or set path explicitly
FFMPEG_PATH=/usr/bin/ffmpeg
```

### Issue: "GigaChat API connection failed"

**Solution**: Verify API key and URL:

```bash
# Check .env file
cat .env | grep GIGACHAT

# Test connection
curl -H "Authorization: Bearer $GIGACHAT_API_KEY" \
  https://api.gigachat.ru/api/v1/auth
```

### Issue: "Out of memory (VRAM)"

**Solution**: Use smaller Whisper model:

```bash
# Switch to smaller model
WHISPER_MODEL_SIZE=tiny

# Or use CPU instead of GPU
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=float32
```

### Issue: Cache not working

**Solution**: Check cache configuration:

```bash
# Test file cache
CACHE_BACKEND=file
CACHE_DIR=/tmp/speech-coach-cache
# Ensure directory exists and is writable
mkdir -p /tmp/speech-coach-cache
chmod 755 /tmp/speech-coach-cache

# Or use memory cache for testing
CACHE_BACKEND=memory
```

---

## Configuration Validation

### Validate Configuration at Startup

```bash
# Run with validation
python -c "from app.core.config import settings; print(settings)"

# Or in tests
def test_settings():
    from app.core.config import settings
    assert settings.app_port > 0
    assert settings.whisper_model_size in ["tiny", "base", "small", "medium", "large"]
```

---

## Advanced Configuration

### Custom Settings Class

```python
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Dict, Optional

class AdvancedSettings(BaseSettings):
    """Advanced configuration with custom validation."""
    
    # Custom validators
    @validator('whisper_model_size')
    def validate_model_size(cls, v):
        valid_sizes = ["tiny", "base", "small", "medium", "large"]
        if v not in valid_sizes:
            raise ValueError(f"Invalid model size: {v}")
        return v
    
    # Custom fields
    custom_prompts: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

---

**Last Updated**: December 19, 2025
**Version**: 1.0.0
