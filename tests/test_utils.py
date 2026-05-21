"""Unit tests for the HR Recruiting System utilities."""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from pathlib import Path

from utils.document_parser import DocumentParser
from utils.scoring_utils import *
from utils.api_handlers import *

class TestDocumentParser:
    def test_parse_excel(self, test_data_dir):
        parser = DocumentParser()
        # Test will be implemented when we have sample test data
        pass

    def test_parse_csv(self, test_data_dir):
        parser = DocumentParser()
        # Test will be implemented when we have sample test data
        pass

    def test_parse_job_description(self, sample_job_description):
        parser = DocumentParser()
        result = parser.parse_job_description(sample_job_description)
        assert isinstance(result, str)
        assert "Senior Software Engineer" in result

class TestScoringUtils:
    def test_calculate_skill_match_score(self):
        candidate_skills = ["Python", "Machine Learning", "AWS"]
        job_skills = ["Python", "AWS", "Docker"]
        score = calculate_skill_match_score(candidate_skills, job_skills)
        assert 0 <= score <= 1
        assert score == pytest.approx(0.67, rel=0.1)

    def test_normalize_skill_names(self):
        skills = ["python", "JAVA", "Machine Learning", "aws"]
        normalized = normalize_skill_names(skills)
        assert all(s.islower() for s in normalized)
        assert "python" in normalized
        assert "java" in normalized

class TestAPIHandlers:
    @patch('utils.api_handlers.requests')
    def test_github_api_handler(self, mock_requests):
        mock_response = MagicMock()
        mock_response.json.return_value = {"login": "test_user"}
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        result = fetch_github_profile("test_user")
        assert result is not None
        assert result["login"] == "test_user"

    @patch('utils.api_handlers.requests')
    def test_linkedin_api_handler(self, mock_requests):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "test_id"}
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        result = fetch_linkedin_profile("test_id")
        assert result is not None
        assert result["id"] == "test_id"
