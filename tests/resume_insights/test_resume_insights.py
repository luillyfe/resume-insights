import pytest
from unittest.mock import Mock, patch
from models import Candidate, SkillDetail, JobSkill, Skill
from resume_insights.resume_insights import ResumeInsights
from resume_insights.skill_analyzer import SkillAnalyzer
from resume_insights.work_history_analyzer import WorkHistoryAnalyzer
from resume_insights.job_matcher import JobMatcher


@pytest.fixture
def mock_query_engine():
    return Mock()


@pytest.fixture
def mock_create_query_engine(mock_query_engine):
    with patch('resume_insights.resume_insights.ResumeInsights._create_query_engine') as mock:
        mock.return_value = mock_query_engine
        yield mock


@pytest.fixture
def mock_configure_settings():
    with patch('resume_insights.resume_insights.configure_settings') as mock:
        yield mock


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
def resume_insights(mock_create_query_engine, mock_configure_settings, sample_file_path):
    return ResumeInsights(sample_file_path)


def test_initialization(resume_insights, mock_configure_settings, mock_create_query_engine, sample_file_path):
    """Test that ResumeInsights initializes correctly with the right components."""
    # Verify configure_settings was called
    mock_configure_settings.assert_called_once()
    
    # Verify _create_query_engine was called with the file path
    mock_create_query_engine.assert_called_once_with(sample_file_path)
    
    # Verify the analyzers were initialized with the query engine
    assert isinstance(resume_insights.skill_analyzer, SkillAnalyzer)
    assert isinstance(resume_insights.work_history_analyzer, WorkHistoryAnalyzer)
    assert isinstance(resume_insights.job_matcher, JobMatcher)


def test_parse_candidate_data(resume_insights, mock_query_engine):
    """Test that _parse_candidate_data correctly processes the query engine response."""
    # Create a mock candidate
    with patch('resume_insights.resume_insights.Candidate.model_validate_json') as mock_validate_json:
        mock_candidate = Mock(spec=Candidate)
        mock_validate_json.return_value = mock_candidate
        
        # Mock the query engine response
        mock_query_engine.query.return_value = '{"name": "John Doe", "email": "john@example.com"}'
        
        # Call the method
        result = resume_insights._parse_candidate_data()
        
        # Verify the query was made with the expected prompt
        mock_query_engine.query.assert_called_once()
        query_arg = mock_query_engine.query.call_args[0][0]
        assert 'Thoroughly analyze the resume document' in query_arg
        assert 'schema' in query_arg
        
        # Verify the response was validated
        mock_validate_json.assert_called_once()
        
        # Verify the result is the mock candidate
        assert result == mock_candidate


def test_extract_candidate_data(resume_insights):
    """Test that extract_candidate_data integrates the analyzers correctly."""
    # Mock the work history analyzer
    resume_insights.work_history_analyzer.extract_work_history = Mock()
    resume_insights.work_history_analyzer.extract_work_history.return_value = [
        {"title": "Data Scientist", "company": "ABC Corp"}
    ]
    
    resume_insights.work_history_analyzer.extract_resume_text = Mock()
    resume_insights.work_history_analyzer.extract_resume_text.return_value = "Sample resume text"
    
    # Mock the skill analyzer
    resume_insights.skill_analyzer.extract_skills_with_details = Mock()
    mock_skills = {"Python": SkillDetail(skill_name="Python", category="Programming", proficiency=90, years_experience=5, mentions=[], related_skills=["Django", "Flask"])}
    resume_insights.skill_analyzer.extract_skills_with_details.return_value = mock_skills
    
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
    resume_insights._parse_candidate_data = Mock(return_value=mock_candidate)
    
    # Call the method
    result = resume_insights.extract_candidate_data()
    
    # Verify the work history was extracted
    resume_insights.work_history_analyzer.extract_work_history.assert_called_once()
    
    # Verify the resume text was extracted
    resume_insights.work_history_analyzer.extract_resume_text.assert_called_once()
    
    # Verify the skills were extracted with the right parameters
    resume_insights.skill_analyzer.extract_skills_with_details.assert_called_once_with(
        "Sample resume text", [{"title": "Data Scientist", "company": "ABC Corp"}]
    )
    
    # Verify the candidate data was parsed
    resume_insights._parse_candidate_data.assert_called_once()
    
    # Verify the result has the expected properties
    assert result.name == "John Doe"
    assert result.email == "john@example.com"
    assert result.skills == mock_skills


def test_match_job_to_skills(resume_insights, sample_data):
    """Test that match_job_to_skills delegates to the job matcher correctly."""
    # Mock the job matcher
    mock_job_skill = JobSkill(skills={"Python": Skill(relevance="High", reasoning="Strong programming foundation required for data science", proficiency=90)}, jobName="Data Scientist")
    resume_insights.job_matcher.match_job_to_skills = Mock(return_value=mock_job_skill)
    
    # Call the method
    result = resume_insights.match_job_to_skills(
        sample_data['skills'], sample_data['job_position'], sample_data['company']
    )
    
    # Verify the job matcher was called with the right parameters
    resume_insights.job_matcher.match_job_to_skills.assert_called_once_with(
        sample_data['skills'], sample_data['job_position'], sample_data['company']
    )
    
    # Verify the result is the mock job skill
    assert result == mock_job_skill


def test_create_query_engine(sample_file_path):
    """Test that _create_query_engine sets up the components correctly."""
    with patch('resume_insights.resume_insights.LlamaParse') as mock_llama_parse, \
         patch('resume_insights.resume_insights.SimpleDirectoryReader') as mock_directory_reader, \
         patch('resume_insights.resume_insights.VectorStoreIndex') as mock_vector_index, \
         patch('resume_insights.resume_insights.LLAMA_CLOUD_API_KEY', 'fake_key'), \
         patch('sys.exit') as mock_exit:  # Patch sys.exit to prevent test from exiting
        
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
        
        # Create a ResumeInsights instance without mocking _create_query_engine
        resume_insights = ResumeInsights(sample_file_path)
        
        # Verify LlamaParse was initialized correctly
        mock_llama_parse.assert_called_once()
        llama_parse_args = mock_llama_parse.call_args[1]
        assert llama_parse_args['api_key'] == 'fake_key'
        
        # Verify SimpleDirectoryReader was initialized correctly
        mock_directory_reader.assert_called_once()
        directory_reader_args = mock_directory_reader.call_args[1]
        assert directory_reader_args['input_files'] == [sample_file_path]
        
        # Verify VectorStoreIndex was initialized correctly
        mock_vector_index.from_documents.assert_called_once_with(mock_documents)
        
        # Verify the query engine was created
        mock_index_instance.as_query_engine.assert_called_once()
        
        # Verify sys.exit was not called
        mock_exit.assert_not_called()