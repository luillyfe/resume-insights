from typing import List, Dict, Optional, cast

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.query_engine import BaseQueryEngine
from llama_index.core.readers.base import BaseReader
from llama_cloud_services import LlamaParse
from llama_cloud_services.parse import ResultType

from resume_insights.models import Candidate, JobSkill
from resume_insights.config import LLAMA_CLOUD_API_KEY, configure_settings
from resume_insights.utils import clean_llm_response
from resume_insights.skill_analyzer import SkillAnalyzer
from resume_insights.work_history_analyzer import WorkHistoryAnalyzer
from resume_insights.job_matcher import JobMatcher


class QueryEngineFactory:
    """
    Factory class for creating query engines from different file types.
    
    This class encapsulates the logic for creating query engines, making it easier
    to test and extend with new file types in the future.
    """
    
    @staticmethod
    def create_from_file(file_path: str) -> BaseQueryEngine:
        """
        Creates a query engine from a file path.

        Args:
            file_path (str): The path to the file.

        Returns:
            QueryEngine: The created query engine.
            
        Raises:
            ValueError: If the file type is not supported or if API keys are missing.
        """
        # Configure settings first
        configure_settings()
        
        # Parser
        parser = LlamaParse(
            result_type=ResultType.TXT,  # "markdown" and "text" are available
            api_key=str(LLAMA_CLOUD_API_KEY),
            # verbose=True,
        )

        file_extractor = {
            ".pdf": parser,
            # Add other file types as needed
        }

        # Reader
        try:
            documents = SimpleDirectoryReader(
                input_files=[file_path],
                file_extractor=cast(Dict[str, BaseReader], file_extractor),
            ).load_data()

            # Vector index
            index = VectorStoreIndex.from_documents(documents)
            # Query Engine
            return index.as_query_engine()
        except Exception as e:
            raise ValueError(f"Failed to create query engine: {str(e)}")


class ResumeInsights:
    """
    Main class for extracting insights from resumes.
    
    This class uses dependency injection to allow for more flexible and testable code.
    It coordinates between different analyzers to extract comprehensive information from resumes.
    """
    
    def __init__(self, 
                 query_engine: Optional[BaseQueryEngine] = None,
                 file_path: Optional[str] = None,
                 skill_analyzer: Optional[SkillAnalyzer] = None,
                 work_history_analyzer: Optional[WorkHistoryAnalyzer] = None,
                 job_matcher: Optional[JobMatcher] = None):
        """
        Initialize the ResumeInsights class.
        
        Args:
            query_engine (Optional[BaseQueryEngine]): A pre-configured query engine. If provided, file_path is ignored.
            file_path (Optional[str]): Path to the resume file. Used to create a query engine if one is not provided.
            skill_analyzer (Optional[SkillAnalyzer]): A pre-configured skill analyzer. If not provided, one will be created.
            work_history_analyzer (Optional[WorkHistoryAnalyzer]): A pre-configured work history analyzer. If not provided, one will be created.
            job_matcher (Optional[JobMatcher]): A pre-configured job matcher. If not provided, one will be created.
            
        Raises:
            ValueError: If neither query_engine nor file_path is provided.
        """
        if query_engine is None and file_path is None:
            raise ValueError("Either query_engine or file_path must be provided")
            
        # Create query engine if not provided
        if query_engine is None and file_path is not None:
            query_engine = QueryEngineFactory.create_from_file(file_path)
        
        self.query_engine = query_engine
        
        # Create analyzers if not provided
        self.skill_analyzer = skill_analyzer or SkillAnalyzer(self.query_engine)
        self.work_history_analyzer = work_history_analyzer or WorkHistoryAnalyzer(self.query_engine)
        self.job_matcher = job_matcher or JobMatcher(self.query_engine)

    def extract_candidate_data(self) -> Candidate:
        """
        Extracts candidate data from the resume.

        Returns:
            Candidate: The extracted candidate data.
            
        Raises:
            Exception: If extraction fails at any point.
        """
        try:
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
        except Exception as e:
            raise Exception(f"Failed to extract candidate data: {str(e)}")
        
    def _parse_candidate_data(self) -> Candidate:
        """
        Parses basic candidate data from the resume using the Candidate schema.
        
        Returns:
            Candidate: The parsed candidate data without detailed skills.
            
        Raises:
            ValueError: If parsing fails.
        """
        # Output Schema
        output_schema = Candidate.model_json_schema()

        # Completely schema-driven prompt
        prompt = f"""
                Thoroughly analyze the resume document and extract all relevant information.
                
                Use this JSON schema to determine what information to extract:
                {output_schema}
                
                Pay close attention to the schema's field descriptions to understand what data to extract.
                Return a complete and valid JSON object that strictly follows the provided schema structure.
                Do not include any explanations or markdown formatting in your response.
                """

        try:
            # Text output
            if self.query_engine is None:
                raise ValueError("Query engine is not initialized")
            output = self.query_engine.query(prompt)
            # Parse the response
            cleaned_output = clean_llm_response(str(output))

            return Candidate.model_validate_json(cleaned_output)
        except Exception as e:
            raise ValueError(f"Failed to parse candidate data: {str(e)}")

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
            
        Raises:
            Exception: If matching fails.
        """
        try:
            return self.job_matcher.match_job_to_skills(skills, job_position, company)
        except Exception as e:
            raise Exception(f"Failed to match job to skills: {str(e)}")


# Factory function for backward compatibility
def create_resume_insights(file_path: str) -> ResumeInsights:
    """
    Factory function to create a ResumeInsights instance from a file path.
    
    This function maintains backward compatibility with code that expects
    to create ResumeInsights by passing a file path directly.
    
    Args:
        file_path (str): Path to the resume file.
        
    Returns:
        ResumeInsights: A configured ResumeInsights instance.
    """
    return ResumeInsights(file_path=file_path)


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
