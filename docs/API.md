# 📡 API Documentation

Complete API reference for Speech Coach service.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently no authentication is required. For production, add API key authentication.

---

## Speech Analysis Endpoints

### 1. Quick Analysis

Analyzes video and returns basic metrics.

**Endpoint**: `POST /api/v1/analyze`

**Parameters**:
- `file` (FormData, required) - Video file (max 100 MB)

**Supported Formats**: MP4, MOV, AVI, MKV, WEBM, FLV, WMV, M4V

**Response**:
```json
{
  "duration_sec": 120.5,
  "speaking_time_sec": 95.2,
  "speaking_ratio": 0.79,
  "words_total": 850,
  "words_per_minute": 107.3,
  "filler_words": {
    "total": 12,
    "per_100_words": 1.41,
    "items": [
      {"word": "ээ", "count": 5},
      {"word": "вот", "count": 7}
    ]
  },
  "pauses": {
    "count": 45,
    "avg_sec": 1.2,
    "max_sec": 4.5,
    "long_pauses": [
      {"timestamp": 30.2, "duration": 4.5}
    ]
  },
  "advice": [
    {
      "type": "filler_words",
      "severity": "high",
      "message": "Обнаружено много слов-паразитов"
    }
  ],
  "transcript": "full text of speech..."
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "file=@speech.mp4"
```

---

### 2. Detailed Analysis

Analyzes video with complete timings for each element.

**Endpoint**: `POST /api/v1/analyze/detailed`

**Parameters**:
- `file` (FormData, required) - Video file (max 100 MB)

**Response**:
Includes all data from quick analysis plus:
```json
{
  "timeline": {
    "words": [
      {
        "word": "Привет",
        "start": 0.5,
        "end": 0.8,
        "duration": 0.3,
        "confidence": 0.95,
        "type": "word"
      }
    ],
    "fillers": [
      {
        "word": "ээ",
        "timestamp": 5.2,
        "duration": 0.4,
        "confidence": 0.85,
        "context": "перед словом 'проект'"
      }
    ],
    "pauses": [
      {
        "start": 10.5,
        "end": 12.2,
        "duration": 1.7,
        "type": "thinking"
      }
    ]
  },
  "visualization_data": {
    "speech_activity": [...],
    "intensity_profile": [...]
  }
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/analyze/detailed" \
  -F "file=@speech.mp4"
```

---

### 3. Get Supported Formats

Lists all supported video formats and requirements.

**Endpoint**: `GET /api/v1/analyze/formats`

**Response**:
```json
{
  "formats": [".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".m4v"],
  "max_size_mb": 100,
  "audio_requirements": "Audio track with speech required",
  "recommended_format": "MP4 (.mp4)",
  "notes": [
    "Files converted to 16kHz mono WAV audio",
    "Recommended duration: 1-10 minutes",
    "Minimum speech volume: -30 dB"
  ]
}
```

---

## Chat Endpoints (Optional)

Require GigaChat API configuration.

### 1. Chat UI

Returns interactive chat interface.

**Endpoint**: `GET /chat/ui`

**Response**: HTML page with chat interface

---

### 2. Send Chat Message

Sends message to AI for response.

**Endpoint**: `POST /chat`

**Body**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "How can I improve my speech?"
    }
  ]
}
```

**Response**:
```json
{
  "choices": [
    {
      "message": {
        "content": "Here are recommendations..."
      }
    }
  ]
}
```

---

### 3. Follow-up Analysis

Analyzes follow-up question about previous analysis.

**Endpoint**: `POST /chat/analyze-followup`

**Body**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "What about my filler words?"
    }
  ]
}
```

---

## Health Endpoints

### 1. Server Status

Checks if server is running.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy"
}
```

---

### 2. Metrics

Returns performance metrics.

**Endpoint**: `GET /api/v1/metrics`

**Response**:
```json
{
  "analyses_total": 42,
  "analyses_successful": 40,
  "analyses_failed": 2,
  "avg_processing_time_sec": 5.2,
  "cache_hits": 150,
  "cache_misses": 25
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid file format",
  "error_type": "UnsupportedFileTypeError"
}
```

### 413 File Too Large
```json
{
  "detail": "File size (150.5 MB) exceeds maximum (100 MB)",
  "error_type": "FileTooLargeError",
  "max_size_mb": 100
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "messages"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error",
  "error_type": "TranscriptionError"
}
```

---

## Rate Limiting

Currently no rate limiting. For production:
- Implement API key-based rate limiting
- Set limits per IP address
- Queue long-running analyses

---

## Pagination

Pagination not applicable as API processes single files.

---

## SDKs & Libraries

### Python Example
```python
import httpx

client = httpx.Client()

# Quick analysis
with open("speech.mp4", "rb") as f:
    response = client.post(
        "http://localhost:8000/api/v1/analyze",
        files={"file": f}
    )
result = response.json()
print(f"Words per minute: {result['words_per_minute']}")
```

### JavaScript/Node.js Example
```javascript
const formData = new FormData();
formData.append("file", fileInput.files[0]);

const response = await fetch(
  "http://localhost:8000/api/v1/analyze",
  {
    method: "POST",
    body: formData
  }
);

const result = await response.json();
console.log(`WPM: ${result.words_per_minute}`);
```

### cURL Example
```bash
# Quick analysis
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@speech.mp4" | jq '.'

# Detailed analysis
curl -X POST "http://localhost:8000/api/v1/analyze/detailed" \
  -F "file=@speech.mp4" | jq '.'

# Get metrics
curl "http://localhost:8000/api/v1/metrics" | jq '.'
```

---

## Async Considerations

All endpoints are async and support concurrent requests:

```python
import asyncio
import httpx

async def analyze_multiple(files):
    async with httpx.AsyncClient() as client:
        tasks = []
        for file in files:
            with open(file, "rb") as f:
                task = client.post(
                    "http://localhost:8000/api/v1/analyze",
                    files={"file": f}
                )
                tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results
```

---

## Testing the API

### Using Postman
1. Create POST request to `http://localhost:8000/api/v1/analyze`
2. Set Body to Form Data
3. Add key `file` of type File
4. Select your video file
5. Send request

### Using Python Requests
```python
import requests

files = {"file": open("speech.mp4", "rb")}
response = requests.post(
    "http://localhost:8000/api/v1/analyze",
    files=files
)
print(response.json())
```

---

## Changelog

### v1.0.0 (Current)
- ✅ Basic speech analysis
- ✅ Detailed timeline analysis
- ✅ Optional GigaChat integration
- ✅ Caching support
- ✅ Metrics collection

### Future Versions
- Batch processing
- Real-time streaming analysis
- Advanced visualization
- Custom analysis templates

---

**Last Updated**: December 19, 2025
**API Version**: 1.0.0
