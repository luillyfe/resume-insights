import unittest
import json
from unittest.mock import Mock
from resume_insights.work_history_analyzer import WorkHistoryAnalyzer

class TestWorkHistoryAnalyzer(unittest.TestCase):
    def setUp(self):
        # Create a mock query engine
        self.mock_query_engine = Mock()
        # Initialize the WorkHistoryAnalyzer with the mock query engine
        self.work_history_analyzer = WorkHistoryAnalyzer(self.mock_query_engine)
        
        # Sample resume text for testing
        self.sample_resume_text = """
        John Doe
        Software Engineer with 5 years of experience in Python and JavaScript.
        
        WORK EXPERIENCE
        Senior Developer, ABC Tech (01/2020-present)
        - Led development of web applications using React and Node.js
        - Implemented CI/CD pipelines using Jenkins
        
        Developer, XYZ Solutions (03/2018-12/2019)
        - Developed backend services using Python and Django
        - Created RESTful APIs and integrated with frontend applications
        """

    def test_extract_resume_text(self):
        # Configure the mock to return our sample resume text
        self.mock_query_engine.query.return_value = self.sample_resume_text
        
        # Call the method being tested
        result = self.work_history_analyzer.extract_resume_text()
        
        # Assertions
        self.assertEqual(result, self.sample_resume_text)
        
        # Verify the query engine was called with the correct prompt
        expected_prompt = "Please return the full text of the resume without any analysis or modifications."
        self.mock_query_engine.query.assert_called_once_with(expected_prompt)

    def test_extract_work_history_json_response(self):
        # Sample JSON response from the query engine
        json_response = json.dumps([
            {
                "title": "Senior Developer",
                "company": "ABC Tech",
                "start_date": "01/2020",
                "end_date": "present",
                "description": "Led development of web applications using React and Node.js. Implemented CI/CD pipelines using Jenkins."
            },
            {
                "title": "Developer",
                "company": "XYZ Solutions",
                "start_date": "03/2018",
                "end_date": "12/2019",
                "description": "Developed backend services using Python and Django. Created RESTful APIs and integrated with frontend applications."
            }
        ])
        
        # Configure the mock to return our JSON response
        self.mock_query_engine.query.return_value = json_response
        
        # Call the method being tested
        result = self.work_history_analyzer.extract_work_history()
        
        # Assertions
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], "Senior Developer")
        self.assertEqual(result[0]["company"], "ABC Tech")
        self.assertEqual(result[0]["start_date"], "01/2020")
        self.assertEqual(result[0]["end_date"], "present")
        self.assertEqual(result[1]["title"], "Developer")
        self.assertEqual(result[1]["company"], "XYZ Solutions")
        
        # Verify the query engine was called with the correct prompt
        expected_prompt = """
        Extract the work history from the resume. For each position, include:
        1. Job title
        2. Company name
        3. Start date (MM/YYYY format if available)
        4. End date (MM/YYYY format if available, or 'present' if current)
        5. Job description
        
        Format the response as a list of JSON objects. Please remove any ```json ``` characters from the output.
        """
        self.mock_query_engine.query.assert_called_once_with(expected_prompt)

    def test_extract_work_history_text_response(self):
        # Sample text response from the query engine (non-JSON format)
        text_response = """
        Job Title: Senior Developer
        Company: ABC Tech
        Start Date: 01/2020
        End Date: present
        Led development of web applications using React and Node.js. Implemented CI/CD pipelines using Jenkins.
        
        Job Title: Developer
        Company: XYZ Solutions
        Start Date: 03/2018
        End Date: 12/2019
        Developed backend services using Python and Django. Created RESTful APIs and integrated with frontend applications.
        """
        
        # Configure the mock to return our text response
        self.mock_query_engine.query.return_value = text_response
        
        # Call the method being tested
        result = self.work_history_analyzer.extract_work_history()
        
        # Assertions
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], "Senior Developer")
        self.assertEqual(result[0]["company"], "ABC Tech")
        self.assertEqual(result[0]["start_date"], "01/2020")
        self.assertEqual(result[0]["end_date"], "present")
        self.assertEqual(result[1]["title"], "Developer")
        self.assertEqual(result[1]["company"], "XYZ Solutions")
        
        # Verify the query engine was called with the correct prompt
        expected_prompt = """
        Extract the work history from the resume. For each position, include:
        1. Job title
        2. Company name
        3. Start date (MM/YYYY format if available)
        4. End date (MM/YYYY format if available, or 'present' if current)
        5. Job description
        
        Format the response as a list of JSON objects. Please remove any ```json ``` characters from the output.
        """
        self.mock_query_engine.query.assert_called_once_with(expected_prompt)

    def test_extract_work_history_empty_response(self):
        # Configure the mock to return an empty response
        self.mock_query_engine.query.return_value = ""
        
        # Call the method being tested
        result = self.work_history_analyzer.extract_work_history()
        
        # Assertions
        self.assertEqual(result, [])

    def test_extract_work_history_invalid_json(self):
        # Configure the mock to return an invalid JSON response
        self.mock_query_engine.query.return_value = "This is not a valid JSON response"
        
        # Call the method being tested
        result = self.work_history_analyzer.extract_work_history()
        
        # Assertions
        self.assertEqual(result, [])

    def test_extract_work_history_non_list_json(self):
        # Configure the mock to return a JSON object that's not a list
        self.mock_query_engine.query.return_value = '{"error": "No work history found"}'  
        
        # Call the method being tested
        result = self.work_history_analyzer.extract_work_history()
        
        # Assertions
        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main()