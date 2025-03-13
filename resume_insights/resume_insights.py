from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.readers.base import BaseReader
from llama_cloud_services import LlamaParse
from llama_cloud_services.parse import ResultType

from typing import List, Dict, cast

from models import Candidate, JobSkill
from resume_insights.config import LLAMA_CLOUD_API_KEY, configure_settings
from resume_insights.utils import clean_llm_response
from resume_insights.skill_analyzer import SkillAnalyzer
from resume_insights.work_history_analyzer import WorkHistoryAnalyzer
from resume_insights.job_matcher import JobMatcher


class ResumeInsights:
    def __init__(self, file_path):
        configure_settings()
        self.query_engine = self._create_query_engine(file_path)
        self.skill_analyzer = SkillAnalyzer(self.query_engine)
        self.work_history_analyzer = WorkHistoryAnalyzer(self.query_engine)
        self.job_matcher = JobMatcher(self.query_engine)

    def extract_candidate_data(self) -> Candidate:
        """
        Extracts candidate data from the resume.

        Returns:
            Candidate: The extracted candidate data.
        """

        # Extract work history first to use for skill analysis
        work_history = self.work_history_analyzer.extract_work_history()

        # Extract resume text
        resume_text = self.work_history_analyzer.extract_resume_text()

        # Extract detailed skills
        skills_with_details = self.skill_analyzer.extract_skills_with_details(
            resume_text, work_history
        )

        # Parse candidate data from the resume
        candidate = self._parse_candidate_data()

        # Update the candidate with detailed skills
        candidate.skills = skills_with_details

        return candidate
        
    def _parse_candidate_data(self) -> Candidate:
        """
        Parses basic candidate data from the resume using the Candidate schema.
        
        Returns:
            Candidate: The parsed candidate data without detailed skills.
        """
        # Output Schema
        output_schema = Candidate.model_json_schema()

        # Schema-driven prompt
        prompt = f"""
                Analyze the resume and extract information according to this JSON schema:
                {output_schema}
                
                Return a valid JSON object that strictly follows the provided schema structure.
                Do not include any explanations or markdown formatting in your response.
                """

        # Text output
        output = self.query_engine.query(prompt)
        # Parse the response
        cleaned_output = clean_llm_response(str(output))
        print(cleaned_output)
        return Candidate.model_validate_json(cleaned_output)

    def match_job_to_skills(
        self, skills: List[str], job_position: str, company: str
    ) -> JobSkill:
        """
        Match candidate skills to a specific job position.

        Args:
            skills: List of candidate skills
            job_position: The job position title
            company: The company name

        Returns:
            JobSkill: Object containing skill relevance information
        """
        return self.job_matcher.match_job_to_skills(skills, job_position, company)

    def _create_query_engine(self, file_path: str):
        """
        Creates a query engine from a file path.

        Args:
            file_path (str): The path to the file.

        Returns:
            The created query engine.
        """

        # Make sure LLAMA_CLOUD_API_KEY is defined and not None
        if LLAMA_CLOUD_API_KEY is None:
            raise ValueError("LLAMA_CLOUD_API_KEY is not set")

        # Parser
        parser = LlamaParse(
            result_type=ResultType.TXT,  # "markdown" and "text" are available
            api_key=LLAMA_CLOUD_API_KEY,
            # verbose=True,
        )

        file_extractor = {
            ".pdf": parser,
            # Add other file types as needed
        }

        # Reader
        documents = SimpleDirectoryReader(
            input_files=[file_path],
            file_extractor=cast(Dict[str, BaseReader], file_extractor),
        ).load_data()

        # Vector index
        index = VectorStoreIndex.from_documents(documents)
        # Query Engine
        return index.as_query_engine()


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
# https://pypi.org/project/llama-index-llms-google-genai/
# https://pypi.org/project/llama-index-embeddings-google-genai/
