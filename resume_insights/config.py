import os
import sys
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter

# Environment variables
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
LLAMA_CLOUD_API_KEY = os.environ.get("LLAMA_CLOUD_API_KEY")

def configure_settings():
    """
    Configures the global settings for the index such as LLM query model and embedding model.
    Exits gracefully if required API keys are not present.
    """
    # Check for required API keys
    missing_keys = []
    
    if not GOOGLE_API_KEY:
        missing_keys.append("GOOGLE_API_KEY")
    
    if not LLAMA_CLOUD_API_KEY:
        missing_keys.append("LLAMA_CLOUD_API_KEY")
    
    if missing_keys:
        print(f"Error: The following environment variable(s) are not set: {', '.join(missing_keys)}")
        print("Please set these environment variables and try again.")
        sys.exit(1)
        
    # LLM query model and embedding model definition
    llm = GoogleGenAI(model="models/gemini-1.5-flash-002", api_key=GOOGLE_API_KEY)
    embed_model = GoogleGenAIEmbedding(model_name="models/text-embedding-004", api_key=GOOGLE_API_KEY)

    # Text Splitter strategy
    sentence_splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=20)

    # Global Settings
    Settings.embed_model = embed_model
    Settings.llm = llm
    Settings.node_parser = sentence_splitter