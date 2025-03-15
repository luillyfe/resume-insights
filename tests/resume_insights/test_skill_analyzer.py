import unittest
from unittest.mock import Mock
from datetime import datetime
from resume_insights.models import SkillDetail
from resume_insights.skill_analyzer import SkillAnalyzer
from resume_insights.utils import parse_date

class TestSkillAnalyzer(unittest.TestCase):
    def setUp(self):
        # Create a mock query engine
        self.mock_query_engine = Mock()
        # Initialize the SkillAnalyzer with the mock query engine
        self.skill_analyzer = SkillAnalyzer(self.mock_query_engine)
        
        # Sample resume text for testing
        self.sample_resume_text = """
        John Doe
        Software Engineer with 5 years of experience in Python and JavaScript.
        Expert in React and familiar with Vue.js.
        
        WORK EXPERIENCE
        Senior Developer, ABC Tech (2020-present)
        - Led development of web applications using React and Node.js
        - Implemented CI/CD pipelines using Jenkins
        
        Developer, XYZ Solutions (2018-2020)
        - Developed backend services using Python and Django
        - Created RESTful APIs and integrated with frontend applications
        """
        
        # Sample work history for testing
        self.sample_work_history = [
            {
                "Job title": "Senior Developer",
                "Company name": "ABC Tech",
                "Start date": "2020",
                "End date": "present",
                "Job description": "Led development of web applications using React and Node.js. Implemented CI/CD pipelines using Jenkins."
            },
            {
                "Job title": "Developer",
                "Company name": "XYZ Solutions",
                "Start date": "2018",
                "End date": "2020",
                "Job description": "Developed backend services using Python and Django. Created RESTful APIs and integrated with frontend applications."
            }
        ]

    def test_extract_raw_skills(self):
        # Create a mock response object with a response attribute
        mock_response = Mock()
        mock_response.response = """
        Technical Skills: Python, JavaScript, React, Node.js, Django, Jenkins, RESTful APIs
        Soft Skills: Leadership, Communication
        """
        # Configure the mock to return the response text when converted to string
        type(mock_response).__str__ = Mock(return_value=mock_response.response)
        
        # Configure the mock query engine to return our mock response
        self.mock_query_engine.query.return_value = mock_response
        
        # Call the method being tested
        skills = self.skill_analyzer._extract_raw_skills()
        
        # Assertions
        self.assertIsInstance(skills, list)
        self.assertGreater(len(skills), 0)
        self.assertIn("Python", skills)
        self.assertIn("JavaScript", skills)
        self.assertIn("React", skills)
        
        # Verify the query engine was called
        self.mock_query_engine.query.assert_called_once()

    def test_extract_raw_skills_empty_response(self):
        # Mock an empty response
        self.mock_query_engine.query.return_value = ""
        
        # Call the method being tested
        skills = self.skill_analyzer._extract_raw_skills()
        
        # Assertions
        self.assertIsInstance(skills, list)
        self.assertEqual(len(skills), 0)

    def test_categorize_skills(self):
        # Sample skills to categorize
        raw_skills = ["Python", "JavaScript", "Leadership", "React", "Machine Learning"]
        
        # Create a mock response object with a response attribute
        mock_response = Mock()
        mock_response.response = """
        **Programming Languages:**
        * Python
        * JavaScript
        
        **Frameworks & Libraries:**
        * React
        
        **Tools & Technologies:**
        * Machine Learning
        
        **Soft Skills:**
        * Leadership
        """
        # Configure the mock to return the response text when converted to string
        type(mock_response).__str__ = Mock(return_value=mock_response.response)
        
        # Configure the mock query engine to return our mock response
        self.mock_query_engine.query.return_value = mock_response
        
        # Call the method being tested
        categorized_skills = self.skill_analyzer._categorize_skills(raw_skills)
        
        # Assertions
        self.assertIsInstance(categorized_skills, dict)
        self.assertIn("Programming Languages", categorized_skills)
        self.assertIn("Frameworks & Libraries", categorized_skills)
        self.assertIn("Soft Skills", categorized_skills)
        self.assertIn("Python", categorized_skills["Programming Languages"])
        self.assertIn("JavaScript", categorized_skills["Programming Languages"])
        self.assertIn("React", categorized_skills["Frameworks & Libraries"])
        self.assertIn("Leadership", categorized_skills["Soft Skills"])

    def test_calculate_experience_duration(self):
        # Sample categorized skills
        categorized_skills = {
            "Programming Languages": ["Python", "JavaScript"],
            "Frameworks & Libraries": ["React", "Django"],
            "Tools & Technologies": ["Jenkins"]
        }
        
        # Call the method being tested
        skills_with_experience = self.skill_analyzer._calculate_experience_duration(
            categorized_skills, self.sample_work_history
        )
        
        # Assertions
        self.assertIsInstance(skills_with_experience, dict)
        
        # Check Python skill (should have experience from both jobs)
        python_skill = None
        for skill in skills_with_experience["Programming Languages"]:
            if skill["skill_name"] == "Python":
                python_skill = skill
                break
                
        self.assertIsNotNone(python_skill)

        if python_skill is not None:  # This satisfies the type checker
            self.assertIsNotNone(python_skill["years_experience"])
            self.assertGreater(python_skill["years_experience"], 0)
        
        # Check React skill (should have experience from only the first job)
        react_skill = None
        for skill in skills_with_experience["Frameworks & Libraries"]:
            if skill["skill_name"] == "React":
                react_skill = skill
                break
                
        self.assertIsNotNone(react_skill)

        if react_skill is not None:  # This satisfies the type checker``
            self.assertIsNotNone(react_skill["years_experience"])
    
            # Verify mentions are correctly captured
            self.assertIsNotNone(react_skill["mentions"])
            self.assertIn("ABC Tech", react_skill["mentions"][0])

    def test_estimate_proficiency(self):
        # Sample skills with experience
        skills_with_experience = {
            "Programming Languages": [
                {
                    "skill_name": "Python",
                    "years_experience": 4.0,
                    "mentions": ["Developer at XYZ Solutions (2018 to 2020)"]
                },
                {
                    "skill_name": "JavaScript",
                    "years_experience": 2.5,
                    "mentions": ["Senior Developer at ABC Tech (2020 to present)"]
                }
            ]
        }
        
        # Call the method being tested
        skills_with_proficiency = self.skill_analyzer._estimate_proficiency(
            skills_with_experience, self.sample_resume_text
        )
        
        # Assertions
        self.assertIsInstance(skills_with_proficiency, dict)
        
        # Check Python skill proficiency
        python_skill = skills_with_proficiency["Programming Languages"][0]
        self.assertEqual(python_skill["skill_name"], "Python")
        self.assertIsNotNone(python_skill["proficiency"])
        self.assertGreaterEqual(python_skill["proficiency"], 0)
        self.assertLessEqual(python_skill["proficiency"], 100)
        
        # Check JavaScript skill proficiency
        js_skill = skills_with_proficiency["Programming Languages"][1]
        self.assertEqual(js_skill["skill_name"], "JavaScript")
        self.assertIsNotNone(js_skill["proficiency"])

    def test_find_related_skills(self):
        # Sample skills with proficiency
        skills_with_proficiency = {
            "Programming Languages": [
                {
                    "skill_name": "Python",
                    "years_experience": 4.0,
                    "proficiency": 75.0,
                    "mentions": ["Developer at XYZ Solutions (2018 to 2020)"]
                },
                {
                    "skill_name": "JavaScript",
                    "years_experience": 2.5,
                    "proficiency": 65.0,
                    "mentions": ["Senior Developer at ABC Tech (2020 to present)"]
                }
            ],
            "Frameworks & Libraries": [
                {
                    "skill_name": "React",
                    "years_experience": 3.0,
                    "proficiency": 70.0,
                    "mentions": ["Senior Developer at ABC Tech (2020 to present)"]
                },
                {
                    "skill_name": "Django",
                    "years_experience": 2.0,
                    "proficiency": 60.0,
                    "mentions": ["Developer at XYZ Solutions (2018 to 2020)"]
                }
            ]
        }
        
        # Create a mock response object with a response attribute
        mock_response = Mock()
        mock_response.response = """
        Python: JavaScript, Django
        JavaScript: Python, React
        React: JavaScript
        Django: Python
        """
        # Configure the mock to return the response text when converted to string
        type(mock_response).__str__ = Mock(return_value=mock_response.response)
        
        # Configure the mock query engine to return our mock response
        self.mock_query_engine.query.return_value = mock_response
        
        # Call the method being tested
        skill_details = self.skill_analyzer._find_related_skills(skills_with_proficiency)
        
        # Assertions
        self.assertIsInstance(skill_details, dict)
        self.assertIn("Python", skill_details)
        self.assertIn("JavaScript", skill_details)
        
        # Check that the returned objects are SkillDetail instances
        self.assertIsInstance(skill_details["Python"], SkillDetail)
        
        # Check related skills
        self.assertIsNotNone(skill_details["Python"].related_skills)
        self.assertIn("JavaScript", skill_details["Python"].related_skills) # type: ignore
        self.assertIn("Django", skill_details["Python"].related_skills) # type: ignore

    def test_extract_skills_with_details_integration(self):
        # Create mock response objects with response attributes
        # For _extract_raw_skills
        raw_skills_mock = Mock()
        raw_skills_mock.response = """Technical Skills: Python, JavaScript, React, Django"""
        type(raw_skills_mock).__str__ = Mock(return_value=raw_skills_mock.response)
        
        # For _categorize_skills
        categorize_mock = Mock()
        categorize_mock.response = """
        **Programming Languages:**
        * Python
        * JavaScript
        
        **Frameworks & Libraries:**
        * React
        * Django
        """
        type(categorize_mock).__str__ = Mock(return_value=categorize_mock.response)
        
        # For _find_related_skills
        related_skills_mock = Mock()
        related_skills_mock.response = """
        Python: JavaScript, Django
        JavaScript: Python, React
        React: JavaScript
        Django: Python
        """
        type(related_skills_mock).__str__ = Mock(return_value=related_skills_mock.response)
        
        # Set up the mock to return different responses for different calls
        self.mock_query_engine.query.side_effect = [
            raw_skills_mock,
            categorize_mock,
            related_skills_mock
        ]
        
        # Call the method being tested
        result = self.skill_analyzer.extract_skills_with_details(
            self.sample_resume_text, self.sample_work_history
        )
        
        # Assertions
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)
        
        # Check that we have SkillDetail objects
        for skill_name, skill_detail in result.items():
            self.assertIsInstance(skill_detail, SkillDetail)
            self.assertEqual(skill_detail.skill_name, skill_name)

    def test_parse_date_utility(self):        
        # Test various date formats
        self.assert_date_value("01/2020", 2020)
        self.assert_date_value("January 2020", 2020) 
        self.assert_date_value("Jan 2020", 2020)
        self.assert_date_value("2020", 2020)
        
        # Test present date
        self.assert_date_value("present", datetime.now().year) 
        
        # Test invalid date
        self.assertIsNone(parse_date("invalid date"))
        self.assertIsNone(parse_date(""))
        self.assertIsNone(parse_date(None)) # type: ignore[arg-type]

    def test_calculate_experience_duration_empty_work_history(self):
        # Test with empty work history
        categorized_skills = {
            "Programming Languages": ["Python", "JavaScript"],
            "Frameworks & Libraries": ["React"]
        }
        
        # Call the method with empty work history
        skills_with_experience = self.skill_analyzer._calculate_experience_duration(
            categorized_skills, []
        )
        
        # Assertions
        self.assertIsInstance(skills_with_experience, dict)
        
        # Check that skills are present but with no experience
        python_skill = None
        for skill in skills_with_experience["Programming Languages"]:
            if skill["skill_name"] == "Python":
                python_skill = skill
                break
        
        # First ensure python_skill exists
        self.assertIsNotNone(python_skill)
    
        if python_skill is not None:  # This satisfies the type checker
            self.assertIsNone(python_skill["years_experience"])
            self.assertIsNone(python_skill["mentions"])

    def test_calculate_experience_duration_skill_not_in_jobs(self):
        # Test with a skill that doesn't appear in any job descriptions
        categorized_skills = {
            "Programming Languages": ["Rust"],  # Not mentioned in sample work history
        }
        
        # Call the method
        skills_with_experience = self.skill_analyzer._calculate_experience_duration(
            categorized_skills, self.sample_work_history
        )
        
        # Assertions
        self.assertIsInstance(skills_with_experience, dict)
        
        # Check that the skill is present but with no experience
        rust_skill = skills_with_experience["Programming Languages"][0]
        self.assertEqual(rust_skill["skill_name"], "Rust")
        self.assertIsNone(rust_skill["years_experience"])
        self.assertIsNone(rust_skill["mentions"])

    def assert_date_value(self, date_str: str, expected_year: int) -> None:
        date = parse_date(date_str)
        self.assertIsNotNone(date)
        if date is not None:  # This satisfies the type checker
            self.assertEqual(date.year, expected_year)

if __name__ == "__main__":
    unittest.main()