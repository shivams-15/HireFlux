from crewai import Agent, Task
import logging
from typing import Dict, List
from utils.gemini_llm import get_crewai_llm, map_model_name

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    def __init__(self, model="gemini-3.5-flash"):
        self.model_name = map_model_name(model)
        
        self.agent = Agent(
            role="AI Recruitment Orchestrator",
            goal="Coordinate and manage the complete AI-powered recruitment process ensuring seamless workflow between specialized agents",
            backstory="""You are the master coordinator of an advanced AI recruitment system. 
            Your expertise lies in managing complex workflows, ensuring data quality throughout 
            the pipeline, and orchestrating the seamless collaboration between specialized AI agents. 
            You understand the critical importance of each step in the recruitment process and 
            ensure that information flows correctly between resume analysis, candidate matching, 
            research, validation, and final reporting stages.""",
            verbose=True,
            allow_delegation=True,
            llm=get_crewai_llm(model=self.model_name)
        )
    
    def create_tasks(self, job_description: str, candidates_data: List[Dict]) -> List[Task]:
        """Create orchestration tasks for the complete recruitment workflow"""
        
        workflow_coordination_task = Task(
            description=f"""Coordinate the complete AI recruitment workflow for {len(candidates_data)} candidates.

JOB DESCRIPTION:
{job_description}

CANDIDATES DATA:
{len(candidates_data)} candidates loaded from spreadsheet

WORKFLOW COORDINATION RESPONSIBILITIES:

1. **Resume Analysis Coordination**:
   - Ensure all candidate resumes are processed using LLM-powered extraction
   - Validate that structured data is correctly extracted for each candidate
   - Verify that all professional links (LinkedIn, GitHub, etc.) are captured
   - Handle any parsing errors gracefully

2. **Matching Process Management**:
   - Coordinate job requirement analysis and candidate evaluation
   - Ensure semantic matching algorithms are properly applied
   - Validate that scoring criteria are consistently applied
   - Oversee selection of top 7-10 candidates for detailed research

3. **Research Operation Oversight**:
   - Manage comprehensive web research across multiple platforms
   - Coordinate data gathering from GitHub, LinkedIn, portfolios, etc.
   - Ensure research quality and completeness
   - Handle rate limiting and API constraints

4. **Validation Process Control**:
   - Oversee identity verification and information validation
   - Ensure data consistency checks are performed
   - Coordinate cross-platform information verification
   - Manage validation scoring and confidence assessment

5. **Report Generation Management**:
   - Coordinate comprehensive report creation
   - Ensure all data is properly synthesized
   - Oversee final candidate rankings and recommendations
   - Validate report quality and completeness

QUALITY ASSURANCE:
- Monitor data flow between each stage
- Ensure no candidate information is lost or mixed up
- Validate that each stage completes successfully before proceeding
- Handle errors and edge cases appropriately
- Maintain audit trail of all processing steps

WORKFLOW OPTIMIZATION:
- Identify bottlenecks and optimization opportunities
- Ensure efficient resource utilization
- Coordinate parallel processing where possible
- Manage timeouts and retries for external API calls""",
            expected_output="""Complete workflow coordination report including:
- Stage-by-stage execution summary
- Data flow validation results
- Quality assurance checkpoints passed
- Any issues encountered and resolved
- Performance metrics and timing information
- Final handoff to report generation with validated data
- Recommendations for process improvements""",
            agent=self.agent
        )
        
        return [workflow_coordination_task]
    
    def coordinate_resume_analysis(self, candidates_data: List[Dict], resume_agent) -> Dict:
        """Coordinate the resume analysis phase"""
        logger.info(f"Orchestrating resume analysis for {len(candidates_data)} candidates")
        
        try:
            # Validate input data
            self._validate_candidates_data(candidates_data)
            
            # Execute resume analysis
            processed_candidates = resume_agent.process_candidates(candidates_data)
            
            # Validate output
            validation_results = self._validate_resume_analysis_output(processed_candidates)
            
            return {
                'status': 'success',
                'processed_candidates': processed_candidates,
                'validation_results': validation_results,
                'metrics': {
                    'total_candidates': len(candidates_data),
                    'successfully_processed': len(processed_candidates),
                    'processing_success_rate': len(processed_candidates) / len(candidates_data) * 100
                }
            }
            
        except Exception as e:
            logger.error(f"Resume analysis coordination failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'processed_candidates': []
            }
    
    def coordinate_matching(self, processed_candidates: List[Dict], job_description: str, matching_agent) -> Dict:
        """Coordinate the candidate matching phase"""
        logger.info("Orchestrating candidate matching process")
        
        try:
            # Validate processed candidates
            if not processed_candidates:
                raise ValueError("No processed candidates available for matching")
            
            # Analyze job requirements
            job_requirements = matching_agent.analyze_job_requirements(job_description)
            
            # Perform matching
            matching_results = matching_agent.match_candidates(processed_candidates, job_requirements)
            
            # Validate matching results
            validation_results = self._validate_matching_output(matching_results)
            
            return {
                'status': 'success',
                'job_requirements': job_requirements,
                'matching_results': matching_results,
                'validation_results': validation_results,
                'metrics': {
                    'candidates_evaluated': len(processed_candidates),
                    'top_candidates_selected': len(matching_results.get('top_candidates', [])),
                    'selection_rate': len(matching_results.get('top_candidates', [])) / len(processed_candidates) * 100
                }
            }
            
        except Exception as e:
            logger.error(f"Matching coordination failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'job_requirements': {},
                'matching_results': {}
            }
    
    def coordinate_research(self, top_candidates: List[Dict], research_agent) -> Dict:
        """Coordinate the research phase"""
        logger.info(f"Orchestrating research for {len(top_candidates)} candidates")
        
        try:
            # Validate top candidates
            if not top_candidates:
                raise ValueError("No top candidates available for research")
            
            # Execute research (async)
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            researched_candidates = loop.run_until_complete(
                research_agent.research_candidates(top_candidates)
            )
            
            # Validate research results
            validation_results = self._validate_research_output(researched_candidates)
            
            return {
                'status': 'success',
                'researched_candidates': researched_candidates,
                'validation_results': validation_results,
                'metrics': {
                    'candidates_researched': len(top_candidates),
                    'research_completed': len(researched_candidates),
                    'research_success_rate': len(researched_candidates) / len(top_candidates) * 100,
                    'avg_sources_per_candidate': self._calculate_avg_research_sources(researched_candidates)
                }
            }
            
        except Exception as e:
            logger.error(f"Research coordination failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'researched_candidates': []
            }
    
    def coordinate_validation(self, researched_candidates: List[Dict], validation_agent) -> Dict:
        """Coordinate the validation phase"""
        logger.info(f"Orchestrating validation for {len(researched_candidates)} candidates")
        
        try:
            # Validate researched candidates
            if not researched_candidates:
                raise ValueError("No researched candidates available for validation")
            
            # Execute validation
            validated_candidates = validation_agent.validate_candidates(researched_candidates)
            
            # Validate validation results (meta-validation)
            validation_results = self._validate_validation_output(validated_candidates)
            
            return {
                'status': 'success',
                'validated_candidates': validated_candidates,
                'validation_results': validation_results,
                'metrics': {
                    'candidates_validated': len(researched_candidates),
                    'validation_completed': len(validated_candidates),
                    'high_confidence_candidates': len([c for c in validated_candidates 
                                                     if c.get('validation_results', {}).get('confidence_score', 0) >= 80]),
                    'avg_confidence_score': sum(c.get('validation_results', {}).get('confidence_score', 0) 
                                              for c in validated_candidates) / len(validated_candidates) if validated_candidates else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Validation coordination failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'validated_candidates': []
            }
    
    def coordinate_summarization(self, validated_candidates: List[Dict], job_requirements: Dict, 
                               matching_results: Dict, summarization_agent) -> Dict:
        """Coordinate the final report generation"""
        logger.info("Orchestrating final report generation")
        
        try:
            # Validate inputs
            if not validated_candidates:
                raise ValueError("No validated candidates available for summarization")
            
            # Generate comprehensive report
            final_report = summarization_agent.generate_comprehensive_report(
                validated_candidates, job_requirements, matching_results
            )
            
            # Save report
            report_file = summarization_agent.save_report(final_report)
            
            # Validate report
            validation_results = self._validate_report_output(final_report)
            
            return {
                'status': 'success',
                'final_report': final_report,
                'report_file': report_file,
                'validation_results': validation_results,
                'metrics': {
                    'candidates_in_report': len(validated_candidates),
                    'report_sections': len(final_report.keys()),
                    'top_candidates_recommended': len(final_report.get('final_rankings', {}).get('primary_ranking', [])[:5])
                }
            }
            
        except Exception as e:
            logger.error(f"Summarization coordination failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'final_report': {}
            }
    
    def _validate_candidates_data(self, candidates_data: List[Dict]):
        """Validate input candidates data"""
        if not candidates_data:
            raise ValueError("No candidates data provided")
        
        required_fields = ['Student Name', 'Skills', 'CV']
        
        for i, candidate in enumerate(candidates_data):
            for field in required_fields:
                if field not in candidate:
                    raise ValueError(f"Missing required field '{field}' in candidate {i+1}")
            
            # Validate CV field has a value
            if not candidate.get('CV'):
                logger.warning(f"Candidate {i+1} has empty CV field")
    
    def _validate_resume_analysis_output(self, processed_candidates: List[Dict]) -> Dict:
        """Validate resume analysis output"""
        validation_results = {
            'total_processed': len(processed_candidates),
            'successful_extractions': 0,
            'failed_extractions': 0,
            'missing_fields': [],
            'quality_score': 0
        }
        
        for candidate in processed_candidates:
            if candidate.get('extraction_successful', False):
                validation_results['successful_extractions'] += 1
                
                # Check for key fields
                required_sections = ['personal_info', 'contact_info', 'skills', 'links']
                missing_sections = [section for section in required_sections 
                                  if not candidate.get(section)]
                
                if missing_sections:
                    validation_results['missing_fields'].extend(missing_sections)
            else:
                validation_results['failed_extractions'] += 1
        
        # Calculate quality score
        if validation_results['total_processed'] > 0:
            validation_results['quality_score'] = (
                validation_results['successful_extractions'] / 
                validation_results['total_processed'] * 100
            )
        
        return validation_results
    
    def _validate_matching_output(self, matching_results: Dict) -> Dict:
        """Validate matching output"""
        validation_results = {
            'has_top_candidates': bool(matching_results.get('top_candidates')),
            'top_candidates_count': len(matching_results.get('top_candidates', [])),
            'has_job_requirements': bool(matching_results.get('all_candidates')),
            'all_candidates_scored': True,
            'quality_score': 0
        }
        
        # Check if all candidates have scores
        all_candidates = matching_results.get('all_candidates', [])
        for candidate in all_candidates:
            if not candidate.get('overall_score'):
                validation_results['all_candidates_scored'] = False
                break
        
        # Quality assessment
        quality_factors = [
            validation_results['has_top_candidates'],
            validation_results['top_candidates_count'] >= 5,
            validation_results['has_job_requirements'],
            validation_results['all_candidates_scored']
        ]
        
        validation_results['quality_score'] = sum(quality_factors) / len(quality_factors) * 100
        
        return validation_results
    
    def _validate_research_output(self, researched_candidates: List[Dict]) -> Dict:
        """Validate research output"""
        validation_results = {
            'total_researched': len(researched_candidates),
            'successful_research': 0,
            'failed_research': 0,
            'research_sources_found': {},
            'quality_score': 0
        }
        
        source_types = ['github', 'linkedin', 'portfolio_sites', 'professional_platforms']
        
        for candidate in researched_candidates:
            if candidate.get('research_successful', False):
                validation_results['successful_research'] += 1
                
                # Count research sources
                research_results = candidate.get('research_results', {})
                for source_type in source_types:
                    if research_results.get(source_type):
                        validation_results['research_sources_found'][source_type] = (
                            validation_results['research_sources_found'].get(source_type, 0) + 1
                        )
            else:
                validation_results['failed_research'] += 1
        
        # Calculate quality score
        if validation_results['total_researched'] > 0:
            validation_results['quality_score'] = (
                validation_results['successful_research'] / 
                validation_results['total_researched'] * 100
            )
        
        return validation_results
    
    def _validate_validation_output(self, validated_candidates: List[Dict]) -> Dict:
        """Validate validation output"""
        validation_results = {
            'total_validated': len(validated_candidates),
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'validation_statuses': {},
            'quality_score': 0
        }
        
        for candidate in validated_candidates:
            validation_data = candidate.get('validation_results', {})
            confidence_score = validation_data.get('confidence_score', 0)
            status = validation_data.get('overall_status', 'Unknown')
            
            # Count confidence levels
            if confidence_score >= 80:
                validation_results['high_confidence'] += 1
            elif confidence_score >= 60:
                validation_results['medium_confidence'] += 1
            else:
                validation_results['low_confidence'] += 1
            
            # Count statuses
            validation_results['validation_statuses'][status] = (
                validation_results['validation_statuses'].get(status, 0) + 1
            )
        
        # Calculate quality score
        if validation_results['total_validated'] > 0:
            validation_results['quality_score'] = (
                (validation_results['high_confidence'] * 1.0 + 
                 validation_results['medium_confidence'] * 0.6) / 
                validation_results['total_validated'] * 100
            )
        
        return validation_results
    
    def _validate_report_output(self, final_report: Dict) -> Dict:
        """Validate final report output"""
        validation_results = {
            'has_executive_summary': bool(final_report.get('executive_summary')),
            'has_candidate_profiles': bool(final_report.get('candidate_profiles')),
            'has_rankings': bool(final_report.get('final_rankings')),
            'has_analysis': bool(final_report.get('detailed_analysis')),
            'has_recommendations': bool(final_report.get('recommendations')),
            'report_completeness': 0,
            'quality_score': 0
        }
        
        # Check completeness
        required_sections = [
            'executive_summary', 'candidate_profiles', 'final_rankings', 
            'detailed_analysis', 'recommendations'
        ]
        
        present_sections = sum(1 for section in required_sections 
                             if final_report.get(section))
        
        validation_results['report_completeness'] = (
            present_sections / len(required_sections) * 100
        )
        
        # Quality assessment
        quality_factors = [
            validation_results['has_executive_summary'],
            validation_results['has_candidate_profiles'],
            validation_results['has_rankings'],
            validation_results['has_analysis'],
            validation_results['has_recommendations']
        ]
        
        validation_results['quality_score'] = sum(quality_factors) / len(quality_factors) * 100
        
        return validation_results
    
    def _calculate_avg_research_sources(self, researched_candidates: List[Dict]) -> float:
        """Calculate average research sources per candidate"""
        if not researched_candidates:
            return 0
        
        total_sources = 0
        for candidate in researched_candidates:
            research_results = candidate.get('research_results', {})
            sources_count = len([source for source, data in research_results.items() 
                               if data and not (isinstance(data, dict) and data.get('error'))])
            total_sources += sources_count
        
        return total_sources / len(researched_candidates)
    
    def generate_workflow_summary(self, all_results: Dict) -> Dict:
        """Generate a comprehensive workflow summary"""
        summary = {
            'workflow_status': 'completed',
            'total_processing_time': all_results.get('total_processing_time', 'Unknown'),
            'stage_results': {},
            'overall_metrics': {},
            'quality_assessment': {},
            'recommendations': []
        }
        
        # Compile stage results
        stages = ['resume_analysis', 'matching', 'research', 'validation', 'summarization']
        
        for stage in stages:
            stage_data = all_results.get(stage, {})
            if stage_data:
                summary['stage_results'][stage] = {
                    'status': stage_data.get('status', 'unknown'),
                    'metrics': stage_data.get('metrics', {}),
                    'validation': stage_data.get('validation_results', {})
                }
        
        # Calculate overall metrics
        summary['overall_metrics'] = self._calculate_overall_metrics(all_results)
        
        # Quality assessment
        summary['quality_assessment'] = self._assess_overall_quality(all_results)
        
        # Generate recommendations
        summary['recommendations'] = self._generate_workflow_recommendations(all_results)
        
        return summary
    
    def _calculate_overall_metrics(self, all_results: Dict) -> Dict:
        """Calculate overall workflow metrics"""
        metrics = {
            'candidates_input': 0,
            'candidates_processed': 0,
            'candidates_matched': 0,
            'candidates_researched': 0,
            'candidates_validated': 0,
            'final_report_generated': False,
            'overall_success_rate': 0
        }
        
        # Extract metrics from each stage
        resume_metrics = all_results.get('resume_analysis', {}).get('metrics', {})
        matching_metrics = all_results.get('matching', {}).get('metrics', {})
        research_metrics = all_results.get('research', {}).get('metrics', {})
        validation_metrics = all_results.get('validation', {}).get('metrics', {})
        
        metrics['candidates_input'] = resume_metrics.get('total_candidates', 0)
        metrics['candidates_processed'] = resume_metrics.get('successfully_processed', 0)
        metrics['candidates_matched'] = matching_metrics.get('candidates_evaluated', 0)
        metrics['candidates_researched'] = research_metrics.get('research_completed', 0)
        metrics['candidates_validated'] = validation_metrics.get('validation_completed', 0)
        metrics['final_report_generated'] = bool(all_results.get('summarization', {}).get('final_report'))
        
        # Calculate success rate
        if metrics['candidates_input'] > 0:
            metrics['overall_success_rate'] = (
                metrics['candidates_validated'] / metrics['candidates_input'] * 100
            )
        
        return metrics
    
    def _assess_overall_quality(self, all_results: Dict) -> Dict:
        """Assess overall workflow quality"""
        quality_scores = []
        
        # Collect quality scores from each stage
        for stage in ['resume_analysis', 'matching', 'research', 'validation', 'summarization']:
            stage_data = all_results.get(stage, {})
            validation_data = stage_data.get('validation_results', {})
            quality_score = validation_data.get('quality_score', 0)
            if quality_score > 0:
                quality_scores.append(quality_score)
        
        overall_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            'overall_quality_score': overall_quality,
            'quality_level': 'High' if overall_quality >= 80 else 'Medium' if overall_quality >= 60 else 'Low',
            'stage_quality_scores': {
                stage: all_results.get(stage, {}).get('validation_results', {}).get('quality_score', 0)
                for stage in ['resume_analysis', 'matching', 'research', 'validation', 'summarization']
            }
        }
    
    def _generate_workflow_recommendations(self, all_results: Dict) -> List[str]:
        """Generate workflow improvement recommendations"""
        recommendations = []
        
        # Analyze each stage for improvement opportunities
        resume_quality = all_results.get('resume_analysis', {}).get('validation_results', {}).get('quality_score', 0)
        if resume_quality < 70:
            recommendations.append("Consider improving resume parsing quality - some candidates may have incomplete data extraction")
        
        matching_quality = all_results.get('matching', {}).get('validation_results', {}).get('quality_score', 0)
        if matching_quality < 70:
            recommendations.append("Review job requirements analysis - matching criteria may need refinement")
        
        research_quality = all_results.get('research', {}).get('validation_results', {}).get('quality_score', 0)
        if research_quality < 70:
            recommendations.append("Enhance research capabilities - consider adding more API integrations")
        
        validation_quality = all_results.get('validation', {}).get('validation_results', {}).get('quality_score', 0)
        if validation_quality < 70:
            recommendations.append("Strengthen validation processes - implement additional verification checks")
        
        # Overall recommendations
        overall_metrics = self._calculate_overall_metrics(all_results)
        if overall_metrics['overall_success_rate'] < 80:
            recommendations.append("Overall success rate below 80% - review entire pipeline for bottlenecks")
        
        if not recommendations:
            recommendations.append("Workflow performed well - continue with current configuration")
        
        return recommendations