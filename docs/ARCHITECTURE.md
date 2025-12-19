# 🏗️ Architecture

Speech Coach system design and architecture.

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Client (Web/API)                    │
└────────────────────────┬────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   ┌─────────┐      ┌─────────┐      ┌─────────┐
   │ Analysis│      │  Chat   │      │ Health  │
   │ Routes  │      │ Routes  │      │ Routes  │
   └────┬────┘      └────┬────┘      └────┬────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────▼────────────────┐
        │    FastAPI Application           │
        │  (app/main.py)                   │
        └────────────────┬────────────────┘
                         │
        ┌────────────────▼────────────────────────────────┐
        │         Speech Analysis Pipeline                │
        │  (app/services/pipeline.py)                     │
        └────────┬───────────────────────┬────────────────┘
                 │                       │
        ┌────────▼────────┐     ┌────────▼────────┐
        │ Basic Pipeline  │     │Advanced Pipeline│
        │(analyzer.py)    │     │(analyzer_...py) │
        └────────┬────────┘     └────────┬────────┘
                 │                       │
        ┌────────▼───────────────────────▼────────────────┐
        │          Core Analysis Services                 │
        ├───────────────────────────────────────────────────┤
        │ ├─ Transcriber (Whisper/faster-whisper)         │
        │ ├─ Audio Extractor (FFmpeg)                     │
        │ ├─ VAD (Voice Activity Detection)               │
        │ ├─ Filler Word Analyzer                         │
        │ ├─ Pause Detector                               │
        │ ├─ GigaChat Integration (Optional)              │
        │ └─ Analytics & Caching                          │
        └────────────┬──────────────────────────────────────┘
                     │
        ┌────────────▼──────────────────────────────────────┐
        │         Infrastructure Services                  │
        ├────────────────────────────────────────────────────┤
        │ ├─ Configuration Management                      │
        │ ├─ Logging & Monitoring                          │
        │ ├─ Error Handling                                │
        │ ├─ Cache Management                              │
        │ └─ Metrics Collection                            │
        └─────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
app/
├── __init__.py
├── main.py                    # FastAPI application entry point
│
├── api/                       # API routes
│   ├── deps.py               # Dependency injection
│   └── routes/
│       ├── analysis.py       # Analysis endpoints
│       ├── chat.py           # Chat endpoints
│       └── health.py         # Health check endpoints
│
├── core/                      # Core application logic
│   ├── config.py             # Settings & configuration
│   ├── exceptions.py         # Custom exceptions
│   ├── lifespan.py           # Application lifecycle
│   ├── logging_config.py     # Logging setup
│   └── validators.py         # File validators
│
├── models/                    # Pydantic data models
│   ├── analysis.py           # Analysis result models
│   ├── gigachat.py           # GigaChat response models
│   ├── gigachat_advanced.py  # Advanced GigaChat models
│   ├── timed_analysis.py     # Timed analysis models
│   ├── timed_models.py       # Detailed timing models
│   ├── transcriber.py        # Transcription models
│   └── transcript.py         # Transcript models
│
├── services/                  # Business logic services
│   ├── analyzer.py           # Basic speech analysis
│   ├── analyzer_advanced.py  # Advanced speech analysis
│   ├── audio_extractor.py    # Audio extraction (basic)
│   ├── audio_extractor_advanced.py # Advanced extraction
│   ├── cache.py              # Caching service
│   ├── contextual_filler_analyzer.py # Contextual filler detection
│   ├── gigachat.py           # GigaChat API client
│   ├── gigachat_advanced.py  # Advanced GigaChat integration
│   ├── metrics_collector.py  # Metrics collection
│   ├── pipeline.py           # Analysis pipeline
│   ├── pipeline_advanced.py  # Advanced analysis pipeline
│   ├── transcriber.py        # Speech-to-text service
│   └── vad.py                # Voice activity detection
│
└── templates/                 # HTML templates
    └── chat.html             # Chat UI template
```

---

## Key Components

### 1. **FastAPI Application** (`app/main.py`)
- Entry point for all requests
- Exception handlers for different error types
- CORS middleware configuration
- Route registration

### 2. **API Routes** (`app/api/routes/`)
- **analysis.py**: Speech analysis endpoints
- **chat.py**: GigaChat integration endpoints
- **health.py**: Health check and metrics endpoints

### 3. **Speech Analysis Pipeline** (`app/services/pipeline.py`)
```
Video File
    ↓
Extract Audio (FFmpeg)
    ↓
Normalize Audio (16kHz mono)
    ↓
Speech Recognition (Whisper)
    ↓
Speech Analysis (Analyzer)
    ├─ Filler words detection
    ├─ Pause detection
    ├─ Speech rate calculation
    └─ Quality metrics
    ↓
Optional: GigaChat Analysis
    ↓
