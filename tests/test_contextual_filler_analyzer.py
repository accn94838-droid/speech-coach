"""Test for contextual filler word analysis."""
import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.services.contextual_filler_analyzer import ContextualFillerAnalyzer
from app.models.transcript import Transcript, WordTiming, TranscriptSegment
from app.services.gigachat import GigaChatClient
from app.services.cache import AnalysisCache


def test_contextual_filler_analyzer():
    """Test contextual filler word analysis."""
    
    # Create mock GigaChat client
    mock_gigachat = AsyncMock(spec=GigaChatClient)
    mock_gigachat.classify_fillers_context = AsyncMock()
    
    # Create cache mock
    mock_cache = MagicMock(spec=AnalysisCache)
    
    # Create analyzer
    analyzer = ContextualFillerAnalyzer(mock_gigachat, mock_cache)
    
    # Create test transcript
    word_timings = [
        WordTiming(word="Привет", start=0.0, end=0.5, confidence=0.9),
        WordTiming(word="я", start=0.5, end=0.7, confidence=0.95),
        WordTiming(word="хочу", start=0.7, end=1.0, confidence=0.85),
        WordTiming(word="рассказать", start=1.0, end=1.5, confidence=0.9),
        WordTiming(word="вот", start=1.5, end=1.7, confidence=0.6),
        WordTiming(word="о", start=1.7, end=1.9, confidence=0.8),
        WordTiming(word="проекте", start=1.9, end=2.3, confidence=0.88),
        WordTiming(word="ээ", start=2.3, end=2.6, confidence=0.4),
        WordTiming(word="который", start=2.6, end=3.0, confidence=0.85),
    ]
    
    transcript = Transcript(
        segments=[TranscriptSegment(start=0.0, end=3.0, text="Привет я хочу рассказать вот о проекте ээ который")],
        text="Привет я хочу рассказать вот о проекте ээ который",
        word_timings=word_timings
    )
    
    # Setup mock response
    mock_gigachat.classify_fillers_context.return_value = [
        {
            "word": "вот",
            "exact_word": "вот",
            "timestamp": 1.5,
            "confidence": 0.6,
            "duration": 0.2,
            "is_filler_context": False,
            "score": 0.3
        }
    ]
    
    async def run_test():
        result = await analyzer.analyze_fillers_with_context(transcript)
        print(f"Found fillers: {len(result)}")
        return result
    
    result = asyncio.run(run_test())
    assert result is not None
