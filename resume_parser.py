from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core import (
    Settings,
    VectorStoreIndex,
    SimpleDirectoryReader,
)
from llama_parse import LlamaParse
from llama_index.core.node_parser import SentenceSplitter

import os

from models import Candidate

GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
LLAMA_CLOUD_API_KEY = os.environ["LLAMA_CLOUD_API_KEY"]

# LLM query model and embedding model definition
llm = Gemini(model_name="models/gemini-1.5-flash-002", api_key=GOOGLE_API_KEY)
embed_model = GeminiEmbedding(
    model_name="models/text-embedding-004", api_key=GOOGLE_API_KEY
)


def get_insights(file):
    # Text Splitter strategy
    sentenceSplitter = SentenceSplitter(chunk_size=1024, chunk_overlap=20)
    # sentenceSplitter.get_nodes_from_documents(documents)

    # Global Settings
    Settings.embed_model = embed_model
    Settings.llm = llm  # .as_structured_llm(output_cls=Candidate)
    Settings.node_parser = sentenceSplitter

    # Output Schema
    output_schema = Candidate.model_json_schema()

    # Prompt
    prompt = f"""
            Extract the following information from the resume:
            {output_schema}
            Provide the result in a structured JSON format. Please remove any ```json ``` characters from the output.
            """

    # Parser
    parser = LlamaParse(
        result_type="text",  # "markdown" and "text" are available
        api_key=LLAMA_CLOUD_API_KEY,
        verbose=True,
    )
    file_extractor = {".pdf": parser}

    # Reader
    documents = SimpleDirectoryReader(
        input_files=[file], file_extractor=file_extractor
    ).load_data()

    # Vector index
    index = VectorStoreIndex.from_documents(documents)
    # Query Engine
    query_engine = index.as_query_engine()
    # Text output
    output = query_engine.query(prompt)
    # JSON output
    # data = json.loads(output.response)
    # Pydanctic model
    return Candidate.model_validate_json(output.response)


if __name__ == "__main__":
    print(get_insights("Resume.pdf"))


# Resources
# https://docs.llamaindex.ai/en/stable/examples/structured_outputs/structured_outputs/
# https://docs.llamaindex.ai/en/stable/module_guides/querying/structured_outputs/pydantic_program/
# https://docs.llamaindex.ai/en/stable/examples/node_parsers/semantic_chunking/
# https://docs.llamaindex.ai/en/stable/module_guides/indexing/vector_store_index/
# https://docs.llamaindex.ai/en/stable/examples/metadata_extraction/PydanticExtractor/
# https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/
# https://github.com/run-llama/llama_index/discussions/13271
# https://www.llamaindex.ai/blog/introducing-llamaextract-beta-structured-data-extraction-in-just-a-few-clicks
