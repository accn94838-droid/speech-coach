"""
Optional, lazy service exports.

Many services depend on heavy ML libraries (Whisper, PyTorch, pyannote, etc.).
To allow running unit tests and importing lightweight parts of the package
without installing all heavy dependencies, we import optional modules inside
try/except blocks and only expose what is available.
"""

from importlib import import_module
import logging

logger = logging.getLogger(__name__)

# Core (lightweight) services that should always be available
from app.services.cache import AnalysisCache, cache_analysis
from app.services.analyzer import SpeechAnalyzer, EnhancedAnalysisResult
from app.services.metrics_collector import MetricsCollector, ProcessingMetrics
from app.services.gigachat import GigaChatClient, GigaChatError

# Optional / heavy services: import if available, otherwise log a warning
try:
    mod = import_module('app.services.audio_extractor')
    AudioExtractor = getattr(mod, 'AudioExtractor')
    FfmpegAudioExtractor = getattr(mod, 'FfmpegAudioExtractor')
except Exception as e:
    logger.debug(f"Optional module app.services.audio_extractor not available: {e}")
    AudioExtractor = None
    FfmpegAudioExtractor = None

try:
    mod = import_module('app.services.audio_extractor_advanced')
    AdvancedFfmpegAudioExtractor = getattr(mod, 'AdvancedFfmpegAudioExtractor')
    TimeoutException = getattr(mod, 'TimeoutException')
except Exception as e:
    logger.debug(f"Optional module app.services.audio_extractor_advanced not available: {e}")
    AdvancedFfmpegAudioExtractor = None
    TimeoutException = None

try:
    mod = import_module('app.services.transcriber')
    Transcriber = getattr(mod, 'Transcriber')
    LocalWhisperTranscriber = getattr(mod, 'LocalWhisperTranscriber')
except Exception as e:
    logger.debug(f"Optional module app.services.transcriber not available: {e}")
    Transcriber = None
    LocalWhisperTranscriber = None

try:
    mod = import_module('app.services.analyzer_advanced')
    AdvancedSpeechAnalyzer = getattr(mod, 'AdvancedSpeechAnalyzer')
except Exception as e:
    logger.debug(f"Optional module app.services.analyzer_advanced not available: {e}")
    AdvancedSpeechAnalyzer = None

try:
    mod = import_module('app.services.pipeline')
    SpeechAnalysisPipeline = getattr(mod, 'SpeechAnalysisPipeline')
except Exception as e:
    logger.debug(f"Optional module app.services.pipeline not available: {e}")
    SpeechAnalysisPipeline = None

try:
    mod = import_module('app.services.pipeline_advanced')
    AdvancedSpeechAnalysisPipeline = getattr(mod, 'AdvancedSpeechAnalysisPipeline')
except Exception as e:
    logger.debug(f"Optional module app.services.pipeline_advanced not available: {e}")
    AdvancedSpeechAnalysisPipeline = None

try:
    mod = import_module('app.services.gigachat_advanced')
    create_enhanced_gigachat_analysis = getattr(mod, 'create_enhanced_gigachat_analysis')
    prepare_timed_result_for_gigachat = getattr(mod, 'prepare_timed_result_for_gigachat')
except Exception as e:
    logger.debug(f"Optional module app.services.gigachat_advanced not available: {e}")
    create_enhanced_gigachat_analysis = None
    prepare_timed_result_for_gigachat = None

__all__ = [
    # Cache & Metrics
    "AnalysisCache",
    "cache_analysis",
    "MetricsCollector",
    "ProcessingMetrics",

    # Analysis
    "SpeechAnalyzer",
    "EnhancedAnalysisResult",

    # GigaChat
    "GigaChatClient",
    "GigaChatError",

    # Optional / conditional exports (may be None)
    "AudioExtractor",
    "FfmpegAudioExtractor",
    "AdvancedFfmpegAudioExtractor",
    "TimeoutException",
    "Transcriber",
    "LocalWhisperTranscriber",
    "AdvancedSpeechAnalyzer",
    "SpeechAnalysisPipeline",
    "AdvancedSpeechAnalysisPipeline",
    "create_enhanced_gigachat_analysis",
    "prepare_timed_result_for_gigachat",
]
