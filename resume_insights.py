from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.core import (
    Settings,
    VectorStoreIndex,
    SimpleDirectoryReader,
)
from llama_cloud_services import LlamaParse
from llama_index.core.node_parser import SentenceSplitter

import os
import re
import json
import copy
from datetime import datetime
from typing import Dict, List, Optional

from numpy import RankWarning

from models import Candidate, JobSkill, SkillDetail

os.environ["GOOGLE_API_KEY"]
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

        # Extract work history first to use for skill analysis
        work_history = self._extract_work_history()

        # Extract resume text
        resume_text = self._extract_resume_text()

        # Extract detailed skills
        skills_with_details = self.extract_skills_with_details(
            resume_text, work_history
        )

        # Prompt
        prompt = f"""
                Use the following JSON schema describing the information I need to extract:
                {output_schema}
                """

        # Text output
        output = self.query_engine.query(prompt)
        # Parse the response
        cleaned_output = self.clean_llm_response(str(output))
        candidate = Candidate.model_validate_json(cleaned_output)

        # Update the candidate with detailed skills
        candidate.skills = skills_with_details

        return candidate

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
        cleaned_output = self.clean_llm_response(str(output))
        return JobSkill.model_validate_json(cleaned_output)

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
        llm = GoogleGenAI(model="models/gemini-1.5-flash-002")
        embed_model = GoogleGenAIEmbedding(model_name="models/text-embedding-004")

        # Text Splitter strategy
        sentenceSplitter = SentenceSplitter(chunk_size=1024, chunk_overlap=20)
        # sentenceSplitter.get_nodes_from_documents(documents)

        # Global Settings
        Settings.embed_model = embed_model
        Settings.llm = llm  # .as_structured_llm(output_cls=Candidate)
        Settings.node_parser = sentenceSplitter

    def extract_skills_with_details(
        self, resume_text: str, work_history: List[Dict]
    ) -> Dict[str, SkillDetail]:
        """
        Extract skills with detailed information including categories, proficiency, and experience.

        Args:
            resume_text: The full text of the resume
            work_history: Parsed work history sections

        Returns:
            Dict[str, SkillDetail]: Dictionary of skills with their details
        """
        # 1. Extract raw skills using LLM
        raw_skills = self._extract_raw_skills()

        # 2. Categorize skills using predefined taxonomies
        categorized_skills = self._categorize_skills(raw_skills)

        # 3. Calculate experience duration by analyzing work history sections
        skills_with_experience = self._calculate_experience_duration(
            categorized_skills, work_history
        )

        # 4. Estimate proficiency based on various factors
        skills_with_proficiency = self._estimate_proficiency(
            skills_with_experience, resume_text
        )

        # 5. Find related skills
        skill_details = self._find_related_skills(skills_with_proficiency)

        return skill_details

    def _extract_raw_skills(self) -> List[str]:
        """
        Extract raw skills from resume text using LLM.

        Returns:
            List[str]: List of raw skills
        """
        prompt = """
        Given the resume text, please identify and list all technical skills, soft skills, and domain knowledge.
        Return only the list of skills without any additional text or explanations.
        """

        response_obj = self.query_engine.query(prompt)
        skills = []

        try:
            # For llama_index.core.base.response.schema.Response objects
            if hasattr(response_obj, "response"):
                skills_text = str(response_obj)

                # If the response is a string
                if isinstance(skills_text, str):
                    # Try to split it into categories if it's a multi-line string
                    categories = [
                        s.strip() for s in skills_text.split("\n") if s.strip()
                    ]
                    for category in categories:
                        # Check if the category follows the format "Category: skill1, skill2, ..."
                        if ": " in category:
                            parts = category.split(": ", 1)
                            if len(parts) == 2:
                                # Extract the skills part and split by commas
                                skills_part = parts[1]
                                category_skills = [
                                    s.strip().lstrip("-*•").strip()
                                    for s in skills_part.split(", ")
                                ]
                                skills.extend(category_skills)
                        else:
                            # If the category doesn't follow the expected format, treat the whole line as a skill
                            skills.append(category.strip().lstrip("-*•").strip())
            else:
                print(
                    f"Response object doesn't have a 'response' attribute: {type(response_obj)}"
                )

        except Exception as e:
            print(f"Error processing skills: {e}")

        return skills

    def _categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """
        Args:
        skills: List of raw skills

        Returns:
            Dict[str, Dict]: Dictionary of categorized skills
        """

        categorized_skills = {}

        prompt = f"""
        For each of the following skills, categorize it into one of these categories:
        - Programming Languages
        - Frameworks & Libraries
        - Tools & Technologies
        - Soft Skills
        - Domain Knowledge
        - Other

        Skills: {', '.join(skills)}

        For each skill, provide the category and any subcategory if applicable.
        """

        response = self.query_engine.query(prompt)
        # Parse the response to get categorized skills
        # If the response is a llama_index.core.base.response.schema.Response object:
        if hasattr(response, "response"):
            skills_text = str(response)
            # Split the text into lines and remove empty lines
            lines = [line.strip() for line in skills_text.split("\n") if line.strip()]

            # Initialize the result dictionary
            categorized_skills = {}
            current_category = None

            for line in lines:
                # Check for category headers (bold text)
                if line.startswith("**") and line.endswith(":**"):
                    # Remove the ** and : from the category name
                    current_category = line.strip("*:")
                    categorized_skills[current_category] = []

                # Check for skills (marked with *)
                elif line.startswith("* ") and current_category:
                    # Remove the * and leading/trailing whitespace
                    skill = line.lstrip("* ").strip()
                    categorized_skills[current_category].append(skill)

        return categorized_skills

    def _calculate_experience_duration(
        self, categorized_skills: Dict[str, List[str]], work_history: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """
        Calculate experience duration for each skill by analyzing work history.

        Args:
            categorized_skills: Dictionary of categorized skills
            work_history: List of work history entries with dates and descriptions

        Returns:
            Dict[str, Dict]: Skills with experience duration added
        """
        skills_with_experience = {}

        # Flatten the skills dictionary
        all_skills = []
        for category, skills in categorized_skills.items():
            all_skills.extend(skills)

        # For each skill, analyze work history to find mentions and calculate duration
        for category, skills in categorized_skills.items():
            skills_with_experience[category] = []

            for skill_name in skills:
                total_experience = 0.0
                mentions = []

                for job in work_history:
                    job_description = job.get("Job description", "")
                    job_title = job.get("Job title", "")
                    company = job.get("Company name", "")

                    # Check if skill is mentioned in job description or title
                    # Use more flexible matching to catch variations and related terms
                    skill_pattern = re.compile(
                        r"\b" + re.escape(skill_name).replace(r"\ ", r"\s*"),
                        re.IGNORECASE,
                    )

                    if skill_pattern.search(job_description) or skill_pattern.search(
                        job_title
                    ):
                        # Calculate duration for this job
                        start_date = self._parse_date(job.get("Start date", ""))
                        end_date = self._parse_date(
                            job.get("End date", "") or "present"
                        )

                        if start_date and end_date:
                            # Calculate years between dates
                            duration = (end_date - start_date).days / 365.25
                            total_experience += duration

                            # Add to mentions
                            mention = f"{job_title} at {company} ({job.get('Start date', '')} to {job.get('End date', 'present')})"
                            mentions.append(mention)

                # Create skill entry
                skill_entry = {
                    "skill_name": skill_name,
                    "years_experience": (
                        round(total_experience, 1) if total_experience > 0 else None
                    ),
                    "mentions": mentions if mentions else None,
                }

                skills_with_experience[category].append(skill_entry)

        return skills_with_experience

    def _estimate_proficiency(
        self, skills_with_experience: Dict[str, List[Dict]], resume_text: str
    ) -> Dict[str, List[Dict]]:
        """
        Estimate proficiency based on experience duration, frequency of mentions, and context.

        Args:
            skills_with_experience: Skills grouped by category, each with experience data
            resume_text: The full text of the resume

        Returns:
            Dict[str, List[Dict]]: Skills with proficiency estimates added
        """
        skills_with_proficiency = copy.deepcopy(skills_with_experience)

        # Iterate through each category
        for category, skills_list in skills_with_experience.items():
            # Iterate through each skill in the category
            for i, skill_info in enumerate(skills_list):
                skill_name = skill_info.get("skill_name", "")
                years_exp = skill_info.get("years_experience", 0) or 0

                # Calculate base proficiency (0-100 scale)
                # Using a logarithmic scale: 0 years = 0, 1 year = 40, 2 years = 60, 5 years = 80, 10+ years = 95
                if years_exp <= 0:
                    base_proficiency = 0
                elif years_exp < 1:
                    base_proficiency = 30 * years_exp
                elif years_exp < 2:
                    base_proficiency = 30 + (years_exp - 1) * 30
                elif years_exp < 5:
                    base_proficiency = 60 + (years_exp - 2) * 6.67
                elif years_exp < 10:
                    base_proficiency = 80 + (years_exp - 5) * 3
                else:
                    base_proficiency = 95

                # Adjust based on frequency of mentions
                mentions = skill_info.get("mentions", []) or []
                mentions_count = len(mentions)
                mention_bonus = (
                    min(5, mentions_count) * 1
                )  # Up to 5% bonus for multiple mentions

                # Check for proficiency indicators in text
                proficiency_indicators = {
                    "expert": 10,
                    "advanced": 7,
                    "proficient": 5,
                    "intermediate": 0,
                    "familiar": -5,
                    "basic": -10,
                    "beginner": -15,
                }

                # Search for proficiency indicators near skill mentions
                context_adjustment = 0
                for indicator, adjustment in proficiency_indicators.items():
                    # Look for indicator within 50 characters of skill mention
                    pattern = (
                        r"\b"
                        + re.escape(indicator)
                        + r"\b.{0,50}\b"
                        + re.escape(skill_name)
                        + r"\b|\b"
                        + re.escape(skill_name)
                        + r"\b.{0,50}\b"
                        + re.escape(indicator)
                        + r"\b"
                    )
                    if re.search(pattern, resume_text, re.IGNORECASE):
                        context_adjustment = adjustment
                        break

                # Calculate final proficiency
                proficiency = base_proficiency + mention_bonus + context_adjustment
                proficiency = max(0, min(100, proficiency))  # Ensure it's between 0-100

                # Update skill info with proficiency in the copied structure
                skills_with_proficiency[category][i]["proficiency"] = round(
                    proficiency, 1
                )

        return skills_with_proficiency

    def _find_related_skills(
        self, skills_with_proficiency: Dict[str, List[Dict]]
    ) -> Dict[str, SkillDetail]:
        """
        Find related skills for each skill and convert to SkillDetail objects.

        Args:
            skills_with_proficiency: Skills with proficiency estimates organized by category
                Format: {'Category': [{'skill_name': 'Skill', ...}, ...], ...}

        Returns:
            Dict[str, SkillDetail]: Dictionary of SkillDetail objects
        """
        # Extract all skill names first
        all_skills = {}
        for category, skills in skills_with_proficiency.items():
            for skill_info in skills:
                skill_name = skill_info["skill_name"]
                # Store the skill with its category and existing data
                all_skills[skill_name] = {
                    "skill_name": skill_name,
                    "category": category,
                    "proficiency": skill_info.get("proficiency"),
                    "years_experience": skill_info.get("years_experience"),
                    "mentions": skill_info.get("mentions"),
                }

        skill_names = list(all_skills.keys())

        # Process skills in chunks to avoid API limitations
        skill_chunks = [skill_names[i : i + 5] for i in range(0, len(skill_names), 5)]

        for chunk in skill_chunks:
            prompt = f"""
            For each of the following skills, list 2-3 closely related skills from this list: {', '.join(skill_names)}
            Skills to analyze: {', '.join(chunk)}
            
            For each skill, provide only the related skills, separated by commas.
            """

            response = self.query_engine.query(prompt)
            # Parse the response to get related skills
            lines = str(response).split("\n")
            for line in lines:
                if ":" in line:
                    skill, related = line.split(":", 1)
                    skill = skill.strip()
                    if skill in chunk:
                        related_skills = [
                            s.strip()
                            for s in related.split(",")
                            if s.strip() in skill_names and s.strip() != skill
                        ]
                        all_skills[skill]["related_skills"] = (
                            related_skills if related_skills else None
                        )

        # Convert to SkillDetail objects
        skill_details = {}
        for skill_name, skill_info in all_skills.items():
            skill_details[skill_name] = SkillDetail(
                skill_name=skill_info["skill_name"],
                category=skill_info.get("category"),
                proficiency=skill_info.get("proficiency"),
                years_experience=skill_info.get("years_experience"),
                mentions=skill_info.get("mentions"),
                related_skills=skill_info.get("related_skills"),
            )

        return skill_details

    def _extract_work_history(self) -> List[Dict]:
        """
        Extract work history from the resume.

        Returns:
            List[Dict]: List of work history entries with dates and descriptions
        """
        prompt = """
        Extract the work history from the resume. For each position, include:
        1. Job title
        2. Company name
        3. Start date (MM/YYYY format if available)
        4. End date (MM/YYYY format if available, or 'present' if current)
        5. Job description
        
        Format the response as a list of JSON objects. Please remove any ```json ``` characters from the output.
        """

        response = self.query_engine.query(prompt)
        # Parse the response to get work history
        # This is a simplified approach - in production, you'd want more robust parsing
        try:
            # Try to parse as JSON directly
            work_history = json.loads(str(response))
            if not isinstance(work_history, list):
                work_history = []
        except json.JSONDecodeError:
            # Fallback to simple parsing
            work_history = []
            current_job = {}
            lines = str(response).split("\n")
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Very simple parsing logic - would need to be more robust in production
                if line.startswith("Title:") or line.startswith("Job Title:"):
                    if current_job and "title" in current_job:
                        work_history.append(current_job)
                        current_job = {}
                    current_job["title"] = line.split(":", 1)[1].strip()
                elif line.startswith("Company:"):
                    current_job["company"] = line.split(":", 1)[1].strip()
                elif line.startswith("Start Date:") or line.startswith("From:"):
                    current_job["start_date"] = line.split(":", 1)[1].strip()
                elif line.startswith("End Date:") or line.startswith("To:"):
                    current_job["end_date"] = line.split(":", 1)[1].strip()
                elif "description" in current_job:
                    current_job["description"] += " " + line
                elif "title" in current_job:
                    current_job["description"] = line

            if current_job and "title" in current_job:
                work_history.append(current_job)

        return work_history

    def _extract_resume_text(self) -> str:
        """
        Extract the full text of the resume.

        Returns:
            str: The full text of the resume
        """
        prompt = "Please return the full text of the resume without any analysis or modifications."
        response = self.query_engine.query(prompt)
        return str(response)

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string into datetime object.

        Args:
            date_str: Date string to parse

        Returns:
            Optional[datetime]: Parsed datetime or None if parsing failed
        """
        if not date_str:
            return None

        # Handle 'present' or 'current'
        if date_str.lower() in ["present", "current", "now"]:
            return datetime.now()

        # Try various date formats
        date_formats = [
            "%m/%Y",  # 01/2020
            "%B %Y",  # January 2020
            "%b %Y",  # Jan 2020
            "%Y",  # 2020
            "%m/%d/%Y",  # 01/15/2020
            "%B %d, %Y",  # January 15, 2020
            "%b %d, %Y",  # Jan 15, 2020
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # If all parsing attempts fail
        return None

    def clean_llm_response(self, response_text: str) -> str:
        """
        Cleans LLM response by removing code block markers and language identifiers.

        Args:
            response_text: The text response from the LLM

        Returns:
            Cleaned text with code block markers removed
        """
        import re

        # Pattern to match code blocks with language identifier
        # This matches ```json\n...\n``` or any other language identifier
        pattern = r"```(?:[a-zA-Z0-9_+-]+)?\s*([\s\S]*?)\s*```"

        # Find all matches - explicitly convert arguments to match expected types
        matches = re.findall(pattern=pattern, string=response_text)

        # If matches were found, return the content inside the code blocks
        if matches:
            # Join multiple code blocks if there are several
            return "\n\n".join(matches)

        # If no code blocks found, return the original text
        return response_text


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
