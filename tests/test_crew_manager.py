"""Unit tests for the HR Recruiting System crew manager."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from app.crew_manager import HRRecruitmentCrew

class TestHRRecruitmentCrew:
    def test_initialization(self, mock_openai_key):
        crew = HRRecruitmentCrew()
        assert crew.model == "gpt-4-turbo-preview"
        assert crew.candidates_data is None
        assert crew.job_description is None
        assert crew.results == {}

    def test_set_candidates_data(self, mock_openai_key, sample_candidates_df):
        crew = HRRecruitmentCrew()
        crew.set_candidates_data(sample_candidates_df)
        assert crew.candidates_data is not None
        assert len(crew.candidates_data) == len(sample_candidates_df)

    def test_set_job_description(self, mock_openai_key, sample_job_description):
        crew = HRRecruitmentCrew()
        crew.set_job_description(sample_job_description)
        assert crew.job_description == sample_job_description

    def test_run_recruitment_process_validation(self, mock_openai_key):
        crew = HRRecruitmentCrew()
        with pytest.raises(ValueError, match="Candidates data must be set before running the process"):
            crew.run_recruitment_process()

        crew.set_candidates_data([{"name": "Test"}])
        with pytest.raises(ValueError, match="Job description must be set before running the process"):
            crew.run_recruitment_process()

    @patch('app.crew_manager.Crew')
    def test_run_recruitment_process(self, mock_crew_class, mock_openai_key, sample_candidates_df, sample_job_description, temp_output_dir):
        # Setup mock crew
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = {"result": "success"}
        mock_crew_class.return_value = mock_crew

        # Run the process
        crew = HRRecruitmentCrew()
        crew.output_dir = temp_output_dir
        crew.set_candidates_data(sample_candidates_df)
        crew.set_job_description(sample_job_description)
        
        result = crew.run_recruitment_process()
        
        assert result == {"result": "success"}
        assert crew.results == {"result": "success"}
        mock_crew.kickoff.assert_called_once()
