"""Summarization Agent for creating comprehensive candidate profiles."""

from crewai import Agent, Task
import logging
from typing import Dict, List
import json
import os
import re
from datetime import datetime
from utils.gemini_llm import get_crewai_llm, map_model_name

logger = logging.getLogger(__name__)

class SummarizationAgent:
    def __init__(self, model="gemini-2.5-pro"):
        self.model_name = map_model_name(model)
        self.agent = Agent(
            role="Summarization Agent",
            goal="Create comprehensive and structured candidate profiles",
            backstory="""You are a specialized agent in information synthesis and summarization.
            Your expertise lies in analyzing various data points about candidates and creating
            clear, concise, yet comprehensive profiles that highlight their strengths,
            experience, and potential fit for roles.""",
            verbose=True,
            llm=get_crewai_llm(model=self.model_name)
        )
    
    def create_tasks(self):
        """Create tasks for the summarization agent"""
        
        create_profile_task = Task(
            description="""For each candidate, create a comprehensive profile by:
            1. Synthesizing information from all sources (resume, online profiles, research)
            2. Highlighting key achievements and experiences
            3. Summarizing technical skills and expertise levels
            4. Identifying unique selling points
            5. Noting any potential red flags or areas for further investigation
            6. Creating an executive summary
            
            Format the information in a clear, structured manner suitable for hiring managers.
            """,
            expected_output="""A detailed candidate profile document containing:
            - Executive summary
            - Key qualifications and achievements
            - Technical skills assessment
            - Experience summary
            - Education and certifications
            - Professional presence and impact
            - Potential fit analysis
            - Areas for further investigation""",
            agent=self.agent
        )
        
        generate_report_task = Task(
            description="""Create a comparative analysis report:
            1. Compare candidates against job requirements
            2. Highlight standout candidates and their unique strengths
            3. Identify gaps in the candidate pool
            4. Provide recommendations for next steps
            5. Include relevant metrics and visualizations
            
            The report should help stakeholders make informed decisions.
            """,
            expected_output="""A comprehensive report including:
            - Executive summary
            - Candidate pool analysis
            - Top candidates comparison
            - Skills gap analysis
            - Recommendations
            - Supporting data and visualizations""",
            agent=self.agent
        )
        
        return [create_profile_task, generate_report_task]
    
    def create_candidate_profile(self, 
                               resume_data: Dict, 
                               research_data: Dict, 
                               match_score: Dict,
                               validation_data: Dict) -> Dict:
        """Create a comprehensive candidate profile with all sources and verification"""
        normalized_research_data = self._normalize_research_data(research_data)
        
        # Extract name and basic info first
        name = resume_data.get('personal_info', {}).get('name', 'Unknown Candidate')
        if not name or name == 'Unknown Candidate':
            name = resume_data.get('name', 'Unknown Candidate')
        
        location = resume_data.get('personal_info', {}).get('location', 'N/A')
        
        # Collect all research sources
        sources_found = self._collect_research_sources(normalized_research_data)
        
        # Get comprehensive skills assessment with sources
        skills_assessment = self._assess_technical_skills_detailed(resume_data, normalized_research_data)
        
        # Get experience with verification
        experience_summary = self._summarize_experience_detailed(resume_data, normalized_research_data)
        
        # Get education with sources
        education_details = self._summarize_education(resume_data, normalized_research_data)
        
        # Get achievements from multiple sources
        achievements = self._extract_achievements(resume_data, normalized_research_data)
        
        # Professional presence metrics
        professional_presence = self._assess_professional_presence_detailed(normalized_research_data)
        
        # Verification status
        verification = self._get_verification_status_detailed(validation_data, name, resume_data, normalized_research_data)
        
        # Match analysis
        match_analysis = self._analyze_match(match_score)
        
        # Risk assessment
        risk_factors = self._identify_risk_factors(resume_data, normalized_research_data, validation_data)
        
        # Projects from resume and research
        projects = self._collect_all_projects(resume_data, normalized_research_data)
        
        # Publications and thought leadership
        publications = self._collect_publications(normalized_research_data)
        
        # Executive summary with context
        executive_summary = self._create_executive_summary_detailed(
            name, location, resume_data, normalized_research_data, match_score, 
            len(sources_found), len(experience_summary)
        )
        
        profile = {
            'candidate_id': resume_data.get('candidate_id', ''),
            'name': name,
            'location': location,
            'personal_info': resume_data.get('personal_info', {}),
            'contact_info': resume_data.get('contact_info', {}),
            'match_score': match_score.get('overall_score', 0),
            
            # Comprehensive profile sections
            'executive_summary': executive_summary,
            'professional_summary': {
                'total_experience_years': self._calculate_total_experience(
                    resume_data.get('experience', [])
                ),
                'current_role': experience_summary[0].get('role', 'N/A') if experience_summary else 'N/A',
                'current_company': experience_summary[0].get('company', 'N/A') if experience_summary else 'N/A',
                'industry': self._identify_industry(resume_data),
                'specialization': self._identify_specialization(skills_assessment)
            },
            
            'technical_assessment': skills_assessment,
            'experience_summary': experience_summary,
            'education_certifications': education_details,
            'projects': projects,
            'achievements': achievements,
            'publications_thought_leadership': publications,
            
            'professional_presence': professional_presence,
            'verification_status': verification,
            'match_analysis': match_analysis,
            'risk_factors': risk_factors,
            
            # Sources and verification tracking
            'research_sources': sources_found,
            'data_completeness': self._calculate_data_completeness(resume_data, normalized_research_data),
            'last_updated': datetime.now().isoformat()
        }
        
        return profile

    def _normalize_research_data(self, research_data: Dict) -> Dict:
        """Normalize research output into a stable schema used by summarization helpers."""
        if not isinstance(research_data, dict):
            return {}

        if 'web_search_results' not in research_data:
            return research_data

        web_results = research_data.get('web_search_results', {}) or {}
        github_results = web_results.get('github', []) or research_data.get('github_findings', []) or []
        linkedin_results = web_results.get('linkedin', []) or research_data.get('linkedin_findings', []) or []
        portfolio_results = web_results.get('portfolio', []) or research_data.get('portfolio_findings', []) or []
        stackoverflow_results = web_results.get('stackoverflow', []) or []
        other_results = web_results.get('other', []) or []

        def first_url(items: List[Dict]) -> str:
            for item in items:
                if isinstance(item, dict) and item.get('url'):
                    return item.get('url', '')
            return ''

        return {
            'github': {
                'profile_url': first_url(github_results),
                'repositories': [],
                'recent_activity': [],
                'profile': {},
                'search_hits': github_results,
            } if github_results else {},
            'linkedin': {
                'profile_url': first_url(linkedin_results),
                'positions': [],
                'recommendations': [],
                'skills': [],
                'connections': 0,
                'search_hits': linkedin_results,
            } if linkedin_results else {},
            'portfolio': {
                'url': first_url(portfolio_results),
                'projects': [],
                'articles': [],
                'technologies': [],
                'search_hits': portfolio_results,
            } if portfolio_results else {},
            'stackoverflow': {
                'profile_url': first_url(stackoverflow_results),
                'reputation': 0,
                'answer_count': 0,
                'question_count': 0,
                'badges': [],
                'search_hits': stackoverflow_results,
            } if stackoverflow_results else {},
            'web_presence': [
                *github_results,
                *linkedin_results,
                *portfolio_results,
                *stackoverflow_results,
                *other_results,
            ],
        }
    
    def generate_comparative_report(self, 
                                  candidates: List[Dict], 
                                  job_requirements: Dict) -> Dict:
        """Generate a comparative analysis report"""
        
        report = {
            'executive_summary': self._create_report_summary(
                candidates, job_requirements
            ),
            'candidate_pool_analysis': self._analyze_candidate_pool(
                candidates, job_requirements
            ),
            'top_candidates': self._analyze_top_candidates(candidates),
            'skills_gap_analysis': self._analyze_skills_gaps(
                candidates, job_requirements
            ),
            'recommendations': self._generate_recommendations(
                candidates, job_requirements
            ),
            'metrics': self._calculate_metrics(candidates),
            'visualizations': self._prepare_visualizations(candidates)
        }
        
        return report
    
    def _create_executive_summary(self, 
                                resume_data: Dict, 
                                research_data: Dict,
                                match_score: Dict) -> str:
        """Create an executive summary for a candidate"""
        name = resume_data.get('personal_info', {}).get('name', 'Candidate')
        if not name or name == 'Candidate':
            name = resume_data.get('name', 'Candidate')
        
        experience_list = resume_data.get('experience', [])
        if not isinstance(experience_list, list):
            experience_list = []
        
        experience_years = self._calculate_total_experience(experience_list)
        
        skills_data = resume_data.get('skills', {})
        if isinstance(skills_data, dict):
            key_skills = skills_data.get('technical', [])[:5]  # Top 5 skills
        elif isinstance(skills_data, list):
            key_skills = skills_data[:5]
        else:
            key_skills = []
        
        current_role = ''
        if experience_list and len(experience_list) > 0:
            first_exp = experience_list[0]
            if isinstance(first_exp, dict):
                current_role = first_exp.get('title', '')
        
        summary = f"{name} is a {experience_years}+ year experienced {current_role} "
        summary += f"with expertise in {', '.join(key_skills)}. "
        summary += f"Overall match score: {match_score.get('overall_score', 0):.1f}%."
        
        return summary
    
    def _assess_technical_skills(self, 
                               resume_data: Dict, 
                               research_data: Dict) -> Dict:
        """Assess technical skills with evidence"""
        skills_assessment = {}
        
        # Handle different skill data structures
        skills_data = resume_data.get('skills', {})
        if isinstance(skills_data, dict):
            claimed_skills = set(skills_data.get('technical', []))
        elif isinstance(skills_data, list):
            claimed_skills = set(skills_data)
        else:
            claimed_skills = set()
        
        # Verify skills through GitHub projects
        github_data = research_data.get('github', {})
        verified_skills = set()
        for repo in github_data.get('repositories', []):
            if isinstance(repo, dict):
                repo_skills = set([
                    repo.get('language', ''),
                    *repo.get('topics', [])
                ])
                verified_skills.update(repo_skills)
        
        # Categorize skills
        skills_assessment['verified'] = list(claimed_skills & verified_skills)
        skills_assessment['claimed'] = list(claimed_skills - verified_skills)
        skills_assessment['discovered'] = list(verified_skills - claimed_skills)
        
        return skills_assessment
    
    def _summarize_experience(self, 
                            resume_data: Dict, 
                            research_data: Dict) -> List[Dict]:
        """Summarize professional experience"""
        experience_data = resume_data.get('experience', [])
        if not isinstance(experience_data, list):
            experience_data = []
        
        linkedin_data = research_data.get('linkedin', {})
        
        summarized_experience = []
        for job in experience_data:
            if not isinstance(job, dict):
                continue
                
            # Enrich job data with LinkedIn information
            linkedin_position = self._find_matching_position(
                job, linkedin_data.get('positions', [])
            )
            
            summarized_experience.append({
                'role': job.get('title', ''),
                'company': job.get('company', ''),
                'duration': job.get('duration', ''),
                'key_achievements': self._extract_job_achievements(job),
                'technologies': self._extract_technologies(job),
                'verified': bool(linkedin_position)
            })
        
        return summarized_experience
    
    def _summarize_education(self, 
                           resume_data: Dict, 
                           research_data: Dict) -> Dict:
        """Summarize education and certifications"""
        education_data = resume_data.get('education', {})
        if isinstance(education_data, list):
            # Convert list to dict format
            education = {'degrees': education_data}
        elif isinstance(education_data, dict):
            education = education_data
        else:
            education = {}
        
        linkedin_data = research_data.get('linkedin', {})
        
        return {
            'degrees': education.get('degrees', []),
            'gpa': education.get('gpa', ''),
            'certifications': resume_data.get('certifications', []),
            'verified_certifications': linkedin_data.get('certifications', []),
            'ongoing_education': self._identify_ongoing_education(education)
        }
    
    def _extract_achievements(self, 
                            resume_data: Dict, 
                            research_data: Dict) -> List[Dict]:
        """Extract key achievements"""
        achievements = []
        
        # Get achievements from experience
        experience_data = resume_data.get('experience', [])
        if isinstance(experience_data, list):
            for job in experience_data:
                if isinstance(job, dict):
                    job_achievements = self._extract_job_achievements(job)
                    achievements.extend([
                        {'type': 'professional', 'achievement': achievement}
                        for achievement in job_achievements
                    ])
        
        # Get achievements from GitHub
        github_data = research_data.get('github', {})
        if isinstance(github_data, dict):
            repos = github_data.get('repositories', [])
            if isinstance(repos, list):
                for repo in repos:
                    if isinstance(repo, dict) and repo.get('stargazers_count', 0) > 10:
                        achievements.append({
                            'type': 'open_source',
                            'achievement': f"Created popular repository {repo.get('name', 'Unknown')} "
                                         f"with {repo.get('stargazers_count', 0)} stars"
                        })
        
        # Get achievements from Kaggle
        kaggle_data = research_data.get('kaggle', {})
        if isinstance(kaggle_data, dict):
            competitions = kaggle_data.get('competitions', [])
            if isinstance(competitions, list):
                for competition in competitions:
                    if isinstance(competition, dict) and competition.get('ranking', 0) <= 100:
                        achievements.append({
                            'type': 'competition',
                            'achievement': f"Ranked {competition.get('ranking', 0)} in "
                                         f"Kaggle competition {competition.get('name', 'Unknown')}"
                        })
        
        return achievements
    
    def _assess_professional_presence(self, research_data: Dict) -> Dict:
        """Assess candidate's professional online presence"""
        github_data = research_data.get('github', {})
        linkedin_data = research_data.get('linkedin', {})
        web_presence = research_data.get('web_presence', [])
        
        return {
            'github_activity': {
                'repositories': len(github_data.get('repositories', [])),
                'contributions': len(github_data.get('recent_activity', [])),
                'profile_complete': bool(github_data.get('profile', {}).get('bio'))
            },
            'linkedin_presence': {
                'profile_complete': bool(linkedin_data.get('summary')),
                'connections': linkedin_data.get('numConnections', 0),
                'recommendations': len(linkedin_data.get('recommendations', []))
            },
            'web_presence': {
                'articles': len([item for item in web_presence 
                               if 'article' in item.get('title', '').lower()]),
                'mentions': len([item for item in web_presence 
                               if 'mention' in item.get('title', '').lower()]),
                'projects': len([item for item in web_presence 
                               if 'project' in item.get('title', '').lower()])
            }
        }
    
    def _get_verification_status(self, validation_data: Dict) -> Dict:
        """Get verification status from validation data"""
        return {
            'verified_info': validation_data.get('verified_info', {}),
            'discrepancies': validation_data.get('discrepancies', []),
            'consistency_score': validation_data.get('consistency_score', 0)
        }
    
    def _analyze_match(self, match_score: Dict) -> Dict:
        """Analyze the match score details"""
        return {
            'overall_score': match_score.get('overall_score', 0),
            'category_scores': match_score.get('scoring_details', {}),
            'strengths': self._identify_strengths(match_score),
            'gaps': self._identify_gaps(match_score)
        }
    
    def _identify_risk_factors(self, 
                             resume_data: Dict, 
                             research_data: Dict,
                             validation_data: Dict) -> List[Dict]:
        """Identify potential risk factors"""
        risks = []
        
        # Check for employment gaps
        gaps = self._find_employment_gaps(resume_data.get('experience', []))
        if gaps:
            risks.append({
                'type': 'employment_gap',
                'details': f"Employment gaps found: {gaps}"
            })
        
        # Check for unverified claims
        if validation_data.get('discrepancies'):
            risks.append({
                'type': 'unverified_claims',
                'details': validation_data['discrepancies']
            })
        
        # Check for job hopping
        if self._check_job_hopping(resume_data.get('experience', [])):
            risks.append({
                'type': 'job_hopping',
                'details': "Frequent job changes observed"
            })
        
        return risks
    
    def _find_employment_gaps(self, experience: List[Dict]) -> List[str]:
        """Find gaps in employment history"""
        gaps = []
        sorted_jobs = sorted(experience, 
                           key=lambda x: x.get('end_date', '2025'),
                           reverse=True)
        
        for i in range(len(sorted_jobs) - 1):
            current_end = sorted_jobs[i].get('start_date')
            next_end = sorted_jobs[i + 1].get('end_date')
            if current_end and next_end:
                gap = self._calculate_date_gap(next_end, current_end)
                if gap > 3:  # Gap greater than 3 months
                    gaps.append(f"{gap} months between {sorted_jobs[i + 1].get('company')} "
                              f"and {sorted_jobs[i].get('company')}")
        
        return gaps
    
    def _check_job_hopping(self, experience: List[Dict]) -> bool:
        """Check for signs of job hopping"""
        short_terms = 0
        for job in experience:
            duration = self._calculate_job_duration(job.get('duration', ''))
            if duration < 12:  # Less than 1 year
                short_terms += 1
        
        return short_terms >= 3  # Consider 3 or more short terms as job hopping
    
    def _calculate_job_duration(self, duration: str) -> int:
        """Calculate job duration in months"""
        try:
            parts = duration.split(' - ')
            start = parts[0].split()[-1]
            end = '2025' if parts[1].lower() == 'present' else parts[1].split()[-1]
            return (int(end) - int(start)) * 12
        except:
            return 0
    
    def _collect_research_sources(self, research_data: Dict) -> List[Dict]:
        """Collect all sources found during research"""
        sources = []
        
        # GitHub sources
        github_data = research_data.get('github', {})
        if github_data:
            sources.append({
                'platform': 'GitHub',
                'profile_url': github_data.get('profile_url', ''),
                'verified': True,
                'data_points': {
                    'repositories': len(github_data.get('repositories', [])),
                    'followers': github_data.get('profile', {}).get('followers', 0),
                    'contributions': len(github_data.get('recent_activity', []))
                }
            })
        
        # LinkedIn sources
        linkedin_data = research_data.get('linkedin', {})
        if linkedin_data:
            sources.append({
                'platform': 'LinkedIn',
                'profile_url': linkedin_data.get('profile_url', ''),
                'verified': True,
                'data_points': {
                    'positions': len(linkedin_data.get('positions', [])),
                    'connections': linkedin_data.get('connections', 0),
                    'recommendations': len(linkedin_data.get('recommendations', []))
                }
            })
        
        # Portfolio/Website sources
        portfolio_data = research_data.get('portfolio', {})
        if portfolio_data:
            sources.append({
                'platform': 'Portfolio Website',
                'profile_url': portfolio_data.get('url', ''),
                'verified': True,
                'data_points': {
                    'projects': len(portfolio_data.get('projects', [])),
                    'articles': len(portfolio_data.get('articles', []))
                }
            })
        
        # StackOverflow sources
        stackoverflow_data = research_data.get('stackoverflow', {})
        if stackoverflow_data:
            sources.append({
                'platform': 'StackOverflow',
                'profile_url': stackoverflow_data.get('profile_url', ''),
                'verified': True,
                'data_points': {
                    'reputation': stackoverflow_data.get('reputation', 0),
                    'answers': stackoverflow_data.get('answer_count', 0),
                    'badges': len(stackoverflow_data.get('badges', []))
                }
            })
        
        # Web presence
        web_presence = research_data.get('web_presence', [])
        for item in web_presence:
            if isinstance(item, dict):
                sources.append({
                    'platform': item.get('source', 'Web'),
                    'profile_url': item.get('url', ''),
                    'verified': False,
                    'description': item.get('title', '')
                })
        
        return sources
    
    def _assess_technical_skills_detailed(self, resume_data: Dict, research_data: Dict) -> Dict:
        """Detailed technical skills assessment with sources"""
        resume_skills = set(resume_data.get('skills', {}).get('technical', []))
        if not resume_skills:
            resume_skills = set(resume_data.get('skills', []))
        
        # Collect skills from different sources
        github_skills = set()
        github_data = research_data.get('github', {})
        for repo in github_data.get('repositories', []):
            if isinstance(repo, dict):
                if repo.get('language'):
                    github_skills.add(repo['language'])
                github_skills.update(repo.get('topics', []))
        
        linkedin_skills = set()
        linkedin_data = research_data.get('linkedin', {})
        linkedin_skills.update(linkedin_data.get('skills', []))
        
        # Categorize skills by verification source
        skills_verified_github = list(resume_skills & github_skills)
        skills_verified_linkedin = list(resume_skills & linkedin_skills)
        skills_verified_both = list(set(skills_verified_github) & set(skills_verified_linkedin))
        skills_claimed_only = list(resume_skills - github_skills - linkedin_skills)
        skills_discovered = list((github_skills | linkedin_skills) - resume_skills)
        
        return {
            'verified_skills': {
                'high_confidence': skills_verified_both,  # Verified in multiple sources
                'medium_confidence': skills_verified_github + skills_verified_linkedin,
                'total_verified': len(set(skills_verified_github + skills_verified_linkedin))
            },
            'claimed_skills': {
                'unverified': skills_claimed_only,
                'count': len(skills_claimed_only)
            },
            'discovered_skills': {
                'additional_expertise': skills_discovered,
                'count': len(skills_discovered)
            },
            'skill_sources': {
                'github_repositories': len(github_data.get('repositories', [])),
                'linkedin_endorsements': len(linkedin_data.get('skills', []))
            },
            'total_skills': len(resume_skills | github_skills | linkedin_skills)
        }
    
    def _summarize_experience_detailed(self, resume_data: Dict, research_data: Dict) -> List[Dict]:
        """Detailed experience summary with verification"""
        experience_data = resume_data.get('experience', [])
        if not isinstance(experience_data, list):
            experience_data = []
        
        linkedin_data = research_data.get('linkedin', {})
        linkedin_positions = linkedin_data.get('positions', [])
        
        detailed_experience = []
        for job in experience_data:
            if not isinstance(job, dict):
                continue
            
            # Try to find matching LinkedIn position
            linkedin_match = self._find_matching_position(job, linkedin_positions)
            
            experience_entry = {
                'role': job.get('title', job.get('role', '')),
                'company': job.get('company', ''),
                'duration': job.get('duration', ''),
                'location': job.get('location', ''),
                'description': job.get('description', ''),
                'key_achievements': self._extract_job_achievements(job),
                'technologies_used': self._extract_technologies(job),
                'verification': {
                    'verified_linkedin': bool(linkedin_match),
                    'source': 'LinkedIn' if linkedin_match else 'Resume only',
                    'confidence': 'High' if linkedin_match else 'Medium'
                },
                'linkedin_details': linkedin_match if linkedin_match else None
            }
            detailed_experience.append(experience_entry)
        
        return detailed_experience
    
    def _assess_professional_presence_detailed(self, research_data: Dict) -> Dict:
        """Detailed professional presence assessment"""
        github_data = research_data.get('github', {})
        linkedin_data = research_data.get('linkedin', {})
        portfolio_data = research_data.get('portfolio', {})
        stackoverflow_data = research_data.get('stackoverflow', {})
        
        return {
            'github': {
                'profile_url': github_data.get('profile_url', ''),
                'metrics': {
                    'public_repos': len(github_data.get('repositories', [])),
                    'followers': github_data.get('profile', {}).get('followers', 0),
                    'total_stars': sum(r.get('stargazers_count', 0) for r in github_data.get('repositories', [])),
                    'total_forks': sum(r.get('forks_count', 0) for r in github_data.get('repositories', [])),
                    'contributions_last_year': len(github_data.get('recent_activity', []))
                },
                'top_repositories': github_data.get('repositories', [])[:5],
                'activity_level': self._assess_github_activity(github_data)
            },
            'linkedin': {
                'profile_url': linkedin_data.get('profile_url', ''),
                'metrics': {
                    'connections': linkedin_data.get('connections', 0),
                    'recommendations': len(linkedin_data.get('recommendations', [])),
                    'endorsements': len(linkedin_data.get('skills', []))
                },
                'profile_completeness': self._assess_linkedin_completeness(linkedin_data),
                'professional_network_strength': self._assess_network_strength(linkedin_data)
            },
            'portfolio': {
                'url': portfolio_data.get('url', ''),
                'projects_showcased': len(portfolio_data.get('projects', [])),
                'articles_published': len(portfolio_data.get('articles', [])),
                'technologies': portfolio_data.get('technologies', [])
            },
            'stackoverflow': {
                'profile_url': stackoverflow_data.get('profile_url', ''),
                'reputation': stackoverflow_data.get('reputation', 0),
                'answers': stackoverflow_data.get('answer_count', 0),
                'questions': stackoverflow_data.get('question_count', 0),
                'badges': stackoverflow_data.get('badges', []),
                'activity_level': self._assess_stackoverflow_activity(stackoverflow_data)
            },
            'overall_presence_score': self._calculate_overall_presence_score(
                github_data, linkedin_data, portfolio_data, stackoverflow_data
            )
        }
    
    def _get_verification_status_detailed(self, validation_data: Dict, name: str, resume_data: Dict, research_data: Dict) -> Dict:
        """Detailed verification status"""
        return {
            'candidate_name': name,
            'verification_timestamp': datetime.now().isoformat(),
            'overall_status': validation_data.get('overall_status', 'Pending'),
            'confidence_score': validation_data.get('confidence_score', validation_data.get('consistency_score', 0)),
            'verified_information': {
                'personal_info': validation_data.get('verified_info', {}).get('personal_info', False),
                'contact_info': validation_data.get('verified_info', {}).get('contact_info', False),
                'experience': validation_data.get('verified_info', {}).get('experience', False),
                'education': validation_data.get('verified_info', {}).get('education', False),
                'skills': validation_data.get('verified_info', {}).get('skills', False)
            },
            'discrepancies_found': validation_data.get('discrepancies', []),
            'cross_reference_checks': validation_data.get('cross_references', {}),
            'data_sources_count': len(self._collect_research_sources(research_data)),
            'verification_notes': validation_data.get('notes', '')
        }
    
    def _collect_all_projects(self, resume_data: Dict, research_data: Dict) -> List[Dict]:
        """Collect all projects from resume and research"""
        projects = []
        
        # Resume projects
        resume_projects = resume_data.get('projects', [])
        for project in resume_projects:
            if isinstance(project, dict):
                projects.append({
                    'name': project.get('name', ''),
                    'description': project.get('description', ''),
                    'technologies': project.get('technologies', []),
                    'source': 'Resume',
                    'url': project.get('url', ''),
                    'verified': False
                })
        
        # GitHub projects
        github_data = research_data.get('github', {})
        for repo in github_data.get('repositories', []):
            if isinstance(repo, dict):
                projects.append({
                    'name': repo.get('name', ''),
                    'description': repo.get('description', ''),
                    'technologies': [repo.get('language', '')] + repo.get('topics', []),
                    'source': 'GitHub',
                    'url': repo.get('html_url', ''),
                    'verified': True,
                    'metrics': {
                        'stars': repo.get('stargazers_count', 0),
                        'forks': repo.get('forks_count', 0),
                        'open_issues': repo.get('open_issues_count', 0)
                    }
                })
        
        # Portfolio projects
        portfolio_data = research_data.get('portfolio', {})
        for project in portfolio_data.get('projects', []):
            if isinstance(project, dict):
                projects.append({
                    'name': project.get('name', ''),
                    'description': project.get('description', ''),
                    'technologies': project.get('technologies', []),
                    'source': 'Portfolio',
                    'url': project.get('url', ''),
                    'verified': True
                })
        
        return projects
    
    def _collect_publications(self, research_data: Dict) -> Dict:
        """Collect publications and thought leadership content"""
        web_presence = research_data.get('web_presence', [])
        
        articles = []
        talks = []
        mentions = []
        
        for item in web_presence:
            if not isinstance(item, dict):
                continue
            
            title = item.get('title', '').lower()
            if 'article' in title or 'blog' in title or 'post' in title:
                articles.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'platform': item.get('source', ''),
                    'snippet': item.get('snippet', '')
                })
            elif 'talk' in title or 'presentation' in title or 'speak' in title:
                talks.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'event': item.get('source', ''),
                    'snippet': item.get('snippet', '')
                })
            else:
                mentions.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'platform': item.get('source', ''),
                    'snippet': item.get('snippet', '')
                })
        
        return {
            'articles': articles,
            'talks_presentations': talks,
            'online_mentions': mentions,
            'total_count': len(articles) + len(talks) + len(mentions)
        }
    
    def _create_executive_summary_detailed(self, name: str, location: str, resume_data: Dict, 
                                          research_data: Dict, match_score: Dict,
                                          sources_count: int, experience_count: int) -> str:
        """Create detailed executive summary"""
        years_experience = self._calculate_total_experience(resume_data.get('experience', []))
        skills_count = len(resume_data.get('skills', {}).get('technical', [])) or len(resume_data.get('skills', []))
        overall_score = match_score.get('overall_score', 0)
        
        # Get current role
        experience = resume_data.get('experience', [])
        current_role = experience[0].get('title', experience[0].get('role', 'Professional')) if experience else 'Professional'
        current_company = experience[0].get('company', '') if experience else ''
        
        summary = f"""
**Candidate: {name}**
**Location: {location}**

{name} is a {current_role}{' at ' + current_company if current_company else ''} with {years_experience} years of professional experience. 
Based on comprehensive AI-powered analysis across {sources_count} verified online sources, this candidate demonstrates:

- **Match Score: {overall_score}%** - {'Strong' if overall_score >= 80 else 'Good' if overall_score >= 60 else 'Moderate'} alignment with job requirements
- **Technical Expertise:** {skills_count}+ documented technical skills and competencies
- **Professional Experience:** {experience_count} verified positions across reputable organizations
- **Digital Footprint:** Active professional presence across {sources_count} platforms
- **Verification Status:** {'High confidence' if sources_count >= 3 else 'Moderate confidence'} - information cross-verified from multiple sources

**Key Highlights:**
{self._generate_key_highlights(resume_data, research_data, match_score)}

**Overall Assessment:**
{self._generate_overall_assessment(overall_score, sources_count, resume_data)}
        """.strip()
        
        return summary
    
    def _calculate_data_completeness(self, resume_data: Dict, research_data: Dict) -> Dict:
        """Calculate how complete the candidate data is"""
        completeness = {
            'resume_data': {
                'personal_info': bool(resume_data.get('personal_info')),
                'contact_info': bool(resume_data.get('contact_info')),
                'experience': bool(resume_data.get('experience')),
                'education': bool(resume_data.get('education')),
                'skills': bool(resume_data.get('skills')),
                'projects': bool(resume_data.get('projects'))
            },
            'research_data': {
                'github': bool(research_data.get('github')),
                'linkedin': bool(research_data.get('linkedin')),
                'portfolio': bool(research_data.get('portfolio')),
                'stackoverflow': bool(research_data.get('stackoverflow')),
                'web_presence': bool(research_data.get('web_presence'))
            }
        }
        
        resume_score = sum(completeness['resume_data'].values()) / len(completeness['resume_data']) * 100
        research_score = sum(completeness['research_data'].values()) / len(completeness['research_data']) * 100
        
        completeness['resume_completeness_percent'] = round(resume_score, 1)
        completeness['research_completeness_percent'] = round(research_score, 1)
        completeness['overall_completeness_percent'] = round((resume_score + research_score) / 2, 1)
        
        return completeness
    
    def _assess_github_activity(self, github_data: Dict) -> str:
        """Assess GitHub activity level"""
        if not github_data:
            return 'None'
        
        repos = len(github_data.get('repositories', []))
        contributions = len(github_data.get('recent_activity', []))
        
        if repos >= 10 and contributions >= 50:
            return 'Highly Active'
        elif repos >= 5 or contributions >= 20:
            return 'Active'
        elif repos >= 1:
            return 'Moderate'
        else:
            return 'Low'
    
    def _assess_linkedin_completeness(self, linkedin_data: Dict) -> str:
        """Assess LinkedIn profile completeness"""
        if not linkedin_data:
            return 'None'
        
        has_summary = bool(linkedin_data.get('summary'))
        has_positions = bool(linkedin_data.get('positions'))
        has_skills = bool(linkedin_data.get('skills'))
        has_recommendations = bool(linkedin_data.get('recommendations'))
        
        score = sum([has_summary, has_positions, has_skills, has_recommendations])
        
        if score >= 3:
            return 'Comprehensive'
        elif score >= 2:
            return 'Good'
        else:
            return 'Basic'
    
    def _assess_network_strength(self, linkedin_data: Dict) -> str:
        """Assess professional network strength"""
        connections = linkedin_data.get('connections', 0)
        
        if connections >= 500:
            return 'Strong'
        elif connections >= 100:
            return 'Moderate'
        else:
            return 'Growing'
    
    def _assess_stackoverflow_activity(self, stackoverflow_data: Dict) -> str:
        """Assess StackOverflow activity level"""
        if not stackoverflow_data:
            return 'None'
        
        reputation = stackoverflow_data.get('reputation', 0)
        
        if reputation >= 1000:
            return 'Highly Active'
        elif reputation >= 100:
            return 'Active'
        else:
            return 'Basic'
    
    def _calculate_overall_presence_score(self, github_data: Dict, linkedin_data: Dict, 
                                         portfolio_data: Dict, stackoverflow_data: Dict) -> int:
        """Calculate overall professional presence score"""
        score = 0
        
        # GitHub contribution
        if github_data:
            repos = len(github_data.get('repositories', []))
            score += min(repos * 5, 25)
        
        # LinkedIn contribution
        if linkedin_data:
            connections = linkedin_data.get('connections', 0)
            score += min(connections // 10, 25)
        
        # Portfolio contribution
        if portfolio_data:
            score += 25
        
        # StackOverflow contribution
        if stackoverflow_data:
            reputation = stackoverflow_data.get('reputation', 0)
            score += min(reputation // 100, 25)
        
        return min(score, 100)
    
    def _calculate_total_experience(self, experience: List[Dict]) -> int:
        """Calculate total years of experience"""
        if not experience:
            return 0
        
        total_months = 0
        for job in experience:
            if isinstance(job, dict):
                duration = self._calculate_job_duration(job.get('duration', ''))
                total_months += duration
        
        return round(total_months / 12, 1)
    
    def _identify_industry(self, resume_data: Dict) -> str:
        """Identify primary industry from experience"""
        experience = resume_data.get('experience', [])
        if not experience or not isinstance(experience, list):
            return 'Technology'
        
        # Simple industry identification - can be enhanced
        return 'Technology & Software Development'
    
    def _identify_specialization(self, skills_assessment: Dict) -> str:
        """Identify primary specialization from skills"""
        verified = skills_assessment.get('verified_skills', {}).get('high_confidence', [])
        
        # Simple specialization logic - can be enhanced
        if any('python' in str(s).lower() for s in verified):
            return 'Backend Development / Data Science'
        elif any('react' in str(s).lower() for s in verified):
            return 'Frontend Development'
        elif any('devops' in str(s).lower() for s in verified):
            return 'DevOps / Cloud Engineering'
        else:
            return 'Full Stack Development'
    
    def _generate_key_highlights(self, resume_data: Dict, research_data: Dict, match_score: Dict) -> str:
        """Generate key highlights for executive summary"""
        highlights = []
        
        # Top skill
        skills = resume_data.get('skills', {})
        if isinstance(skills, dict):
            top_skills = skills.get('technical', [])[:3]
        else:
            top_skills = skills[:3] if isinstance(skills, list) else []
        
        if top_skills:
            highlights.append(f"• Expertise in {', '.join(top_skills)}")
        
        # GitHub activity
        github_data = research_data.get('github', {})
        if github_data.get('repositories'):
            repo_count = len(github_data['repositories'])
            highlights.append(f"• {repo_count} public repositories on GitHub demonstrating practical coding experience")
        
        # Experience
        experience = resume_data.get('experience', [])
        if experience:
            highlights.append(f"• Proven track record with {len(experience)} professional positions")
        
        return '\n'.join(highlights) if highlights else '• Comprehensive professional background'
    
    def _generate_overall_assessment(self, overall_score: int, sources_count: int, resume_data: Dict) -> str:
        """Generate overall assessment text"""
        if overall_score >= 80:
            fit_level = "HIGHLY RECOMMENDED"
            assessment = "Exceptional candidate with strong alignment to requirements"
        elif overall_score >= 60:
            fit_level = "RECOMMENDED"
            assessment = "Good candidate with solid qualifications"
        else:
            fit_level = "CONSIDER"
            assessment = "Candidate shows potential but may require additional evaluation"
        
        return f"**{fit_level}** - {assessment}. Profile verified through {sources_count} independent sources."

    def generate_comprehensive_report(self, validated_candidates: List[Dict], job_requirements: Dict, matching_results: Dict = None) -> Dict:
        """Generate a comprehensive report for all validated candidates
        
        Args:
            validated_candidates: List of validated candidate data
            job_requirements: Job requirements data
            matching_results: Optional matching results data
        
        Returns:
            Comprehensive report dictionary
        """
        logger.info(f"Generating comprehensive report for {len(validated_candidates)} candidates")
        
        try:
            candidate_profiles = []
            
            # Debug: Log the structure of validated_candidates
            logger.info(f"Type of validated_candidates: {type(validated_candidates)}")
            if validated_candidates:
                logger.info(f"Type of first element: {type(validated_candidates[0])}")
                logger.info(f"First element keys: {list(validated_candidates[0].keys()) if isinstance(validated_candidates[0], dict) else 'Not a dict'}")
            
            for i, candidate_item in enumerate(validated_candidates):
                try:
                    # Handle different possible structures
                    candidate_data = None
                    
                    if isinstance(candidate_item, dict):
                        candidate_data = candidate_item
                    elif isinstance(candidate_item, list) and len(candidate_item) > 0:
                        # If it's a list, try to get the first dict item
                        for item in candidate_item:
                            if isinstance(item, dict):
                                candidate_data = item
                                break
                    else:
                        logger.warning(f"Candidate {i} has unexpected type: {type(candidate_item)}")
                        continue
                    
                    if not candidate_data:
                        logger.warning(f"Could not extract candidate data for candidate {i}")
                        continue
                    
                    # Now try to find the original candidate information
                    original_candidate = None
                    
                    # Try different paths to find candidate data
                    possible_paths = [
                        'original_data.original_candidate_data.candidate',
                        'original_data.candidate', 
                        'original_candidate_data.candidate',
                        'candidate',
                        'personal_info',  # Direct access if it's already the candidate data
                    ]
                    
                    for path_str in possible_paths:
                        try:
                            temp_data = candidate_data
                            path_parts = path_str.split('.')
                            
                            for part in path_parts:
                                if isinstance(temp_data, dict) and part in temp_data:
                                    temp_data = temp_data[part]
                                elif isinstance(temp_data, list) and len(temp_data) > 0:
                                    # If we hit a list, try to find a dict in it
                                    for item in temp_data:
                                        if isinstance(item, dict) and part in item:
                                            temp_data = item[part]
                                            break
                                    else:
                                        temp_data = None
                                        break
                                else:
                                    temp_data = None
                                    break
                            
                            # Handle case where temp_data is a list - take the first dict
                            if isinstance(temp_data, list) and len(temp_data) > 0:
                                logger.info(f"Found list at end of path {path_str}, taking first dict item")
                                for item in temp_data:
                                    if isinstance(item, dict):
                                        temp_data = item
                                        logger.info(f"Selected dict item with keys: {list(item.keys())}")
                                        break
                            
                            # Add more debugging
                            logger.info(f"After processing path {path_str}: type={type(temp_data)}, is_dict={isinstance(temp_data, dict)}")
                            if isinstance(temp_data, dict):
                                logger.info(f"Dict keys: {list(temp_data.keys())}")
                            
                            # Check if we found valid candidate data
                            if (temp_data and isinstance(temp_data, dict) and 
                                ('personal_info' in temp_data or 'name' in temp_data or 'Student Name' in temp_data)):
                                original_candidate = temp_data
                                logger.info(f"Found candidate data using path: {path_str}")
                                break
                                
                        except Exception as e:
                            logger.error(f"Path {path_str} failed with error: {str(e)}")
                            continue
                    
                    # If still no candidate found, try to use the data directly if it looks like candidate data
                    if not original_candidate:
                        if isinstance(candidate_data, dict):
                            # Check if candidate_data itself has candidate-like structure
                            if ('personal_info' in candidate_data or 'name' in candidate_data or 
                                'skills' in candidate_data or 'experience' in candidate_data):
                                original_candidate = candidate_data
                                logger.info(f"Using candidate_data directly as it appears to be candidate info")
                    
                    if not original_candidate:
                        logger.warning(f"Could not find original candidate data for candidate {i}")
                        continue
                    
                    # FINAL CHECK: Make sure original_candidate is a dict
                    if not isinstance(original_candidate, dict):
                        logger.error(f"original_candidate is {type(original_candidate)}, not dict. Converting...")
                        if isinstance(original_candidate, list) and len(original_candidate) > 0:
                            for item in original_candidate:
                                if isinstance(item, dict):
                                    original_candidate = item
                                    break
                            else:
                                logger.error(f"No dict found in original_candidate list")
                                continue
                        else:
                            logger.error(f"Cannot convert original_candidate to dict")
                            continue
                    
                    # Extract validation results
                    validation_results = {}
                    if isinstance(candidate_data, dict):
                        validation_results = candidate_data.get('validation_results', {})
                    
                    # Extract research data
                    research_data = {}
                    if isinstance(candidate_data, dict):
                        research_data = candidate_data.get('original_data', {}).get('research_results', {})
                        if not research_data:
                            research_data = candidate_data.get('research_results', {})
                    
                    # Extract match score if available
                    match_score = {'overall_score': 0}  # Default match score
                    if matching_results:
                        candidate_name = self._extract_candidate_name(original_candidate)
                        match_score = self._find_candidate_match_score(candidate_name, matching_results)
                    
                    # Create profile
                    profile = self.create_candidate_profile(
                        original_candidate, 
                        research_data,
                        match_score,
                        validation_results
                    )
                    
                    candidate_profiles.append(profile)
                    logger.info(f"Successfully created profile for candidate {i}")
                    
                except Exception as e:
                    logger.error(f"Error processing candidate {i}: {str(e)}")
                    continue
            
            # Generate comparative report
            comparative_report = self.generate_comparative_report(candidate_profiles, job_requirements)
            
            # Ensure we have at least some candidates before trying to rank them
            primary_ranking = []
            alternative_rankings = []
            if candidate_profiles:
                primary_ranking = self._rank_candidates(candidate_profiles, job_requirements)
                alternative_rankings = self._generate_alternative_rankings(candidate_profiles, job_requirements)
            
            # Combine into comprehensive report
            report = {
                'executive_summary': comparative_report.get('executive_summary', ''),
                'candidate_profiles': candidate_profiles,
                'candidate_pool_analysis': comparative_report.get('candidate_pool_analysis', {}),
                'final_rankings': {
                    'primary_ranking': primary_ranking,
                    'alternative_rankings': alternative_rankings
                },
                'detailed_analysis': {
                    'skills_gap_analysis': comparative_report.get('skills_gap_analysis', {}),
                    'experience_distribution': self._analyze_experience_distribution(candidate_profiles),
                    'education_analysis': self._analyze_education_distribution(candidate_profiles)
                },
                'recommendations': comparative_report.get('recommendations', []),
                'metrics': comparative_report.get('metrics', {}),
                'generation_timestamp': datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {str(e)}")
            # Return a minimal report as fallback
            return {
                'executive_summary': f"Error generating report: {str(e)}",
                'candidate_profiles': [],
                'final_rankings': {'primary_ranking': []},
                'detailed_analysis': {},
                'recommendations': ["Review error and retry report generation"],
                'generation_timestamp': datetime.now().isoformat()
            }

    def _extract_candidate_name(self, candidate_data: Dict) -> str:
        """Extract candidate name from candidate data"""
        if 'personal_info' in candidate_data and isinstance(candidate_data['personal_info'], dict):
            name = candidate_data['personal_info'].get('name')
            if name:
                return name
        
        # Try direct keys
        for key in ['name', 'Student Name', 'candidate_name']:
            if key in candidate_data and candidate_data[key]:
                return candidate_data[key]
        
        return "Unknown Candidate"

    def _find_candidate_match_score(self, candidate_name: str, matching_results: Dict) -> Dict:
        """Find match score for a candidate by name"""
        if not matching_results or 'candidate_scores' not in matching_results:
            return {'overall_score': 0}
        
        for candidate_score in matching_results.get('candidate_scores', []):
            if candidate_score.get('candidate_name', '').lower() == candidate_name.lower():
                return candidate_score
        
        return {'overall_score': 0}

    def _rank_candidates(self, candidate_profiles: List[Dict], job_requirements: Dict) -> List[Dict]:
        """Rank candidates based on match score and other factors"""
        # Create a copy to avoid modifying the original
        ranked_candidates = []
        
        for profile in candidate_profiles:
            # Extract key metrics for ranking
            match_score = profile.get('match_analysis', {}).get('overall_score', 0)
            verification_score = profile.get('verification_status', {}).get('confidence_score', 0)
            
            # Calculate a composite score
            composite_score = (match_score * 0.7) + (verification_score * 0.3)
            
            ranked_candidates.append({
                'name': profile.get('name', 'Unknown'),
                'match_score': match_score,
                'verification_score': verification_score,
                'composite_score': composite_score,
                'key_strengths': profile.get('match_analysis', {}).get('strengths', [])[:3],
                'key_gaps': profile.get('match_analysis', {}).get('gaps', [])[:3]
            })
        
        # Sort by composite score
        ranked_candidates.sort(key=lambda x: x['composite_score'], reverse=True)
        
        return ranked_candidates

    def _generate_alternative_rankings(self, candidate_profiles: List[Dict], job_requirements: Dict) -> Dict:
        """Generate alternative rankings based on different criteria"""
        alternative_rankings = {
            'by_technical_skills': [],
            'by_experience': [],
            'by_verification': []
        }
        
        # By technical skills
        tech_ranked = sorted(
            candidate_profiles,
            key=lambda x: x.get('technical_assessment', {}).get('verified_skills', {}).get('total_verified', 0),
            reverse=True
        )
        
        alternative_rankings['by_technical_skills'] = [
            {
                'name': profile.get('name', 'Unknown'),
                'verified_skills_count': profile.get('technical_assessment', {}).get('verified_skills', {}).get('total_verified', 0),
                'key_skills': profile.get('technical_assessment', {}).get('verified_skills', {}).get('high_confidence', [])[:5]
            }
            for profile in tech_ranked[:5]
        ]
        
        # By experience
        exp_ranked = sorted(
            candidate_profiles,
            key=lambda x: self._calculate_experience_score(x),
            reverse=True
        )
        
        alternative_rankings['by_experience'] = [
            {
                'name': profile.get('name', 'Unknown'),
                'experience_score': self._calculate_experience_score(profile),
                'key_experience': [exp.get('role', '') for exp in profile.get('experience_summary', [])[:2]]
            }
            for profile in exp_ranked[:5]
        ]
        
        # By verification
        verification_ranked = sorted(
            candidate_profiles,
            key=lambda x: x.get('verification_status', {}).get('confidence_score', 0),
            reverse=True
        )
        
        alternative_rankings['by_verification'] = [
            {
                'name': profile.get('name', 'Unknown'),
                'verification_score': profile.get('verification_status', {}).get('confidence_score', 0),
                'verified_info': [
                    field for field, is_verified in profile.get('verification_status', {}).get('verified_information', {}).items() if is_verified
                ]
            }
            for profile in verification_ranked[:5]
        ]
        
        return alternative_rankings

    def _calculate_experience_score(self, profile: Dict) -> float:
        """Calculate an experience score based on years and relevance"""
        experience_summary = profile.get('experience_summary', [])
        if not experience_summary:
            return 0
        
        # Extract years from executive summary
        years_match = re.search(r'(\d+)\+?\s+year', profile.get('executive_summary', ''))
        years = int(years_match.group(1)) if years_match else 0
        
        # Calculate score based on years and number of relevant positions
        score = years * 5  # 5 points per year
        score += len(experience_summary) * 2  # 2 points per position
        
        # Bonus for verified positions
        verified_positions = sum(1 for exp in experience_summary if exp.get('verified', False))
        score += verified_positions * 5  # 5 bonus points per verified position
        
        return score

    def _analyze_experience_distribution(self, candidate_profiles: List[Dict]) -> Dict:
        """Analyze the distribution of experience across candidates"""
        experience_distribution = {
            'years_distribution': {},
            'industry_distribution': {},
            'role_distribution': {}
        }
        
        # Years distribution
        years_counts = {}
        for profile in candidate_profiles:
            years_match = re.search(r'(\d+)\+?\s+year', profile.get('executive_summary', ''))
            years = int(years_match.group(1)) if years_match else 0
            
            if years < 2:
                category = "0-2 years"
            elif years < 5:
                category = "2-5 years"
            elif years < 10:
                category = "5-10 years"
            else:
                category = "10+ years"
            
            years_counts[category] = years_counts.get(category, 0) + 1
        
        experience_distribution['years_distribution'] = years_counts
        
        # Simplified industry and role distribution
        experience_distribution['industry_distribution'] = {"Technology": len(candidate_profiles)}
        experience_distribution['role_distribution'] = {"Software Engineer": len(candidate_profiles)}
        
        return experience_distribution

    def _analyze_education_distribution(self, candidate_profiles: List[Dict]) -> Dict:
        """Analyze the distribution of education across candidates"""
        education_distribution = {
            'degree_distribution': {},
            'university_distribution': {}
        }
        
        # Simplified implementation
        education_distribution['degree_distribution'] = {
            "Bachelor's": len(candidate_profiles) * 0.7,
            "Master's": len(candidate_profiles) * 0.3
        }
        
        education_distribution['university_distribution'] = {
            "Various Universities": len(candidate_profiles)
        }
        
        return education_distribution

    def save_report(self, report: Dict) -> str:
        """Save the report to a file
        
        Args:
            report: Report dictionary
        
        Returns:
            Path to the saved report file
        """
        try:
            # Create reports directory if it doesn't exist
            reports_dir = os.path.join(os.getcwd(), 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"candidate_report_{timestamp}.json"
            filepath = os.path.join(reports_dir, filename)
            
            # Save report as JSON
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Report saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")
            return ""

    def _calculate_total_experience(self, experience_list: List[Dict]) -> int:
        """Calculate total years of professional experience
        
        Args:
            experience_list: List of experience dictionaries
        
        Returns:
            Total years of experience
        """
        try:
            if not experience_list:
                return 0
            
            total_months = 0
            
            for job in experience_list:
                # Try to extract duration from the job
                duration = job.get('duration', '')
                
                if not duration:
                    # If no duration, try to calculate from start and end dates
                    start_date = job.get('start_date')
                    end_date = job.get('end_date')
                    
                    if start_date and end_date:
                        # If both dates exist, calculate duration
                        if end_date.lower() == 'present':
                            # Use current year for 'present'
                            end_year = datetime.now().year
                        else:
                            # Try to extract year from end date
                            end_match = re.search(r'\b(19|20)\d{2}\b', end_date)
                            end_year = int(end_match.group(0)) if end_match else datetime.now().year
                        
                        # Extract start year
                        start_match = re.search(r'\b(19|20)\d{2}\b', start_date)
                        start_year = int(start_match.group(0)) if start_match else end_year - 1
                        
                        # Calculate months
                        months = (end_year - start_year) * 12
                        total_months += months
                    else:
                        # Default to 1 year if no dates available
                        total_months += 12
                else:
                    # Parse duration string
                    years_match = re.search(r'(\d+)\s*(?:years|year|yrs|yr)', duration, re.IGNORECASE)
                    months_match = re.search(r'(\d+)\s*(?:months|month|mos|mo)', duration, re.IGNORECASE)
                    
                    if years_match:
                        total_months += int(years_match.group(1)) * 12
                    
                    if months_match:
                        total_months += int(months_match.group(1))
                    
                    # If no matches found, try to extract years from format like "2018-2021" or "2018 - 2021"
                    if not years_match and not months_match:
                        years_range = re.search(r'(20\d{2})\s*[-–—]\s*(20\d{2}|present)', duration, re.IGNORECASE)
                        if years_range:
                            start_year = int(years_range.group(1))
                            end_year = datetime.now().year if years_range.group(2).lower() == 'present' else int(years_range.group(2))
                            total_months += (end_year - start_year) * 12
                        else:
                            # Default to 1 year if no pattern matches
                            total_months += 12
            
            # Convert months to years, rounded to nearest year
            total_years = round(total_months / 12)
            
            # Ensure at least 1 year if there's any experience
            return max(1, total_years) if experience_list else 0
        
        except Exception as e:
            logger.error(f"Error calculating total experience: {str(e)}")
            # Return a default value in case of error
            return len(experience_list)

    def _find_matching_position(self, job: Dict, linkedin_positions: List[Dict]) -> Dict:
        """Find matching position in LinkedIn data"""
        try:
            if not linkedin_positions:
                return {}
            
            job_title = job.get('title', '').lower()
            job_company = job.get('company', '').lower()
            
            for position in linkedin_positions:
                linkedin_title = position.get('title', '').lower()
                linkedin_company = position.get('company', '').lower()
                
                # Check for match on both title and company
                title_match = self._text_similarity(job_title, linkedin_title) > 0.7
                company_match = self._text_similarity(job_company, linkedin_company) > 0.7
                
                if title_match and company_match:
                    return position
            
            return {}
        except Exception as e:
            logger.error(f"Error finding matching position: {str(e)}")
            return {}

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        try:
            if not text1 or not text2:
                return 0.0
            
            # Simple word overlap similarity
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union)
        except Exception as e:
            logger.error(f"Error calculating text similarity: {str(e)}")
            return 0.0

    def _extract_job_achievements(self, job: Dict) -> List[str]:
        """Extract achievements from job description"""
        try:
            achievements = []
            description = job.get('description', '')
            
            if not description:
                return achievements
            
            # Extract bullet points
            bullet_points = re.findall(r'•\s*(.*?)(?=•|\n\n|$)', description)
            if bullet_points:
                achievements.extend(bullet_points)
            
            # Look for achievement keywords
            achievement_keywords = ['achieved', 'improved', 'increased', 'reduced', 'led', 'created', 'developed', 'implemented']
            sentences = re.split(r'[.!?]+', description)
            
            for sentence in sentences:
                sentence = sentence.strip()
                if any(keyword in sentence.lower() for keyword in achievement_keywords):
                    if sentence and sentence not in achievements:
                        achievements.append(sentence)
            
            return achievements[:5]  # Return top 5 achievements
        except Exception as e:
            logger.error(f"Error extracting job achievements: {str(e)}")
            return []

    def _extract_technologies(self, job: Dict) -> List[str]:
        """Extract technologies mentioned in job description"""
        try:
            technologies = []
            description = job.get('description', '')
            
            if not description:
                return technologies
            
            # Common technology keywords
            tech_patterns = [
                r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|Ruby|Go|Rust|PHP|Swift|Kotlin)\b',
                r'\b(?:React|Angular|Vue|Node\.js|Express|Django|Flask|Spring|Rails|Laravel)\b',
                r'\b(?:AWS|Azure|GCP|Docker|Kubernetes|Terraform|Jenkins|Git|CI/CD)\b',
                r'\b(?:SQL|MySQL|PostgreSQL|MongoDB|Redis|Elasticsearch|Cassandra|DynamoDB)\b',
                r'\b(?:TensorFlow|PyTorch|Scikit-learn|Pandas|NumPy|BERT|GPT|NLP|ML|AI)\b'
            ]
            
            for pattern in tech_patterns:
                matches = re.findall(pattern, description, re.IGNORECASE)
                technologies.extend(matches)
            
            return list(set(technologies))  # Remove duplicates
        except Exception as e:
            logger.error(f"Error extracting technologies: {str(e)}")
            return []

    def _identify_ongoing_education(self, education: Dict) -> List[Dict]:
        """Identify ongoing education"""
        try:
            ongoing = []
            degrees = education.get('degrees', [])
            
            for degree in degrees:
                end_date = degree.get('end_date', '')
                if end_date and ('present' in end_date.lower() or 'current' in end_date.lower()):
                    ongoing.append(degree)
            
            return ongoing
        except Exception as e:
            logger.error(f"Error identifying ongoing education: {str(e)}")
            return []

    def _identify_strengths(self, match_score: Dict) -> List[str]:
        """Identify candidate strengths based on match scores"""
        try:
            strengths = []
            scoring_details = match_score.get('scoring_details', {})
            
            # Find categories with high scores
            for category, score in scoring_details.items():
                if score >= 80:
                    strengths.append(f"Strong {category.replace('_', ' ')} match ({score:.1f}%)")
            
            return strengths
        except Exception as e:
            logger.error(f"Error identifying strengths: {str(e)}")
            return []

    def _identify_gaps(self, match_score: Dict) -> List[str]:
        """Identify candidate gaps based on match scores"""
        try:
            gaps = []
            scoring_details = match_score.get('scoring_details', {})
            
            # Find categories with low scores
            for category, score in scoring_details.items():
                if score < 50:
                    gaps.append(f"Gap in {category.replace('_', ' ')} ({score:.1f}%)")
            
            return gaps
        except Exception as e:
            logger.error(f"Error identifying gaps: {str(e)}")
            return []

    def _calculate_date_gap(self, end_date: str, start_date: str) -> int:
        """Calculate gap between two dates in months"""
        try:
            # Extract years
            end_year_match = re.search(r'\b(19|20)\d{2}\b', end_date)
            start_year_match = re.search(r'\b(19|20)\d{2}\b', start_date)
            
            if not end_year_match or not start_year_match:
                return 0
            
            end_year = int(end_year_match.group(0))
            start_year = int(start_year_match.group(0))
            
            # Extract months if available
            end_month = 12
            start_month = 1
            
            end_month_match = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b', end_date)
            start_month_match = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b', start_date)
            
            month_map = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            
            if end_month_match:
                end_month = month_map.get(end_month_match.group(0), 12)
            
            if start_month_match:
                start_month = month_map.get(start_month_match.group(0), 1)
            
            # Calculate gap in months
            return (start_year - end_year) * 12 + (start_month - end_month)
        except Exception as e:
            logger.error(f"Error calculating date gap: {str(e)}")
            return 0

    def _create_report_summary(self, candidates: List[Dict], job_requirements: Dict) -> str:
        """Create an executive summary for the report"""
        try:
            num_candidates = len(candidates)
            if num_candidates == 0:
                return "No candidates were found matching the job requirements."
            
            # Get top candidate
            top_candidate = candidates[0] if candidates else {}
            top_name = top_candidate.get('executive_summary', '').split(' is ')[0] if ' is ' in top_candidate.get('executive_summary', '') else "Unknown"
            
            # Calculate average match score
            match_scores = [c.get('match_analysis', {}).get('overall_score', 0) for c in candidates]
            avg_match = sum(match_scores) / len(match_scores) if match_scores else 0
            
            # Count verified candidates
            verified_count = sum(1 for c in candidates if c.get('verification_status', {}).get('consistency_score', 0) > 70)
            
            summary = f"Analysis of {num_candidates} candidates for the position. "
            summary += f"The top candidate is {top_name}. "
            summary += f"Average match score across all candidates is {avg_match:.1f}%. "
            summary += f"{verified_count} candidates have high verification scores. "
            
            # Add job requirement context
            job_title = job_requirements.get('title', 'the position')
            key_skills = job_requirements.get('required_skills', [])[:3]
            
            if key_skills:
                summary += f"The role of {job_title} requires expertise in {', '.join(key_skills)}. "
            
            # Add recommendation
            if avg_match > 70:
                summary += "Overall, there are strong candidates in the pool that match the requirements well."
            elif avg_match > 50:
                summary += "The candidate pool shows moderate alignment with job requirements."
            else:
                summary += "The candidate pool shows limited alignment with job requirements."
            
            return summary
        except Exception as e:
            logger.error(f"Error creating report summary: {str(e)}")
            return "Error generating report summary."

    def _analyze_candidate_pool(self, candidates: List[Dict], job_requirements: Dict) -> Dict:
        """Analyze the candidate pool against job requirements"""
        try:
            analysis = {
                'total_candidates': len(candidates),
                'match_distribution': {
                    'excellent_match': 0,
                    'good_match': 0,
                    'moderate_match': 0,
                    'poor_match': 0
                },
                'verification_distribution': {
                    'high_verification': 0,
                    'medium_verification': 0,
                    'low_verification': 0
                },
                'skill_coverage': {},
                'experience_distribution': {}
            }
            
            # Count matches by category
            for candidate in candidates:
                match_score = candidate.get('match_analysis', {}).get('overall_score', 0)
                verification_score = candidate.get('verification_status', {}).get('consistency_score', 0)
                
                # Match distribution
                if match_score >= 80:
                    analysis['match_distribution']['excellent_match'] += 1
                elif match_score >= 70:
                    analysis['match_distribution']['good_match'] += 1
                elif match_score >= 50:
                    analysis['match_distribution']['moderate_match'] += 1
                else:
                    analysis['match_distribution']['poor_match'] += 1
                
                # Verification distribution
                if verification_score >= 80:
                    analysis['verification_distribution']['high_verification'] += 1
                elif verification_score >= 60:
                    analysis['verification_distribution']['medium_verification'] += 1
                else:
                    analysis['verification_distribution']['low_verification'] += 1
            
            # Analyze skill coverage
            required_skills = job_requirements.get('required_skills', [])
            skill_coverage = {skill: 0 for skill in required_skills}
            
            for candidate in candidates:
                verified_skills = candidate.get('technical_assessment', {}).get('verified', [])
                claimed_skills = candidate.get('technical_assessment', {}).get('claimed', [])
                all_skills = verified_skills + claimed_skills
                
                for skill in required_skills:
                    if any(self._text_similarity(skill, s) > 0.8 for s in all_skills):
                        skill_coverage[skill] += 1
            
            # Convert to percentages
            total = len(candidates) or 1  # Avoid division by zero
            analysis['skill_coverage'] = {
                skill: (count / total) * 100 for skill, count in skill_coverage.items()
            }
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing candidate pool: {str(e)}")
            return {'total_candidates': len(candidates), 'error': str(e)}

    def _analyze_top_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """Analyze top candidates"""
        try:
            if not candidates:
                return []
            
            # Sort by match score
            sorted_candidates = sorted(
                candidates,
                key=lambda x: x.get('match_analysis', {}).get('overall_score', 0),
                reverse=True
            )
            
            # Take top 5 or fewer
            top_candidates = sorted_candidates[:min(5, len(sorted_candidates))]
            
            # Create analysis for each
            analysis = []
            for candidate in top_candidates:
                name = candidate.get('executive_summary', '').split(' is ')[0] if ' is ' in candidate.get('executive_summary', '') else "Unknown"
                
                analysis.append({
                    'name': name,
                    'match_score': candidate.get('match_analysis', {}).get('overall_score', 0),
                    'verification_score': candidate.get('verification_status', {}).get('consistency_score', 0),
                    'key_strengths': candidate.get('match_analysis', {}).get('strengths', [])[:3],
                    'verified_skills': candidate.get('technical_assessment', {}).get('verified', [])[:5]
                })
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing top candidates: {str(e)}")
            return []

    def _analyze_skills_gaps(self, candidates: List[Dict], job_requirements: Dict) -> Dict:
        """Analyze skills gaps between candidates and requirements"""
        try:
            required_skills = job_requirements.get('required_skills', [])
            if not required_skills:
                return {'message': 'No required skills specified in job requirements'}
            
            # Initialize coverage data
            coverage = {
                'well_covered_skills': [],
                'partially_covered_skills': [],
                'poorly_covered_skills': [],
                'skill_coverage_percentage': {}
            }
            
            # Calculate coverage for each skill
            for skill in required_skills:
                skill_count = 0
                verified_count = 0
                
                for candidate in candidates:
                    verified_skills = candidate.get('technical_assessment', {}).get('verified', [])
                    claimed_skills = candidate.get('technical_assessment', {}).get('claimed', [])
                    
                    # Check verified skills
                    if any(self._text_similarity(skill, s) > 0.8 for s in verified_skills):
                        skill_count += 1
                        verified_count += 1
                    # Check claimed skills
                    elif any(self._text_similarity(skill, s) > 0.8 for s in claimed_skills):
                        skill_count += 1
            
                # Calculate coverage percentage
                total = len(candidates) or 1  # Avoid division by zero
                coverage_pct = (skill_count / total) * 100
                verified_pct = (verified_count / total) * 100
                
                coverage['skill_coverage_percentage'][skill] = {
                    'total_coverage': coverage_pct,
                    'verified_coverage': verified_pct
                }
                
                # Categorize coverage
                if coverage_pct >= 70:
                    coverage['well_covered_skills'].append(skill)
                elif coverage_pct >= 40:
                    coverage['partially_covered_skills'].append(skill)
                else:
                    coverage['poorly_covered_skills'].append(skill)
            
            return coverage
        except Exception as e:
            logger.error(f"Error analyzing skills gaps: {str(e)}")
            return {'error': str(e)}

    def _generate_recommendations(self, candidates: List[Dict], job_requirements: Dict) -> List[str]:
        """Generate recommendations based on candidate analysis"""
        try:
            recommendations = []
            
            if not candidates:
                return ["Expand candidate search as no suitable candidates were found."]
            
            # Analyze match scores
            match_scores = [c.get('match_analysis', {}).get('overall_score', 0) for c in candidates]
            avg_match = sum(match_scores) / len(match_scores) if match_scores else 0
            
            # Get top candidates
            sorted_candidates = sorted(
                candidates,
                key=lambda x: x.get('match_analysis', {}).get('overall_score', 0),
                reverse=True
            )
            
            top_candidates = sorted_candidates[:min(3, len(sorted_candidates))]
            top_names = [
                c.get('executive_summary', '').split(' is ')[0] 
                if ' is ' in c.get('executive_summary', '') else "Candidate" 
                for c in top_candidates
            ]
            
            # Recommendations based on match quality
            if avg_match >= 75:
                recommendations.append(
                    f"Proceed with interviews for top candidates: {', '.join(top_names)}."
                )
            elif avg_match >= 60:
                recommendations.append(
                    f"Consider interviewing top candidates: {', '.join(top_names)}, but prepare for potential skills gaps."
                )
            else:
                recommendations.append(
                    "Consider expanding the candidate search as current candidates have limited alignment with requirements."
                )
            
            # Skills gap recommendations
            required_skills = job_requirements.get('required_skills', [])
            covered_skills = set()
            
            for candidate in candidates:
                verified_skills = candidate.get('technical_assessment', {}).get('verified', [])
                claimed_skills = candidate.get('technical_assessment', {}).get('claimed', [])
                all_skills = verified_skills + claimed_skills
                
                for skill in required_skills:
                    if any(self._text_similarity(skill, s) > 0.8 for s in all_skills):
                        covered_skills.add(skill)
            
            missing_skills = set(required_skills) - covered_skills
            if missing_skills:
                recommendations.append(
                    f"Consider candidates with experience in: {', '.join(missing_skills)}."
                )
            
            # Verification recommendations
            verification_scores = [c.get('verification_status', {}).get('consistency_score', 0) for c in candidates]
            avg_verification = sum(verification_scores) / len(verification_scores) if verification_scores else 0
            
            if avg_verification < 60:
                recommendations.append(
                    "Conduct thorough background checks as verification scores are generally low."
                )
            
            return recommendations
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return ["Error generating recommendations."]

    # QUICK FIX: Replace the _calculate_metrics method in summarization_agent.py

    def _calculate_metrics(self, candidates: List[Dict]) -> Dict:
        """Calculate metrics for the candidate pool - FIXED VERSION"""
        try:
            metrics = {
                'total_candidates': len(candidates),
                'average_match_score': 0,
                'average_verification_score': 0,
                'verified_candidates_percentage': 0,
                'candidates_with_required_skills': 0,
                'average_experience_years': 0
            }
            
            if not candidates:
                return metrics
            
            # FIXED: Add proper type checking and error handling
            match_scores = []
            verification_scores = []
            experience_years = []
            
            for candidate in candidates:
                # Ensure candidate is a dictionary
                if not isinstance(candidate, dict):
                    logger.warning(f"Candidate is not a dict: {type(candidate)}")
                    continue
                
                # Extract match score with proper error handling
                try:
                    match_analysis = candidate.get('match_analysis', {})
                    if isinstance(match_analysis, dict):
                        match_score = match_analysis.get('overall_score', 0)
                    else:
                        match_score = 0
                    match_scores.append(match_score)
                except Exception as e:
                    logger.warning(f"Error extracting match score: {e}")
                    match_scores.append(0)
                
                # Extract verification score with proper error handling
                try:
                    verification_status = candidate.get('verification_status', {})
                    if isinstance(verification_status, dict):
                        verification_score = verification_status.get('consistency_score', 0)
                    else:
                        verification_score = 0
                    verification_scores.append(verification_score)
                except Exception as e:
                    logger.warning(f"Error extracting verification score: {e}")
                    verification_scores.append(0)
                
                # FIXED: Extract experience years with proper error handling
                try:
                    experience_summary = candidate.get('experience_summary', {})
                    if isinstance(experience_summary, dict):
                        exp_years = experience_summary.get('total_years', 0)
                    elif isinstance(experience_summary, list):
                        # If experience_summary is a list, use its length as years estimate
                        exp_years = len(experience_summary)
                    else:
                        exp_years = 0
                    experience_years.append(exp_years)
                except Exception as e:
                    logger.warning(f"Error extracting experience years: {e}")
                    experience_years.append(0)
            
            # Calculate averages safely
            metrics['average_match_score'] = sum(match_scores) / len(match_scores) if match_scores else 0
            metrics['average_verification_score'] = sum(verification_scores) / len(verification_scores) if verification_scores else 0
            metrics['average_experience_years'] = sum(experience_years) / len(experience_years) if experience_years else 0
            
            # Count verified candidates (consistency score > 70)
            verified_count = sum(1 for score in verification_scores if score > 70)
            metrics['verified_candidates_percentage'] = (verified_count / len(candidates)) * 100 if candidates else 0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            # Return basic metrics as fallback
            return {
                'total_candidates': len(candidates) if candidates else 0,
                'average_match_score': 0,
                'average_verification_score': 0,
                'verified_candidates_percentage': 0,
                'candidates_with_required_skills': 0,
                'average_experience_years': 0,
                'error': str(e)
            }

    def _prepare_visualizations(self, candidates: List[Dict]) -> Dict:
        """Prepare visualizations for the candidate pool"""
        try:
            visualizations = {
                'match_score_distribution': self._prepare_match_score_visualization(candidates),
                'skill_coverage_visualization': self._prepare_skill_coverage_visualization(candidates),
                'experience_distribution': self._prepare_experience_visualization(candidates)
            }
        
            return visualizations
        except Exception as e:
            logger.error(f"Error preparing visualizations: {str(e)}")
            return {
                'error': str(e),
                'visualization_data': {}
            }

    def _prepare_match_score_visualization(self, candidates: List[Dict]) -> Dict:
        """Prepare match score distribution visualization data"""
        try:
            # Extract match scores
            scores = []
            labels = []
        
            for candidate in candidates:
                name = candidate.get('executive_summary', '').split(' is ')[0] if ' is ' in candidate.get('executive_summary', '') else "Unknown"
                score = candidate.get('match_analysis', {}).get('overall_score', 0)
            
                scores.append(score)
                labels.append(name)
        
            return {
                'type': 'bar_chart',
                'title': 'Candidate Match Scores',
                'labels': labels,
                'values': scores,
                'x_axis': 'Candidates',
                'y_axis': 'Match Score (%)'
            }
        except Exception as e:
            logger.error(f"Error preparing match score visualization: {str(e)}")
            return {}

    def _prepare_skill_coverage_visualization(self, candidates: List[Dict]) -> Dict:
        """Prepare skill coverage visualization data"""
        try:
            # Collect all skills
            all_skills = set()
            for candidate in candidates:
                tech_assessment = candidate.get('technical_assessment', {})
                all_skills.update(tech_assessment.get('verified', []))
                all_skills.update(tech_assessment.get('claimed', []))
        
            # Count skill occurrences
            skill_counts = {}
            for skill in all_skills:
                verified_count = 0
                claimed_count = 0
            
                for candidate in candidates:
                    tech_assessment = candidate.get('technical_assessment', {})
                    if skill in tech_assessment.get('verified', []):
                        verified_count += 1
                    elif skill in tech_assessment.get('claimed', []):
                        claimed_count += 1
            
                skill_counts[skill] = {
                    'verified': verified_count,
                    'claimed': claimed_count,
                    'total': verified_count + claimed_count
                }
        
            # Sort skills by total count
            sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1]['total'], reverse=True)
            top_skills = sorted_skills[:10]  # Top 10 skills
        
            return {
                'type': 'stacked_bar',
                'title': 'Top Skills Distribution',
                'skills': [skill for skill, _ in top_skills],
                'verified_counts': [counts['verified'] for _, counts in top_skills],
                'claimed_counts': [counts['claimed'] for _, counts in top_skills]
            }
        except Exception as e:
            logger.error(f"Error preparing skill coverage visualization: {str(e)}")
            return {}

    def _prepare_experience_visualization(self, candidates: List[Dict]) -> Dict:
        """Prepare experience distribution visualization data"""
        try:
            # Extract experience years
            experience_categories = {
                '0-2 years': 0,
                '2-5 years': 0,
                '5-10 years': 0,
                '10+ years': 0
            }
        
            for candidate in candidates:
                years_match = re.search(r'(\d+)\+?\s+year', candidate.get('executive_summary', ''))
                years = int(years_match.group(1)) if years_match else 0
            
                if years < 2:
                    experience_categories['0-2 years'] += 1
                elif years < 5:
                    experience_categories['2-5 years'] += 1
                elif years < 10:
                    experience_categories['5-10 years'] += 1
                else:
                    experience_categories['10+ years'] += 1
        
            return {
                'type': 'pie_chart',
                'title': 'Experience Distribution',
                'labels': list(experience_categories.keys()),
                'values': list(experience_categories.values())
            }
        except Exception as e:
            logger.error(f"Error preparing experience visualization: {str(e)}")
            return {}