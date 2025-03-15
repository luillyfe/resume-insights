import json
from typing import List, Dict

class WorkHistoryAnalyzer:
    """
    Class for extracting and analyzing work history from resumes.
    """
    
    def __init__(self, query_engine):
        """
        Initialize the work history analyzer.
        
        Args:
            query_engine: The query engine to use for extracting information
        """
        self.query_engine = query_engine
        
    def extract_work_history(self) -> List[Dict]:
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

                # Simple parsing logic
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
    
    def extract_resume_text(self) -> str:
        """
        Extract the full text of the resume.

        Returns:
            str: The full text of the resume
        """
        prompt = "Please return the full text of the resume without any analysis or modifications."
        response = self.query_engine.query(prompt)
        return str(response)