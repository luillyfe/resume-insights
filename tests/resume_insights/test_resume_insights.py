import pytest
from unittest.mock import Mock, patch
from resume_insights.models import Candidate, SkillDetail, JobSkill, Skill
from resume_insights.core import ResumeInsights, QueryEngineFactory, create_resume_insights
from resume_insights.skill_analyzer import SkillAnalyzer
from resume_insights.work_history_analyzer import WorkHistoryAnalyzer
from resume_insights.job_matcher import JobMatcher


@pytest.fixture
def mock_query_engine():
    return Mock()


@pytest.fixture
def sample_file_path():
    return '/path/to/sample/resume.pdf'


@pytest.fixture
def sample_data():
    return {
        'skills': ["Python", "Machine Learning", "Data Analysis"],
        'job_position': "Data Scientist",
        'company': "Tech Corp"
    }


@pytest.fixture
def resume_insights_with_mock_engine(mock_query_engine):
    """Create a ResumeInsights instance with a mock query engine"""
    return ResumeInsights(query_engine=mock_query_engine)


class TestQueryEngineFactory:
    """Tests for the QueryEngineFactory class"""
    
    @patch('resume_insights.core.configure_settings')
    @patch('resume_insights.core.LlamaParse')
    @patch('resume_insights.core.SimpleDirectoryReader')
    @patch('resume_insights.core.VectorStoreIndex')
    def test_create_from_file(self, mock_vector_index, mock_directory_reader, mock_llama_parse, 
                             mock_configure_settings, sample_file_path):
        """Test that create_from_file correctly sets up the components"""
        # Mock the components
        mock_parser_instance = Mock()
        mock_llama_parse.return_value = mock_parser_instance
        
        mock_documents = [Mock()]
        mock_reader_instance = Mock()
        mock_reader_instance.load_data.return_value = mock_documents
        mock_directory_reader.return_value = mock_reader_instance
        
        mock_index_instance = Mock()
        mock_query_engine = Mock()
        mock_index_instance.as_query_engine.return_value = mock_query_engine
        mock_vector_index.from_documents.return_value = mock_index_instance
        
        # Call the method
        result = QueryEngineFactory.create_from_file(sample_file_path)
        
        # Verify configure_settings was called
        mock_configure_settings.assert_called_once()
        
        # Verify LlamaParse was initialized correctly
        mock_llama_parse.assert_called_once()
        
        # Verify SimpleDirectoryReader was initialized correctly
        mock_directory_reader.assert_called_once()
        directory_reader_args = mock_directory_reader.call_args[1]
        assert directory_reader_args['input_files'] == [sample_file_path]
        
        # Verify VectorStoreIndex was initialized correctly
        mock_vector_index.from_documents.assert_called_once_with(mock_documents)
        
        # Verify the query engine was created
        mock_index_instance.as_query_engine.assert_called_once()
        
        # Verify the result is the mock query engine
        assert result == mock_query_engine
    
    @patch('resume_insights.core.configure_settings')
    @patch('resume_insights.core.SimpleDirectoryReader')
    def test_create_from_file_error_handling(self, mock_directory_reader, mock_configure_settings, sample_file_path):
        """Test that create_from_file handles errors correctly"""
        # Mock the directory reader to raise an exception
        mock_directory_reader.side_effect = Exception("Test error")
        
        # Call the method and verify it raises a ValueError
        with pytest.raises(ValueError) as excinfo:
            QueryEngineFactory.create_from_file(sample_file_path)
        
        # Verify the error message
        assert "Failed to create query engine: Test error" in str(excinfo.value)


