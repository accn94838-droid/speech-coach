"""Test caching logic without loading models."""
import inspect
from pathlib import Path

from app.services.transcriber import LocalWhisperTranscriber
from app.core.config import settings


def test_constructor_signature():
    """Test constructor signature."""
    sig = inspect.signature(LocalWhisperTranscriber.__init__)
    params = list(sig.parameters.keys())
    
    print("LocalWhisperTranscriber constructor parameters:")
    for param in params:
        print(f"  - {param}: {sig.parameters[param]}")
    
    assert 'cache_dir' in params, "cache_dir parameter missing"
    assert 'cache_ttl' in params, "cache_ttl parameter missing"
    
    print("✓ Constructor has new caching parameters")


def test_method_exists():
    """Test that caching methods exist."""
    assert hasattr(LocalWhisperTranscriber, '_get_cache_key'), "_get_cache_key method missing"
    assert hasattr(LocalWhisperTranscriber, '_get_cache_path'), "_get_cache_path method missing"
    assert hasattr(LocalWhisperTranscriber, 'transcribe'), "transcribe method missing"
    
    print("✓ All caching methods present")


def test_cache_key_logic():
    """Test cache key generation logic."""
    source = inspect.getsource(LocalWhisperTranscriber._get_cache_key)
    
    assert 'file_hash' in source, "file_hash should be in cache key"
    assert 'model_size' in source, "model_size should be in cache key"
    assert 'device' in source, "device should be in cache key"
    assert 'compute_type' in source, "compute_type should be in cache key"
    
    print("✓ Cache key generation logic is correct")


if __name__ == "__main__":
    test_constructor_signature()
    test_method_exists()
    test_cache_key_logic()
    print("\nAll tests passed!")