Results
```

### 4. **Core Services**

#### Transcriber (`services/transcriber.py`)
- Uses faster-whisper for efficient speech recognition
- Supports multiple model sizes (tiny to large)
- Caches results to avoid reprocessing
- Handles audio files and streams

#### Audio Extractor (`services/audio_extractor.py`)
- Uses FFmpeg to extract audio from video
- Converts to standardized format (16kHz mono WAV)
- Optimizes for Whisper input
- Cleans up temporary files

#### Voice Activity Detection (`services/vad.py`)
- Detects speaking vs non-speaking segments
- Filters out silent pauses
- Uses WebRTC VAD engine
- Configurable sensitivity

#### Analyzer (`services/analyzer.py`)
- Detects filler words (ээ, мм, вот, и т.д.)
- Identifies pauses and long silences
- Calculates speech rate (words per minute)
- Generates recommendations

#### GigaChat Integration (`services/gigachat.py`)
- Optional AI-powered speech analysis
- Provides detailed feedback
- Sends analysis results to GigaChat API
- Handles authentication and token management

### 5. **Configuration Management** (`core/config.py`)
- Pydantic-based settings
- Environment variable support
- Field validation
- Secure secrets handling

### 6. **Caching** (`services/cache.py`)
- Redis/File-based caching
- TTL support
- Cache invalidation strategies
- Performance metrics

---

## Data Flow

### Analysis Request Flow
```
1. Client sends video file
   ↓
2. API validates file (size, format, extensions)
   ↓
3. Pipeline extracts audio using FFmpeg
   ↓
4. Audio normalized to 16kHz mono WAV
   ↓
5. Whisper transcribes audio to text
   ↓
6. Analyzer processes transcript:
   - Finds filler words
   - Detects pauses
   - Calculates metrics
   ↓
7. Optional: Send to GigaChat for AI analysis
   ↓
8. Return results with recommendations
   ↓
9. Results cached for future requests
```

### Response Structure
```json
{
  "duration_sec": 120.5,
  "speaking_time_sec": 95.2,
  "words_per_minute": 107.3,
  "filler_words": { ... },
  "pauses": { ... },
  "advice": [ ... ],
  "transcript": "...",
  "timed_data": {
    "words": [ ... ],
    "fillers": [ ... ],
    "pauses": [ ... ]
  }
}
```

---

## Error Handling

### Exception Hierarchy
```
Exception
├─ SpeechCoachException
│  ├─ FileValidationError
│  │  ├─ FileTooLargeError
│  │  └─ UnsupportedFileTypeError
│  ├─ TranscriptionError
│  ├─ AnalysisError
│  └─ GigaChatError
└─ (Other FastAPI exceptions)
```

### Error Response Format
```json
{
  "detail": "Error message",
  "error_type": "ExceptionClassName",
  "internal_error": "Additional context (if applicable)"
}
```

---

## Performance Considerations

### Optimization Strategies
1. **Caching**: Results cached with TTL
2. **Model Optimization**: Use smaller Whisper models for faster processing
3. **Async Operations**: Non-blocking I/O for HTTP requests
4. **Connection Pooling**: Reuse HTTP connections
5. **Concurrent Processing**: Process multiple requests in parallel

### Resource Limits
- Max file size: 100 MB
- Max concurrent analyses: 3-5 (configurable)
- Request timeout: 30 seconds (configurable)
- Model loading: Once at startup (lazy loading for GigaChat)

### Benchmarks
- Small video (1-2 min): ~5-10 seconds
- Medium video (5-10 min): ~15-30 seconds
- Large video (30+ min): ~60+ seconds

---

## Security Architecture

### Input Validation
- File extension whitelist
- MIME type checking
- File size limits
- Filename sanitization

### Environment Configuration
- Sensitive data in environment variables
- Pydantic SecretStr for API keys
- Default secure settings
- SSL verification enabled by default

### Error Safety
- No sensitive data in error messages
- Internal exceptions logged securely
- User-friendly error responses

### CORS
- Restricted to safe origins (localhost for dev)
- Configurable for production
- Proper HTTP method restrictions

---

## Deployment Architecture

### Development
```
Developer Machine
├─ App (uvicorn)
├─ Logs (local file)
└─ Cache (local file)
```

### Production
```
Load Balancer
    ├─ App Instance 1 (uvicorn/gunicorn)
    ├─ App Instance 2 (uvicorn/gunicorn)
    └─ App Instance N (uvicorn/gunicorn)
    │
    ├─ Redis Cache (shared)
    ├─ Log Aggregation (ELK/Datadog)
    └─ Monitoring (Prometheus/Grafana)
```

### Docker
```
Docker Image
├─ Python 3.9+
├─ FFmpeg
├─ App Code
├─ Dependencies
└─ Entry Point: uvicorn
```

---

## Technology Stack

### Core
- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation

### Speech Processing
- **faster-whisper**: Speech recognition
- **ffmpeg**: Audio extraction
- **webrtcvad**: Voice activity detection

### External Services
- **GigaChat API**: Optional AI analysis

### Development
- **pytest**: Testing framework
- **mypy**: Type checking
- **flake8**: Code linting
- **black**: Code formatting

### Infrastructure
- **Docker**: Containerization
- **Redis**: Caching (optional)
- **PostgreSQL**: Database (optional)

---

## Scalability

### Horizontal Scaling
- Stateless application (can run multiple instances)
- Shared caching layer (Redis)
- Load balancer for distribution
- Database for persistence (if added)

### Vertical Scaling
- Larger Whisper models for accuracy
- GPU support for transcription
- Increased concurrent request limits
- Memory optimization

### Rate Limiting
- Per-IP rate limiting (future)
- API key-based quotas (future)
- Request queuing (future)

---

**Last Updated**: December 19, 2025
**Version**: 1.0.0