class TestResumeInsights:
    """Tests for the ResumeInsights class"""
    
    def test_initialization_with_query_engine(self, mock_query_engine):
        """Test that ResumeInsights initializes correctly with a query engine"""
        # Create a ResumeInsights instance with a mock query engine
        resume_insights = ResumeInsights(query_engine=mock_query_engine)
        
        # Verify the query engine was set
        assert resume_insights.query_engine == mock_query_engine
        
        # Verify the analyzers were initialized with the query engine
        assert isinstance(resume_insights.skill_analyzer, SkillAnalyzer)
        assert isinstance(resume_insights.work_history_analyzer, WorkHistoryAnalyzer)
        assert isinstance(resume_insights.job_matcher, JobMatcher)
    
    @patch('resume_insights.core.QueryEngineFactory.create_from_file')
    def test_initialization_with_file_path(self, mock_create_from_file, sample_file_path, mock_query_engine):
        """Test that ResumeInsights initializes correctly with a file path"""
        # Mock the create_from_file method
        mock_create_from_file.return_value = mock_query_engine
        
        # Create a ResumeInsights instance with a file path
        resume_insights = ResumeInsights(file_path=sample_file_path)
        
        # Verify create_from_file was called with the file path
        mock_create_from_file.assert_called_once_with(sample_file_path)
        
        # Verify the query engine was set
        assert resume_insights.query_engine == mock_query_engine
    
    def test_initialization_with_custom_analyzers(self, mock_query_engine):
        """Test that ResumeInsights initializes correctly with custom analyzers"""
        # Create mock analyzers
        mock_skill_analyzer = Mock(spec=SkillAnalyzer)
        mock_work_history_analyzer = Mock(spec=WorkHistoryAnalyzer)
        mock_job_matcher = Mock(spec=JobMatcher)
        
        # Create a ResumeInsights instance with custom analyzers
        resume_insights = ResumeInsights(
            query_engine=mock_query_engine,
            skill_analyzer=mock_skill_analyzer,
            work_history_analyzer=mock_work_history_analyzer,
            job_matcher=mock_job_matcher
        )
        
        # Verify the analyzers were set
        assert resume_insights.skill_analyzer == mock_skill_analyzer
        assert resume_insights.work_history_analyzer == mock_work_history_analyzer
        assert resume_insights.job_matcher == mock_job_matcher
    
    def test_initialization_with_no_query_engine_or_file_path(self):
        """Test that ResumeInsights raises an error when neither query_engine nor file_path is provided"""
        # Create a ResumeInsights instance with neither query_engine nor file_path
        with pytest.raises(ValueError) as excinfo:
            ResumeInsights()
        
        # Verify the error message
        assert "Either query_engine or file_path must be provided" in str(excinfo.value)
    
    def test_extract_candidate_data(self, resume_insights_with_mock_engine, mock_query_engine):
        """Test that extract_candidate_data integrates the analyzers correctly"""
        # Mock the work history analyzer
        resume_insights_with_mock_engine.work_history_analyzer.extract_work_history = Mock()
        resume_insights_with_mock_engine.work_history_analyzer.extract_work_history.return_value = [
            {"title": "Data Scientist", "company": "ABC Corp"}
        ]
        
        resume_insights_with_mock_engine.work_history_analyzer.extract_resume_text = Mock()
        resume_insights_with_mock_engine.work_history_analyzer.extract_resume_text.return_value = "Sample resume text"
        
        # Mock the skill analyzer
        resume_insights_with_mock_engine.skill_analyzer.extract_skills_with_details = Mock()
        mock_skills = {"Python": SkillDetail(skill_name="Python", category="Programming", proficiency=90, years_experience=5, mentions=[], related_skills=["Django", "Flask"])}
        resume_insights_with_mock_engine.skill_analyzer.extract_skills_with_details.return_value = mock_skills
        
        # Mock _parse_candidate_data
        mock_candidate = Candidate(
            name="John Doe",
            email="john@example.com",
            phone="555-0123",
            location="New York, NY",
            age=30,
            summary="Experienced software developer",
            skills={}
        )
        resume_insights_with_mock_engine._parse_candidate_data = Mock(return_value=mock_candidate)
        
        # Call the method
        result = resume_insights_with_mock_engine.extract_candidate_data()
        
        # Verify the work history was extracted
        resume_insights_with_mock_engine.work_history_analyzer.extract_work_history.assert_called_once()
        
        # Verify the resume text was extracted
        resume_insights_with_mock_engine.work_history_analyzer.extract_resume_text.assert_called_once()
        
        # Verify the skills were extracted with the right parameters
        resume_insights_with_mock_engine.skill_analyzer.extract_skills_with_details.assert_called_once_with(
            "Sample resume text", [{"title": "Data Scientist", "company": "ABC Corp"}]
        )
        
        # Verify the candidate data was parsed
        resume_insights_with_mock_engine._parse_candidate_data.assert_called_once()
        
        # Verify the result has the expected properties
        assert result.name == "John Doe"
        assert result.email == "john@example.com"
        assert result.skills == mock_skills
    
    def test_extract_candidate_data_error_handling(self, resume_insights_with_mock_engine):
        """Test that extract_candidate_data handles errors correctly"""
        # Mock the work history analyzer to raise an exception
        resume_insights_with_mock_engine.work_history_analyzer.extract_work_history = Mock()
        resume_insights_with_mock_engine.work_history_analyzer.extract_work_history.side_effect = Exception("Test error")
        
        # Call the method and verify it raises an Exception
        with pytest.raises(Exception) as excinfo:
            resume_insights_with_mock_engine.extract_candidate_data()
        
        # Verify the error message
        assert "Failed to extract candidate data: Test error" in str(excinfo.value)
    
    def test_parse_candidate_data(self, resume_insights_with_mock_engine, mock_query_engine):
        """Test that _parse_candidate_data correctly processes the query engine response"""
        # Create a mock candidate
        with patch('resume_insights.core.Candidate.model_validate_json') as mock_validate_json:
            mock_candidate = Mock(spec=Candidate)
            mock_validate_json.return_value = mock_candidate
            
            # Mock the query engine response
            mock_query_engine.query.return_value = '{"name": "John Doe", "email": "john@example.com"}'
            
            # Call the method
            result = resume_insights_with_mock_engine._parse_candidate_data()
            
            # Verify the query was made with the expected prompt
            mock_query_engine.query.assert_called_once()
            query_arg = mock_query_engine.query.call_args[0][0]
            assert 'Thoroughly analyze the resume document' in query_arg
            assert 'schema' in query_arg
            
            # Verify the response was validated
            mock_validate_json.assert_called_once()
            
            # Verify the result is the mock candidate
            assert result == mock_candidate
    
    def test_parse_candidate_data_error_handling(self, resume_insights_with_mock_engine, mock_query_engine):
        """Test that _parse_candidate_data handles errors correctly"""
        # Mock the query engine to raise an exception
        mock_query_engine.query.side_effect = Exception("Test error")
        
        # Call the method and verify it raises a ValueError
        with pytest.raises(ValueError) as excinfo:
            resume_insights_with_mock_engine._parse_candidate_data()
        
        # Verify the error message
        assert "Failed to parse candidate data: Test error" in str(excinfo.value)
    
    def test_match_job_to_skills(self, resume_insights_with_mock_engine, sample_data):
        """Test that match_job_to_skills delegates to the job matcher correctly"""
        # Mock the job matcher
        mock_job_skill = JobSkill(skills={"Python": Skill(relevance="High", reasoning="Strong programming foundation required for data science", proficiency=90)}, jobName="Data Scientist")
        resume_insights_with_mock_engine.job_matcher.match_job_to_skills = Mock(return_value=mock_job_skill)
        
        # Call the method
        result = resume_insights_with_mock_engine.match_job_to_skills(
            sample_data['skills'], sample_data['job_position'], sample_data['company']
        )
        
        # Verify the job matcher was called with the right parameters
        resume_insights_with_mock_engine.job_matcher.match_job_to_skills.assert_called_once_with(
            sample_data['skills'], sample_data['job_position'], sample_data['company']
        )
        
        # Verify the result is the mock job skill
        assert result == mock_job_skill
    
    def test_match_job_to_skills_error_handling(self, resume_insights_with_mock_engine, sample_data):
        """Test that match_job_to_skills handles errors correctly"""
        # Mock the job matcher to raise an exception
        resume_insights_with_mock_engine.job_matcher.match_job_to_skills = Mock(side_effect=Exception("Test error"))
        
        # Call the method and verify it raises an Exception
        with pytest.raises(Exception) as excinfo:
            resume_insights_with_mock_engine.match_job_to_skills(
                sample_data['skills'], sample_data['job_position'], sample_data['company']
            )
        
        # Verify the error message
        assert "Failed to match job to skills: Test error" in str(excinfo.value)


class TestCreateResumeInsights:
    """Tests for the create_resume_insights factory function"""
    
    @patch('resume_insights.core.ResumeInsights')
    def test_create_resume_insights(self, mock_resume_insights_class, sample_file_path):
        """Test that create_resume_insights correctly creates a ResumeInsights instance"""
        # Mock the ResumeInsights class
        mock_instance = Mock()
        mock_resume_insights_class.return_value = mock_instance
        
        # Call the factory function
        result = create_resume_insights(sample_file_path)
        
        # Verify ResumeInsights was initialized with the file path
        mock_resume_insights_class.assert_called_once_with(file_path=sample_file_path)
        
        # Verify the result is the mock instance
        assert result == mock_instance