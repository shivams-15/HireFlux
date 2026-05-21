"""Unit tests for the HR Recruiting System agents."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from agents.orchestrator_agent import OrchestratorAgent
from agents.resume_analysis_agent import ResumeAnalysisAgent
from agents.matching_agent import MatchingAgent
from agents.research_agent import ResearchAgent
from agents.validation_agent import ValidationAgent
from agents.summarization_agent import SummarizationAgent

class TestOrchestratorAgent:
    def test_create_tasks(self, mock_openai_key):
        agent = OrchestratorAgent()
        mock_agents = {
            'resume': MagicMock(),
            'matching': MagicMock(),
            'research': MagicMock(),
            'validation': MagicMock(),
            'summarization': MagicMock()
        }
        tasks = agent.create_tasks(**mock_agents, job_description="Test Job", candidates_data=[])
        assert len(tasks) > 0

class TestResumeAnalysisAgent:
    def test_create_tasks(self, mock_openai_key):
        agent = ResumeAnalysisAgent()
        tasks = agent.create_tasks()
        assert len(tasks) > 0

class TestMatchingAgent:
    def test_create_tasks(self, mock_openai_key):
        agent = MatchingAgent()
        tasks = agent.create_tasks()
        assert len(tasks) > 0

class TestResearchAgent:
    def test_create_tasks(self, mock_openai_key):
        agent = ResearchAgent()
        tasks = agent.create_tasks()
        assert len(tasks) > 0

class TestValidationAgent:
    def test_create_tasks(self, mock_openai_key):
        agent = ValidationAgent()
        tasks = agent.create_tasks()
        assert len(tasks) > 0

class TestSummarizationAgent:
    def test_create_tasks(self, mock_openai_key):
        agent = SummarizationAgent()
        tasks = agent.create_tasks()
        assert len(tasks) > 0
