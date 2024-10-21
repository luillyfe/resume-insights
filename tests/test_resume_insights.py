import unittest
from unittest.mock import patch, MagicMock
from resume_insights import ResumeInsights
from models import Candidate, JobSkill, Skill


class TestResumeInsights(unittest.TestCase):

    @patch("resume_insights.VectorStoreIndex")
    @patch("resume_insights.SimpleDirectoryReader")
    @patch("resume_insights.LlamaParse")
    def setUp(self, mock_llama_parse, mock_reader, mock_index):
        # Mock the file reading and indexing process
        mock_reader.return_value.load_data.return_value = [MagicMock()]
        mock_index.from_documents.return_value.as_query_engine.return_value = (
            MagicMock()
        )

        self.resume_insights = ResumeInsights("dummy_path.pdf")

    def test_extract_candidate_data(self):
        # Mock the query_engine's response
        mock_response = MagicMock()
        mock_response.response = '{"name": "John Doe", "email": "john@example.com", "skills": ["Python", "Data Analysis"]}'
        self.resume_insights.query_engine.query.return_value = mock_response

        candidate = self.resume_insights.extract_candidate_data()

        self.assertIsInstance(candidate, Candidate)
        self.assertEqual(candidate.name, "John Doe")
        self.assertEqual(candidate.email, "john@example.com")
        self.assertEqual(candidate.skills, ["Python", "Data Analysis"])

    def test_match_job_to_skills(self):
        # Mock the query_engine's response
        mock_response = MagicMock()
        mock_response.response = '{"skills": {"Python": {"relevance": "highly relevant", "reasoning": "Essential for data analysis tasks"}}}'
        self.resume_insights.query_engine.query.return_value = mock_response

        job_skill = self.resume_insights.match_job_to_skills(
            skills=["Python"], job_position="Data Analyst", company="Tech Corp"
        )

        self.assertIsInstance(job_skill, JobSkill)
        self.assertEqual(len(job_skill.skills), 1)
        # Equality comparison (not identity)
        self.assertEqual(
            job_skill.skills["Python"],
            Skill.model_validate_json(
                '{"relevance": "highly relevant", "reasoning": "Essential for data analysis tasks"}'
            ),
        )

    # It temporarily replaces the Settings, Gemini and GeminiEmbeddings objects with mocks during the test execution
    @patch("resume_insights.Settings")
    @patch("resume_insights.Gemini")
    @patch("resume_insights.GeminiEmbedding")
    def test_configure_settings(
        self, mock_gemini_embedding, mock_gemini, mock_settings
    ):
        self.resume_insights._configure_settings()

        mock_gemini.assert_called_once()
        mock_gemini_embedding.assert_called_once()
        self.assertEqual(mock_settings.embed_model, mock_gemini_embedding.return_value)
        self.assertEqual(mock_settings.llm, mock_gemini.return_value)
        self.assertIsNotNone(mock_settings.node_parser)


if __name__ == "__main__":
    unittest.main()
