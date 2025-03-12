import os
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
    """
    # LLM query model and embedding model definition
    llm = GoogleGenAI(model="models/gemini-1.5-flash-002")
    embed_model = GoogleGenAIEmbedding(model_name="models/text-embedding-004")

    # Text Splitter strategy
    sentence_splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=20)

    # Global Settings
    Settings.embed_model = embed_model
    Settings.llm = llm
    Settings.node_parser = sentence_splitter