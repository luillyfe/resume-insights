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

from models import Candidate, JobSkill

GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
LLAMA_CLOUD_API_KEY = os.environ["LLAMA_CLOUD_API_KEY"]


class ResumeInsights:
    def __init__(self, file_path):
        self._configure_settings()
        self.query_engine = self._create_query_engine(file_path)

    def extract_candidate_data(self) -> Candidate:
        """
        Extracts candidate data from the resume.

        Returns:
            Candidate: The extracted candidate data.
        """
        # Output Schema
        output_schema = Candidate.model_json_schema()

        # Prompt
        prompt = f"""
                Use the following JSON schema describing the information I need to extract.  Please extract the properties defined in the JSON schema:
                ```json
                {output_schema}
                ```json
                Provide the result in a structured JSON format. Please remove any ```json ``` characters from the output.
                """

        # Text output
        output = self.query_engine.query(prompt)
        # Pydanctic model
        return Candidate.model_validate_json(output.response)

    def match_job_to_skills(self, skills, job_position, company) -> JobSkill:
        skills_job_prompt = [
            f"""Given this skill: {skill}, please provide your reasoning for why this skill 
                    matter to the follloging job position: {job_position} at {company}.
                    if the skill is not relevant please say so.
                    Use system thinking level 3 to accomplish this task"""
            for skill in skills
        ]

        skills_job_prompt = f"""{", ".join(skills_job_prompt)}
            Please use the following schema: {JobSkill.model_json_schema()}
            Provide the result in a structured JSON format. Please remove any ```json ``` characters from the output.
            """

        output = self.query_engine.query(skills_job_prompt)
        # return json.loads(output.response)["skills"]
        return JobSkill.model_validate_json(output.response)

    def _create_query_engine(self, file_path: str):
        """
        Creates a query engine from a file path.

        Args:
            file_path (str): The path to the file.

        Returns:
            The created query engine.
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
            input_files=[file_path], file_extractor=file_extractor
        ).load_data()

        # Vector index
        index = VectorStoreIndex.from_documents(documents)
        # Query Engine
        return index.as_query_engine()

    def _configure_settings(self):
        """
        Configures the settings for the index such LLM query model and embedding model.
        """
        # LLM query model and embedding model definition
        llm = Gemini(model="models/gemini-1.5-flash-002", api_key=GOOGLE_API_KEY)
        embed_model = GeminiEmbedding(
            model_name="models/text-embedding-004", api_key=GOOGLE_API_KEY
        )

        # Text Splitter strategy
        sentenceSplitter = SentenceSplitter(chunk_size=1024, chunk_overlap=20)
        # sentenceSplitter.get_nodes_from_documents(documents)

        # Global Settings
        Settings.embed_model = embed_model
        Settings.llm = llm  # .as_structured_llm(output_cls=Candidate)
        Settings.node_parser = sentenceSplitter


if __name__ == "__main__":
    pass


# Resources
# https://docs.llamaindex.ai/en/stable/examples/structured_outputs/structured_outputs/
# https://docs.llamaindex.ai/en/stable/module_guides/querying/structured_outputs/pydantic_program/
# https://docs.llamaindex.ai/en/stable/examples/node_parsers/semantic_chunking/
# https://docs.llamaindex.ai/en/stable/module_guides/indexing/vector_store_index/
# https://docs.llamaindex.ai/en/stable/examples/metadata_extraction/PydanticExtractor/
# https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/
# https://github.com/run-llama/llama_index/discussions/13271
# https://www.llamaindex.ai/blog/introducing-llamaextract-beta-structured-data-extraction-in-just-a-few-clicks
