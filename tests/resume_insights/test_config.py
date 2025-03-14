from unittest.mock import patch
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter

from resume_insights.config import configure_settings

@patch('resume_insights.config.GOOGLE_API_KEY', 'fake_key')
@patch('resume_insights.config.LLAMA_CLOUD_API_KEY', 'fake_key')
def test_configure_settings_llm():
    configure_settings()
    assert isinstance(Settings.llm, GoogleGenAI)
    assert Settings.llm.model == "models/gemini-1.5-flash-002"

def test_configure_settings_embed_model():
    configure_settings()
    assert isinstance(Settings.embed_model, GoogleGenAIEmbedding)
    assert Settings.embed_model.model_name == "models/text-embedding-004"

def test_configure_settings_node_parser():
    configure_settings()
    assert isinstance(Settings.node_parser, SentenceSplitter)
    assert Settings.node_parser.chunk_size == 1024
    assert Settings.node_parser.chunk_overlap == 20

# New tests for graceful exit when API keys are missing
@patch('resume_insights.config.GOOGLE_API_KEY', None)
@patch('resume_insights.config.LLAMA_CLOUD_API_KEY', None)
@patch('sys.exit')
def test_exit_when_both_api_keys_missing(mock_exit):
    """Test that the application exits when both API keys are missing."""
    # Call the function we're testing
    configure_settings()

    # Assert that sys.exit was called with exit code 1
    mock_exit.assert_called_once_with(1)

@patch('resume_insights.config.GOOGLE_API_KEY', None)
@patch('resume_insights.config.LLAMA_CLOUD_API_KEY', 'fake_key')
@patch('sys.exit')
def test_exit_when_google_api_key_missing(mock_exit):
    """Test that the application exits when Google API key is missing."""
    configure_settings()
    mock_exit.assert_called_once_with(1)

@patch('resume_insights.config.GOOGLE_API_KEY', 'fake_key')
@patch('resume_insights.config.LLAMA_CLOUD_API_KEY', None)
@patch('sys.exit')
def test_exit_when_llama_api_key_missing(mock_exit):
    """Test that the application exits when Llama API key is missing."""
    configure_settings()
    mock_exit.assert_called_once_with(1)



