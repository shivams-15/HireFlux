"""Test configuration and fixtures for the HR Recruiting System tests."""

import pytest
import os
from pathlib import Path
import pandas as pd
import tempfile

@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory."""
    return Path(__file__).parent / "test_data"

@pytest.fixture
def sample_candidates_df():
    """Create a sample candidates DataFrame for testing."""
    data = {
        "Student Name": ["John Doe", "Jane Smith", "Bob Wilson"],
        "Skills": [
            "Python, Machine Learning, AWS",
            "JavaScript, React, Node.js",
            "Data Science, SQL, R"
        ],
        "CV": [
            "https://example.com/john_cv.pdf",
            "https://example.com/jane_cv.pdf",
            "https://example.com/bob_cv.pdf"
        ]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_job_description():
    """Create a sample job description for testing."""
    return """
    Senior Software Engineer
    
    Requirements:
    - 5+ years of experience in Python development
    - Strong background in machine learning and AI
    - Experience with cloud platforms (AWS/GCP/Azure)
    - Excellent communication skills
    
    Responsibilities:
    - Design and implement machine learning solutions
    - Lead technical projects and mentor junior developers
    - Collaborate with cross-functional teams
    """

@pytest.fixture
def mock_openai_key():
    """Set a mock OpenAI API key for testing."""
    os.environ["OPENAI_API_KEY"] = "mock-openai-key-for-testing"
    yield
    del os.environ["OPENAI_API_KEY"]

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
