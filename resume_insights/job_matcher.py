from typing import List
from models import JobSkill
from resume_insights.utils import clean_llm_response

class JobMatcher:
    """
    Class for matching candidate skills to job requirements.
    """
    
    def __init__(self, query_engine):
        """
        Initialize the job matcher.
        
        Args:
            query_engine: The query engine to use for matching
        """
        self.query_engine = query_engine
        
    def match_job_to_skills(self, skills: List[str], job_position: str, company: str) -> JobSkill:
        """
        Match candidate skills to a specific job position.
        
        Args:
            skills: List of candidate skills
            job_position: The job position title
            company: The company name
            
        Returns:
            JobSkill: Object containing skill relevance information
        """
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
        cleaned_output = clean_llm_response(str(output))
        return JobSkill.model_validate_json(cleaned_output)