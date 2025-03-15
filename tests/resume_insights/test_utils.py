import pytest
from datetime import datetime
from resume_insights.utils import clean_llm_response, parse_date

class TestUtils:
    @pytest.fixture
    def sample_responses(self):
        # Sample responses for testing clean_llm_response
        return {
            "code_block_json": '''```json
{"name": "John Doe", "skills": ["Python", "JavaScript"]}
```''',
            "code_block_python": '''```python
def hello_world():
    print("Hello, World!")
```''',
            "code_block_no_language": '''```
Plain text in a code block
```''',
            "multiple_code_blocks": '''```json
{"name": "John Doe"}
```

Some text in between

```python
def hello():
    return "Hello"
```''',
            "no_code_blocks": "This is just plain text without any code blocks."
        }

    def test_clean_llm_response_with_json_code_block(self, sample_responses):
        # Test with JSON code block
        result = clean_llm_response(sample_responses["code_block_json"])
        expected = '{"name": "John Doe", "skills": ["Python", "JavaScript"]}'
        assert result == expected

    def test_clean_llm_response_with_python_code_block(self, sample_responses):
        # Test with Python code block
        result = clean_llm_response(sample_responses["code_block_python"])
        expected = 'def hello_world():\n    print("Hello, World!")'
        assert result == expected

    def test_clean_llm_response_with_no_language_code_block(self, sample_responses):
        # Test with code block without language identifier
        result = clean_llm_response(sample_responses["code_block_no_language"])
        expected = 'Plain text in a code block'
        assert result == expected

    def test_clean_llm_response_with_multiple_code_blocks(self, sample_responses):
        # Test with multiple code blocks
        result = clean_llm_response(sample_responses["multiple_code_blocks"])
        expected = '{"name": "John Doe"}\n\ndef hello():\n    return "Hello"'
        assert result == expected

    def test_clean_llm_response_with_no_code_blocks(self, sample_responses):
        # Test with text that has no code blocks
        result = clean_llm_response(sample_responses["no_code_blocks"])
        assert result == sample_responses["no_code_blocks"]

    def test_clean_llm_response_with_empty_string(self):
        # Test with empty string
        result = clean_llm_response("")
        assert result == ""

    def test_parse_date_month_year_format(self):
        # Test MM/YYYY format
        date = parse_date("01/2020")
        assert date is not None
        assert date.year == 2020
        assert date.month == 1
        assert date.day == 1  # Default day

    def test_parse_date_full_month_year_format(self):
        # Test "Month YYYY" format
        date = parse_date("January 2020")
        assert date is not None
        assert date.year == 2020
        assert date.month == 1

    def test_parse_date_abbreviated_month_year_format(self):
        # Test "Mon YYYY" format
        date = parse_date("Jan 2020")
        assert date is not None
        assert date.year == 2020
        assert date.month == 1

    def test_parse_date_year_only_format(self):
        # Test YYYY format
        date = parse_date("2020")
        assert date is not None
        assert date.year == 2020
        assert date.month == 1  # Default month

    def test_parse_date_month_day_year_format(self):
        # Test MM/DD/YYYY format
        date = parse_date("01/15/2020")
        assert date is not None
        assert date.year == 2020
        assert date.month == 1
        assert date.day == 15

    def test_parse_date_full_month_day_year_format(self):
        # Test "Month DD, YYYY" format
        date = parse_date("January 15, 2020")
        assert date is not None
        assert date.year == 2020
        assert date.month == 1
        assert date.day == 15

    def test_parse_date_abbreviated_month_day_year_format(self):
        # Test "Mon DD, YYYY" format
        date = parse_date("Jan 15, 2020")
        assert date is not None
        assert date.year == 2020
        assert date.month == 1
        assert date.day == 15

    def test_parse_date_present_values(self):
        # Test "present" value
        now = datetime.now()
        date = parse_date("present")
        assert date is not None
        assert date.year == now.year
        assert date.month == now.month

        # Test "current" value
        date = parse_date("current")
        assert date is not None
        assert date.year == now.year
        assert date.month == now.month

        # Test "now" value
        date = parse_date("now")
        assert date is not None
        assert date.year == now.year
        assert date.month == now.month

    def test_parse_date_invalid_formats(self):
        # Test invalid date format
        assert parse_date("invalid date") is None
        
        # Test empty string
        assert parse_date("") is None
        
        # Test None value
        assert parse_date(None) is None  # type: ignore[arg-type]