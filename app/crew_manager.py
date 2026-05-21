import logging
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Import our agents
from agents.orchestrator_agent import OrchestratorAgent
from agents.resume_analysis_agent import ResumeAnalysisAgent
from agents.matching_agent import MatchingAgent
from agents.research_agent import ResearchAgent
from agents.validation_agent import ValidationAgent
from agents.summarization_agent import SummarizationAgent

# Import utilities
from utils.document_parser import DocumentParser
from utils.gemini_llm import map_model_name

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class HRRecruitmentCrew:
    """Enhanced HR recruitment crew manager with comprehensive AI pipeline"""
    
    def __init__(self, model="gemini-3.5-flash"):
        """Initialize the HR recruitment crew with all agents"""
        self.model = map_model_name(model)
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Validate API keys
        self._validate_api_keys()
        
        # Initialize document parser
        self.document_parser = DocumentParser()
        
        # Initialize all agents
        self.orchestrator_agent = OrchestratorAgent(model=self.model)
        self.resume_analysis_agent = ResumeAnalysisAgent(model=self.model)
        self.matching_agent = MatchingAgent(model=self.model)
        self.research_agent = ResearchAgent(model=self.model)
        self.validation_agent = ValidationAgent(model=self.model)
        self.summarization_agent = SummarizationAgent(model=self.model)
        
        # Initialize data placeholders
        self.candidates_data = None
        self.job_description = None
        self.results = {}
        
        logger.info("HR Recruitment Crew initialized successfully")
    
    def _validate_api_keys(self):
        """Validate required and optional API keys"""
        # Required API keys
        required_keys = {
            'GEMINI_API_KEY': 'Google Gemini API (required for core functionality)'
        }
        
        missing_required = []
        for key, description in required_keys.items():
            if not os.getenv(key):
                missing_required.append(f"{key} ({description})")
        
        if missing_required:
            raise ValueError(f"Missing required API keys: {', '.join(missing_required)}")
        
        # Optional API keys
        optional_keys = {
            'GITHUB_API_TOKEN': 'GitHub API (enhances repository analysis)',
            'GOOGLE_API_KEY': 'Google Search API (enables web search)',
            'GOOGLE_SEARCH_ENGINE_ID': 'Google Custom Search Engine ID',
            'LINKEDIN_API_KEY': 'LinkedIn API (enhances profile analysis)',
            'GOOGLE_APPLICATION_CREDENTIALS': 'Google Service Account (for Google Docs access)'
        }
        
        configured_optional = []
        missing_optional = []
        
        for key, description in optional_keys.items():
            if os.getenv(key):
                configured_optional.append(key)
            else:
                missing_optional.append(f"{key} ({description})")
        
        logger.info(f"Configured optional APIs: {configured_optional}")
        if missing_optional:
            logger.warning(f"Optional APIs not configured: {[key.split(' (')[0] for key in missing_optional]}")
    
    def set_candidates_data(self, candidates_data: List[Dict]):
        """Set the candidates data for processing"""
        self.candidates_data = candidates_data
        logger.info(f"Set data for {len(candidates_data)} candidates")
    
    def set_job_description(self, job_description: str):
        """Set the job description for matching"""
        self.job_description = job_description
        logger.info("Job description set")
    
    def load_candidates_from_file(self, file_path: str) -> List[Dict]:
        """Load candidates from spreadsheet file"""
        try:
            logger.info(f"Loading candidates from file: {file_path}")
            
            # Verify the file exists
            if not os.path.isfile(file_path):
                logger.error(f"File not found: {file_path}")
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Log file size and type
            file_size = os.path.getsize(file_path)
            _, file_extension = os.path.splitext(file_path)
            logger.info(f"File size: {file_size} bytes, extension: {file_extension}")
            
            # Check if file is readable
            try:
                with open(file_path, 'rb') as f:
                    # Just read a bit to check if it's accessible
                    f.read(10)
            except Exception as e:
                logger.error(f"File is not readable: {str(e)}")
                raise ValueError(f"File is not readable: {str(e)}")
            
            # Parse the spreadsheet
            parser = DocumentParser()
            candidates_data = parser.parse_spreadsheet(file_path)
            
            # Log the number of candidates found
            logger.info(f"Loaded {len(candidates_data)} candidates from file")
            
            # Log the first candidate as a sample (with sensitive info redacted)
            if candidates_data:
                sample = candidates_data[0].copy()
                if 'email' in sample:
                    sample['email'] = '[REDACTED]'
                if 'phone' in sample:
                    sample['phone'] = '[REDACTED]'
                logger.info(f"Sample candidate data: {sample}")
            
            # Set the candidates data
            self.set_candidates_data(candidates_data)
            
            return candidates_data
        except Exception as e:
            logger.error(f"Error loading candidates from file: {str(e)}")
            raise
    
    def load_job_description_from_file(self, file_path: str) -> str:
        """Load job description from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                job_description = f.read()
            self.set_job_description(job_description)
            return job_description
        except Exception as e:
            logger.error(f"Error loading job description from file: {str(e)}")
            raise
    
    def run_complete_recruitment_process(self, progress_callback=None) -> Dict:
        """Run the complete recruitment process with all agents"""
        if not self.candidates_data:
            raise ValueError("Candidates data must be set before running the process")
        
        if not self.job_description:
            raise ValueError("Job description must be set before running the process")
        
        logger.info("Starting complete HR recruitment process")
        start_time = datetime.now()
        
        try:
            # Step 1: Resume Analysis
            if progress_callback:
                progress_callback("resume_analysis", 0, "Starting resume analysis...")
            
            logger.info("Step 1: Analyzing resumes with AI")
            processed_candidates = self.resume_analysis_agent.process_candidates(self.candidates_data)
            
            if progress_callback:
                progress_callback("resume_analysis", 100, f"Analyzed {len(processed_candidates)} candidates")
            
            # Step 2: Candidate Matching
            if progress_callback:
                progress_callback("matching", 0, "Analyzing job requirements...")
            
            logger.info("Step 2: Matching candidates to job requirements")
            job_requirements = self.matching_agent.analyze_job_requirements(self.job_description)
            
            if progress_callback:
                progress_callback("matching", 50, "Matching candidates...")
            
            matching_results = self.matching_agent.match_candidates(processed_candidates, job_requirements)
            top_candidates = matching_results['top_candidates']
            
            if progress_callback:
                progress_callback("matching", 100, f"Selected {len(top_candidates)} top candidates")
            
            # Step 3: Deep Research
            if progress_callback:
                progress_callback("research", 0, "Starting comprehensive research...")
            
            logger.info(f"Step 3: Researching {len(top_candidates)} top candidates")
            
            # Run research asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if progress_callback:
                progress_callback("research", 30, "Gathering data from multiple platforms...")
            
            researched_candidates = loop.run_until_complete(
                self.research_agent.research_candidates(top_candidates)
            )
            
            if progress_callback:
                progress_callback("research", 100, "Research completed")
            
            # Step 4: Information Validation
            if progress_callback:
                progress_callback("validation", 0, "Validating candidate information...")
            
            logger.info("Step 4: Validating candidate information")
            validated_candidates = self.validation_agent.validate_candidates(researched_candidates)
            
            if progress_callback:
                progress_callback("validation", 100, "Validation completed")
            
            # Step 5: Comprehensive Report Generation
            if progress_callback:
                progress_callback("summarization", 0, "Generating comprehensive report...")
            
            logger.info("Step 5: Generating comprehensive report")
            final_report = self.summarization_agent.generate_comprehensive_report(
                validated_candidates, job_requirements, matching_results
            )
            
            if progress_callback:
                progress_callback("summarization", 80, "Saving report...")
            
            # Save the complete results
            complete_results = {
                'metadata': {
                    'process_start_time': start_time.isoformat(),
                    'process_end_time': datetime.now().isoformat(),
                    'total_processing_time': str(datetime.now() - start_time),
                    'model_used': self.model,
                    'total_candidates_processed': len(self.candidates_data),
                    'top_candidates_selected': len(top_candidates),
                    'final_candidates_validated': len(validated_candidates)
                },
                'input_data': {
                    'job_description': self.job_description,
                    'candidates_count': len(self.candidates_data)
                },
                'processing_results': {
                    'processed_candidates': processed_candidates,
                    'job_requirements': job_requirements,
                    'matching_results': matching_results,
                    'researched_candidates': researched_candidates,
                    'validated_candidates': validated_candidates
                },
                'final_report': final_report
            }
            
            # Save to file
            report_file = self._save_complete_results(complete_results)
            complete_results['report_file_path'] = report_file
            
            if progress_callback:
                progress_callback("summarization", 100, "Report generation completed")
            
            # Store results
            self.results = complete_results
            
            logger.info("Complete HR recruitment process finished successfully")
            return complete_results
            
        except Exception as e:
            logger.error(f"Error in recruitment process: {str(e)}")
            if progress_callback:
                progress_callback("error", 0, f"Process failed: {str(e)}")
            raise
    
    def run_resume_analysis_only(self) -> List[Dict]:
        """Run only the resume analysis step"""
        if not self.candidates_data:
            raise ValueError("Candidates data must be set before running analysis")
        
        logger.info("Running resume analysis only")
        processed_candidates = self.resume_analysis_agent.process_candidates(self.candidates_data)
        return processed_candidates
    
    def run_matching_only(self, processed_candidates: List[Dict]) -> Dict:
        """Run only the matching step"""
        if not self.job_description:
            raise ValueError("Job description must be set before running matching")
        
        logger.info("Running candidate matching only")
        job_requirements = self.matching_agent.analyze_job_requirements(self.job_description)
        matching_results = self.matching_agent.match_candidates(processed_candidates, job_requirements)
        
        return {
            'job_requirements': job_requirements,
            'matching_results': matching_results
        }
    
    async def run_research_only(self, top_candidates: List[Dict]) -> List[Dict]:
        """Run only the research step"""
        logger.info(f"Running research for {len(top_candidates)} candidates")
        researched_candidates = await self.research_agent.research_candidates(top_candidates)
        return researched_candidates
    
    def run_validation_only(self, researched_candidates: List[Dict]) -> List[Dict]:
        """Run only the validation step"""
        logger.info("Running validation only")
        validated_candidates = self.validation_agent.validate_candidates(researched_candidates)
        return validated_candidates
    
    def generate_report_only(self, validated_candidates: List[Dict], job_requirements: Dict, 
                           matching_results: Dict = None) -> Dict:
        """Generate only the final report"""
        logger.info("Generating report only")
        final_report = self.summarization_agent.generate_comprehensive_report(
            validated_candidates, job_requirements, matching_results
        )
        return final_report
    
    def _save_complete_results(self, complete_results: Dict) -> str:
        """Save complete results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.output_dir / f"complete_recruitment_results_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(complete_results, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Complete results saved to {filename}")
            return str(filename)
            
        except Exception as e:
            logger.error(f"Error saving complete results: {str(e)}")
            return None
    
    def get_process_summary(self) -> Dict:
        """Get a summary of the last completed process"""
        if not self.results:
            return {"error": "No process has been completed yet"}
        
        metadata = self.results.get('metadata', {})
        final_report = self.results.get('final_report', {})
        executive_summary = final_report.get('executive_summary', {})
        
        return {
            'process_info': {
                'start_time': metadata.get('process_start_time'),
                'end_time': metadata.get('process_end_time'),
                'total_time': metadata.get('total_processing_time'),
                'model_used': metadata.get('model_used')
            },
            'candidate_metrics': {
                'total_processed': metadata.get('total_candidates_processed', 0),
                'top_selected': metadata.get('top_candidates_selected', 0),
                'final_validated': metadata.get('final_candidates_validated', 0)
            },
            'key_findings': executive_summary.get('key_findings', []),
            'top_candidates': executive_summary.get('top_candidates_preview', []),
            'recommendations': executive_summary.get('recommendations', {}),
            'report_file': self.results.get('report_file_path')
        }
    
    def get_top_candidates(self, limit: int = 10) -> List[Dict]:
        """Get the top candidates from the results"""
        if not self.results:
            return []
        
        try:
            final_report = self.results.get('final_report', {})
            candidate_profiles = final_report.get('candidate_profiles', [])
            
            # Sort by rank and return top N
            sorted_candidates = sorted(candidate_profiles, key=lambda x: x.get('rank', 999))
            return sorted_candidates[:limit]
            
        except Exception as e:
            logger.error(f"Error extracting top candidates: {str(e)}")
            return []
    
    def get_candidate_by_name(self, name: str) -> Optional[Dict]:
        """Get a specific candidate by name"""
        if not self.results:
            return None
        
        try:
            final_report = self.results.get('final_report', {})
            candidate_profiles = final_report.get('candidate_profiles', [])
            
            for candidate in candidate_profiles:
                candidate_name = candidate.get('basic_information', {}).get('name', '')
                if candidate_name.lower() == name.lower():
                    return candidate
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding candidate {name}: {str(e)}")
            return None
    
    def export_results(self, format_type: str = "json", output_path: str = None) -> str:
        """Export results in different formats"""
        if not self.results:
            raise ValueError("No results available to export")
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"exported_results_{timestamp}.{format_type}"
        
        try:
            if format_type.lower() == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
            
            elif format_type.lower() == "csv":
                # Export candidate summary as CSV
                import pandas as pd
                
                candidate_profiles = self.results.get('final_report', {}).get('candidate_profiles', [])
                
                csv_data = []
                for candidate in candidate_profiles:
                    basic_info = candidate.get('basic_information', {})
                    validation = candidate.get('validation_assessment', {})
                    recommendation = candidate.get('overall_recommendation', {})
                    
                    csv_data.append({
                        'Rank': candidate.get('rank', 0),
                        'Name': basic_info.get('name', ''),
                        'Email': basic_info.get('email', ''),
                        'Location': basic_info.get('location', ''),
                        'Overall_Score': recommendation.get('confidence_level', 0),
                        'Validation_Status': validation.get('overall_status', ''),
                        'Recommendation': recommendation.get('recommendation', ''),
                        'Key_Strengths': '; '.join(candidate.get('strengths_and_concerns', {}).get('key_strengths', []))
                    })
                
                df = pd.DataFrame(csv_data)
                df.to_csv(output_path, index=False)
            
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
            
            logger.info(f"Results exported to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error exporting results: {str(e)}")
            raise
    
    def clear_results(self):
        """Clear stored results and reset the crew"""
        self.results = {}
        self.candidates_data = None
        self.job_description = None
        logger.info("Results and data cleared")
    
    def get_agent_status(self) -> Dict:
        """Get status of all agents"""
        return {
            'orchestrator': bool(self.orchestrator_agent),
            'resume_analysis': bool(self.resume_analysis_agent),
            'matching': bool(self.matching_agent),
            'research': bool(self.research_agent),
            'validation': bool(self.validation_agent),
            'summarization': bool(self.summarization_agent),
            'document_parser': bool(self.document_parser)
        }
    
    def get_api_status(self) -> Dict:
        """Get status of API configurations"""
        return {
            'openai': bool(os.getenv('OPENAI_API_KEY')),
            'github': bool(os.getenv('GITHUB_API_TOKEN')),
            'google_search': bool(os.getenv('GOOGLE_API_KEY') and os.getenv('GOOGLE_SEARCH_ENGINE_ID')),
            'linkedin': bool(os.getenv('LINKEDIN_API_KEY')),
            'google_credentials': bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
        }
