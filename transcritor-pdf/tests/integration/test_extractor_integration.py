import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image

from src.extractor import text_extractor
from src.extractor import llm_client # To get to _llm_client for reset
from src.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI # For spec

# Mark all tests in this file as asyncio by default if most are async
# Individual sync tests can be marked or left unmarked if default is already sync
# pytestmark = pytest.mark.asyncio # Not strictly needed if tests are decorated

@pytest.fixture
def mock_llm_client_for_text_extractor(mocker): # Renamed for clarity
    """Fixture to mock the LLM client specifically for text_extractor tests."""
    mock_client_instance = AsyncMock(spec=ChatGoogleGenerativeAI)

    mock_response = MagicMock()
    mock_response.content = "Successfully extracted text from image."
    mock_client_instance.invoke.return_value = mock_response

    # Patch get_llm_client where it's *looked up* by text_extractor.py
    mocker.patch('src.extractor.text_extractor.get_llm_client', return_value=mock_client_instance)
    return mock_client_instance

@pytest.fixture
def mock_settings_with_valid_api_key(mocker):
    """Fixture to temporarily patch settings GOOGLE_API_KEY for relevant tests."""
    with patch.object(settings, 'GOOGLE_API_KEY', 'DUMMY_API_KEY_FOR_TESTING_PURPOSES') as p:
        yield p

@pytest.fixture
def sample_image():
    """Fixture to create a dummy PIL Image for testing."""
    img = Image.new('RGB', (60, 30), color = 'red')
    return img

@pytest.mark.asyncio
async def test_extract_text_from_image_success(mock_llm_client_for_text_extractor, sample_image, mock_settings_with_valid_api_key):
    extracted_text = text_extractor.extract_text_from_image(sample_image)
    assert extracted_text == "Successfully extracted text from image."
    mock_llm_client_for_text_extractor.invoke.assert_called_once()
    args, _ = mock_llm_client_for_text_extractor.invoke.call_args
    messages_list = args[0]
    assert len(messages_list) == 1
    human_message_content = messages_list[0].content
    assert isinstance(human_message_content, list)
    assert any(item.get("type") == "text" for item in human_message_content)
    assert any(item.get("type") == "image_url" for item in human_message_content)
    assert "data:image/webp;base64," in human_message_content[1]["image_url"]["url"]

@pytest.mark.asyncio
async def test_extract_text_from_image_llm_returns_none(mock_llm_client_for_text_extractor, sample_image, mock_settings_with_valid_api_key):
    mock_response = MagicMock()
    mock_response.content = None
    mock_llm_client_for_text_extractor.invoke.return_value = mock_response
    extracted_text = text_extractor.extract_text_from_image(sample_image)
    assert extracted_text is None

@pytest.mark.asyncio
async def test_extract_text_from_image_llm_unexpected_response(mock_llm_client_for_text_extractor, sample_image, mock_settings_with_valid_api_key):
    mock_llm_client_for_text_extractor.invoke.return_value = "just a string"
    extracted_text = text_extractor.extract_text_from_image(sample_image)
    assert extracted_text is None

@pytest.mark.asyncio
async def test_extract_text_from_image_encoding_error(sample_image, mocker, mock_settings_with_valid_api_key):
    mocker.patch('src.extractor.text_extractor.encode_image_to_base64', side_effect=Exception("Encoding failed"))
    extracted_text = text_extractor.extract_text_from_image(sample_image)
    assert extracted_text is None

@pytest.mark.asyncio
async def test_extract_text_from_image_llm_api_error(mock_llm_client_for_text_extractor, sample_image, mock_settings_with_valid_api_key):
    # Ensure _invoke_llm_with_retry is patched where it's defined and used
    with patch('src.extractor.text_extractor._invoke_llm_with_retry', side_effect=Exception("LLM API call failed after retries")):
        extracted_text = text_extractor.extract_text_from_image(sample_image)
        assert extracted_text is None

# This is the corrected synchronous test for get_llm_client behavior
def test_get_llm_client_initialization_and_singleton_behavior(mocker):
    """Test the singleton behavior and correct initialization of get_llm_client."""

    mocker.patch.object(settings, 'GOOGLE_API_KEY', 'key_for_singleton_test_sync')
    mocker.patch.object(settings, 'GEMINI_CHAT_MODEL_NAME', 'model_for_singleton_test_sync')

    # Patch ChatGoogleGenerativeAI where it's imported and used in llm_client.py
    MockChatGoogleClass = mocker.patch('src.extractor.llm_client.ChatGoogleGenerativeAI')

    mock_instance = MagicMock(spec=ChatGoogleGenerativeAI)
    MockChatGoogleClass.return_value = mock_instance

    # Reset the global _llm_client in the llm_client module for a clean test
    if hasattr(llm_client, '_llm_client'): # Check if attribute exists
        llm_client._llm_client = None

    client1 = llm_client.get_llm_client()

    MockChatGoogleClass.assert_called_once_with(
        model='model_for_singleton_test_sync',
        google_api_key='key_for_singleton_test_sync'
    )
    assert client1 == mock_instance

    client2 = llm_client.get_llm_client()
    assert client1 is client2
    MockChatGoogleClass.assert_called_once()
