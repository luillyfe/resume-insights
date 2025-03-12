import re
from datetime import datetime
from typing import Optional

def clean_llm_response(response_text: str) -> str:
    """
    Cleans LLM response by removing code block markers and language identifiers.

    Args:
        response_text: The text response from the LLM

    Returns:
        Cleaned text with code block markers removed
    """
    # Pattern to match code blocks with language identifier
    # This matches ```json\n...\n``` or any other language identifier
    pattern = r"```(?:[a-zA-Z0-9_+-]+)?\s*([\s\S]*?)\s*```"

    # Find all matches
    matches = re.findall(pattern=pattern, string=response_text)

    # If matches were found, return the content inside the code blocks
    if matches:
        # Join multiple code blocks if there are several
        return "\n\n".join(matches)

    # If no code blocks found, return the original text
    return response_text

def parse_date(date_str: str) -> Optional[datetime]:
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