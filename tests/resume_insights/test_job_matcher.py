import unittest
from unittest.mock import Mock, patch
from models import JobSkill
from resume_insights.job_matcher import JobMatcher

class TestJobMatcher(unittest.TestCase):
    def setUp(self):
        # Create a mock query engine
        self.mock_query_engine = Mock()
        # Initialize the JobMatcher with the mock query engine
        self.job_matcher = JobMatcher(self.mock_query_engine)

    def test_match_job_to_skills_successful(self):
        # Test data
        skills = ["Python", "Machine Learning"]
        job_position = "Data Scientist"
        company = "Tech Corp"
        
        # Mock response from query engine
        mock_response = '''
        {
            "skills": {
                "Python": {
                    "relevance": "High",
                    "reasoning": "Python is essential for data science roles",
                    "proficiency": 4
                },
                "Machine Learning": {
                    "relevance": "High",
                    "reasoning": "Machine Learning is a core skill for data scientists",
                    "proficiency": 5
                }
            },
            "jobName": "Data Scientist"
        }
        '''
        
        # Configure the mock to return our predefined response
        self.mock_query_engine.query.return_value = mock_response
        
        # Call the method being tested
        result = self.job_matcher.match_job_to_skills(skills, job_position, company)
        
        # Assertions
        self.assertIsInstance(result, JobSkill)
        self.assertEqual(result.jobName, "Data Scientist")
        self.assertEqual(len(result.skills), 2)
        self.assertEqual(result.skills["Python"].relevance, "High")
        self.assertEqual(result.skills["Machine Learning"].relevance, "High")
        
        # Verify the query engine was called with the correct prompt
        call_args = self.mock_query_engine.query.call_args[0][0]
        self.assertIn("Python", call_args)
        self.assertIn("Machine Learning", call_args)
        self.assertIn("Data Scientist", call_args)
        self.assertIn("Tech Corp", call_args)
        self.assertIn(str(JobSkill.model_json_schema()), call_args)

    def test_match_job_to_skills_with_code_block(self):
        # Test data
        skills = ["JavaScript"]
        job_position = "Frontend Developer"
        company = "Web Solutions"
        
        # Mock response with code block formatting
        mock_response = '''
        ```json
        {
            "skills": {
                "JavaScript": {
                    "relevance": "High",
                    "reasoning": "JavaScript is essential for frontend development",
                    "proficiency": 4
                }
            },
            "jobName": "Frontend Developer"
        }
        ```
        '''
        
        # Configure the mock
        self.mock_query_engine.query.return_value = mock_response
        
        # Call the method being tested
        result = self.job_matcher.match_job_to_skills(skills, job_position, company)
        
        # Assertions
        self.assertIsInstance(result, JobSkill)
        self.assertEqual(result.jobName, "Frontend Developer")
        self.assertEqual(len(result.skills), 1)
        self.assertEqual(result.skills["JavaScript"].relevance, "High")

    def test_match_job_to_skills_empty_skills(self):
        # Test with empty skills list
        skills = []
        job_position = "Software Engineer"
        company = "Tech Inc"
        
        # Mock response
        mock_response = '''
        {
            "skills": {},
            "jobName": "Software Engineer"
        }
        '''
        
        # Configure the mock
        self.mock_query_engine.query.return_value = mock_response
        
        # Call the method being tested
        result = self.job_matcher.match_job_to_skills(skills, job_position, company)
        
        # Assertions
        self.assertIsInstance(result, JobSkill)
        self.assertEqual(result.jobName, "Software Engineer")
        self.assertEqual(len(result.skills), 0)
        
        # Verify the query was called with the correct prompt
        self.mock_query_engine.query.assert_called_once()

    @patch('resume_insights.job_matcher.clean_llm_response')
    def test_clean_llm_response_called(self, mock_clean_llm_response):
        # Test data
        skills = ["Python"]
        job_position = "Developer"
        company = "Tech Co"
        
        # Mock response and cleaned output
        mock_response = "Raw response"
        cleaned_json = '{"skills":{"Python":{"relevance":"High","reasoning":"Important for development","proficiency":4}},"jobName":"Developer"}'
        
        # Configure mocks
        self.mock_query_engine.query.return_value = mock_response
        mock_clean_llm_response.return_value = cleaned_json
        
        # Call the method being tested
        result = self.job_matcher.match_job_to_skills(skills, job_position, company)
        
        # Verify clean_llm_response was called with the correct argument
        mock_clean_llm_response.assert_called_once_with(str(mock_response))
        
        # Assertions on the result
        self.assertIsInstance(result, JobSkill)
        self.assertEqual(result.jobName, "Developer")

    def test_match_job_to_skills_invalid_response(self):
        # Test data
        skills = ["Python"]
        job_position = "Developer"
        company = "Tech Co"
        
        # Mock an invalid JSON response
        self.mock_query_engine.query.return_value = "Invalid JSON"
        
        # Expect a validation error when parsing the response
        with self.assertRaises(Exception):
            self.job_matcher.match_job_to_skills(skills, job_position, company)

if __name__ == '__main__':
    unittest.main()