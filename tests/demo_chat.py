"""Demo script for GigaChat chat functionality."""
import asyncio
from unittest.mock import AsyncMock

from app.api.routes.chat import ChatRequest, ChatMessage
from app.services.gigachat import GigaChatClient


async def demonstrate_chat_functionality():
    """Demonstrate GigaChat chat functionality."""
    print("GigaChat Chat Demonstration")
    print("=" * 50)
    
    # Create mock client for demonstration
    mock_client = AsyncMock()
    mock_client._access_token = "demo_token_12345"
    mock_client.api_url = "https://demo-gigachat-api.com"
    mock_client.model = "gigachat:latest"
    mock_client.max_tokens = 1000
    mock_client.authenticate = AsyncMock()
    mock_client.client = AsyncMock()
    
    # Setup mock response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Hello! I'm GigaChat and ready to help you improve your public speaking skills."
                }
            }
        ],
        "usage": {
            "total_tokens": 15
        }
    }
    mock_client.client.post = AsyncMock(return_value=mock_response)
    
    print("1. Simulating authentication...")
    await mock_client.authenticate()
    print(f"   Token: {mock_client._access_token[:10]}...")
    
    print("\n2. Preparing messages...")
    chat_request = ChatRequest(
        messages=[
            ChatMessage(role="user", content="How can I improve my public speaking?")
        ]
    )
    print(f"   Message count: {len(chat_request.messages)}")
    
    print("\n3. Simulating API request...")
    print(f"   API URL: {mock_client.api_url}")
    print(f"   Model: {mock_client.model}")
    print(f"   Max tokens: {mock_client.max_tokens}")
    
    print("\n4. Simulating API response...")
    response = await mock_client.client.post()
    data = response.json()
    print(f"   Status: {response.status_code}")
    print(f"   Response: {data['choices'][0]['message']['content'][:50]}...")
    print(f"   Tokens used: {data['usage']['total_tokens']}")
    
    print("\n✓ Chat demonstration completed successfully")


if __name__ == "__main__":
    asyncio.run(demonstrate_chat_functionality())
