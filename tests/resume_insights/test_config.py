import pytest
from unittest.mock import patch, MagicMock
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.llms import LLM
from llama_index.core.embeddings import BaseEmbedding

from resume_insights.config import configure_settings


@pytest.fixture
def mock_genai():
    """Fixture for mocking GoogleGenAI."""
    with patch("resume_insights.config.GoogleGenAI") as mock:
        mock_llm_instance = MagicMock(spec=LLM)
        mock_llm_instance.model = "models/gemini-1.5-flash-002"
        mock.return_value = mock_llm_instance
        yield mock


@pytest.fixture
def mock_embedding():
    """Fixture for mocking GoogleGenAIEmbedding."""
    with patch("resume_insights.config.GoogleGenAIEmbedding") as mock:
        mock_embed_instance = MagicMock(spec=BaseEmbedding)
        mock_embed_instance.model_name = "models/text-embedding-004"
        mock.return_value = mock_embed_instance
        yield mock


@pytest.fixture
def mock_api_keys():
    """Fixture for mocking API keys with valid values."""
    with patch("resume_insights.config.GOOGLE_API_KEY", "fake_key"), \
         patch("resume_insights.config.LLAMA_CLOUD_API_KEY", "fake_key"):
        yield


@pytest.fixture
def mock_missing_api_keys():
    """Fixture for mocking missing API keys."""
    with patch("resume_insights.config.GOOGLE_API_KEY", None), \
         patch("resume_insights.config.LLAMA_CLOUD_API_KEY", None), \
         patch("sys.exit") as mock_exit:
        yield mock_exit


@pytest.fixture
def mock_missing_google_api_key():
    """Fixture for mocking missing Google API key."""
    with patch("resume_insights.config.GOOGLE_API_KEY", None), \
         patch("resume_insights.config.LLAMA_CLOUD_API_KEY", "fake_key"), \
         patch("sys.exit") as mock_exit:
        yield mock_exit


@pytest.fixture
def mock_missing_llama_api_key():
    """Fixture for mocking missing Llama API key."""
    with patch("resume_insights.config.GOOGLE_API_KEY", "fake_key"), \
         patch("resume_insights.config.LLAMA_CLOUD_API_KEY", None), \
         patch("sys.exit") as mock_exit:
        yield mock_exit


def test_configure_settings_llm(mock_genai, mock_embedding, mock_api_keys):
    """Test that the LLM is properly configured."""
    configure_settings()

    # Verify the mock was called with correct parameters
    mock_genai.assert_called_once_with(
        model="models/gemini-1.5-flash-002", api_key="fake_key"
    )
    assert Settings.llm == mock_genai.return_value


def test_configure_settings_embed_model(mock_genai, mock_embedding, mock_api_keys):
    """Test that the embedding model is properly configured."""
    configure_settings()

    # Verify the mock was called with correct parameters
    mock_embedding.assert_called_once_with(
        model_name="models/text-embedding-004", api_key="fake_key"
    )
    assert Settings.embed_model == mock_embedding.return_value


def test_configure_settings_node_parser(mock_genai, mock_embedding, mock_api_keys):
    """Test that the node parser is properly configured."""
    configure_settings()

    assert isinstance(Settings.node_parser, SentenceSplitter)
    assert Settings.node_parser.chunk_size == 1024
    assert Settings.node_parser.chunk_overlap == 20


# New tests for graceful exit when API keys are missing
def test_exit_when_both_api_keys_missing(mock_genai, mock_embedding, mock_missing_api_keys):
    """Test that the application exits when both API keys are missing."""
    # Call the function we're testing
    configure_settings()

    # Assert that sys.exit was called with exit code 1
    mock_missing_api_keys.assert_called_once_with(1)


def test_exit_when_google_api_key_missing(mock_genai, mock_embedding, mock_missing_google_api_key):
    """Test that the application exits when Google API key is missing."""
    configure_settings()
    mock_missing_google_api_key.assert_called_once_with(1)


def test_exit_when_llama_api_key_missing(mock_genai, mock_embedding, mock_missing_llama_api_key):
    """Test that the application exits when Llama API key is missing."""
    configure_settings()

    mock_missing_llama_api_key.assert_called_once_with(1)
