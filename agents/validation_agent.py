from crewai import Agent, Task
import logging
from typing import Dict, List, Optional, Tuple
import json
import os
import re
from fuzzywuzzy import fuzz
import difflib
from datetime import datetime
import asyncio
from utils.gemini_llm import GeminiClient, get_gemini_llm, map_model_name

logger = logging.getLogger(__name__)

class ValidationAgent:
    def __init__(self, model="gemini-3.5-flash"):
        self.model_name = map_model_name(model)
        self.llm_client = GeminiClient(model=self.model_name)
        
        self.agent = Agent(
            role="Information Validation Agent",
            goal="Ensure accuracy and verify that all gathered information belongs to the correct candidate",
            backstory="""You are an expert information validator and identity verification specialist. 
            Your expertise lies in cross-referencing information from multiple sources, detecting 
            inconsistencies, and ensuring that all research data accurately belongs to the intended 
            candidate. You understand the importance of preventing identity mix-ups and false 
            associations in recruitment processes. You use advanced techniques including name 
            matching, biographical consistency checks, and timeline validation.""",
            verbose=True,
            llm=get_gemini_llm(model=self.model_name),
            allow_delegation=False
        )
    
    def create_tasks(self, researched_candidates: List[Dict]) -> List[Task]:
        """Create validation tasks for researched candidates"""
        
        comprehensive_validation_task = Task(
            description=f"""Validate the research information for {len(researched_candidates)} candidates to ensure accuracy and correct identity association.

RESEARCHED CANDIDATES TO VALIDATE:
{json.dumps([{
    'name': c.get('original_candidate_data', {}).get('candidate', {}).get('personal_info', {}).get('name', ''),
    'research_success': c.get('research_successful', False),
    'platforms_found': list(c.get('research_results', {}).keys())
} for c in researched_candidates], indent=2)}

For each candidate, perform comprehensive validation:

1. **Identity Verification**:
   - Verify that all found profiles belong to the same person
   - Check name consistency across platforms
   - Validate biographical information alignment
   - Detect potential identity mix-ups or false matches
   - Cross-reference contact information when available

2. **Information Consistency Checks**:
   - Verify that skills mentioned in resume match skills demonstrated online
   - Check timeline consistency in employment and education history
   - Validate project descriptions and technical expertise claims
   - Ensure location and background information aligns

3. **Source Credibility Assessment**:
   - Evaluate the reliability of each information source
   - Check for recent activity vs. outdated information
   - Assess the quality and authenticity of online profiles
   - Identify any suspicious or fabricated information

4. **Data Quality Validation**:
   - Verify that extracted information is accurately represented
   - Check for scraping errors or misinterpretations
   - Validate that links and URLs are correctly associated
   - Ensure that technical skills are properly categorized

5. **Completeness Assessment**:
   - Identify information gaps that need further verification
   - Assess the overall research quality for each candidate
   - Determine confidence levels for different data points
   - Flag candidates requiring manual review

6. **Error Detection and Correction**:
   - Identify and flag any inconsistencies or errors
   - Suggest corrections where appropriate
   - Mark uncertain information for manual verification
   - Provide confidence scores for each data point

VALIDATION CRITERIA:
- Name similarity threshold: 80% (adjustable based on context)
- Location consistency: Major geographical areas should align
- Timeline logic: Employment/education dates should be reasonable
- Skill consistency: Online activities should reflect claimed skills
- Profile authenticity: Check for signs of genuine vs. fake profiles

OUTPUT REQUIREMENTS:
- Clear validation status for each candidate (Verified/Questionable/Invalid)
- Detailed breakdown of what was verified vs. what needs review
- Confidence scores for different aspects of information
- Specific flags for any issues found
- Recommendations for follow-up actions""",
            expected_output="""Comprehensive validation report for each candidate including:
- Overall validation status and confidence score
- Identity verification results with detailed reasoning
- Information consistency analysis
- Source credibility assessment
- Data quality metrics
- Specific issues or red flags identified
- Corrected/cleaned information where applicable
- Recommendations for each candidate (Proceed/Manual Review/Reject)
- Summary of validation methodology used""",
            agent=self.agent
        )
        
        return [comprehensive_validation_task]
    
    def validate_candidates(self, researched_candidates: List[Dict]) -> List[Dict]:
        """Validate all researched candidates"""
        validated_candidates = []
        
        for i, candidate_data in enumerate(researched_candidates):
            candidate_name = self._extract_candidate_name(candidate_data)
            logger.info(f"Validating candidate {i+1}/{len(researched_candidates)}: {candidate_name}")
            
            try:
                validation_result = self._comprehensive_validation(candidate_data)
                
                validated_candidate = {
                    'original_data': candidate_data,
                    'validation_results': validation_result,
                    'validation_timestamp': datetime.now().isoformat(),
                    'validation_successful': True
                }
                
                validated_candidates.append(validated_candidate)
                
            except Exception as e:
                logger.error(f"Error validating candidate {candidate_name}: {str(e)}")
                validated_candidates.append({
                    'original_data': candidate_data,
                    'validation_results': {'error': str(e)},
                    'validation_timestamp': datetime.now().isoformat(),
                    'validation_successful': False
                })
        
        return validated_candidates
    
    def _comprehensive_validation(self, candidate_data: Dict) -> Dict:
        """Perform comprehensive validation on a single candidate"""
        
        original_candidate = candidate_data.get('original_candidate_data', {}).get('candidate', {})
        research_results = candidate_data.get('research_results', {})
        
        validation_results = {
            'overall_status': 'Unknown',
            'confidence_score': 0.0,
            'identity_verification': {},
            'information_consistency': {},
            'source_credibility': {},
            'data_quality': {},
            'issues_found': [],
            'corrections_made': [],
            'recommendations': [],
            'detailed_analysis': {}
        }
        
        # 1. Identity Verification
        validation_results['identity_verification'] = self._verify_identity(original_candidate, research_results)
        
        # 2. Information Consistency
        validation_results['information_consistency'] = self._check_information_consistency(original_candidate, research_results)
        
        # 3. Source Credibility
        validation_results['source_credibility'] = self._assess_source_credibility(research_results)
        
        # 4. Data Quality
        validation_results['data_quality'] = self._validate_data_quality(research_results)
        
        # 5. Calculate Overall Score and Status
        validation_results['confidence_score'] = self._calculate_overall_confidence(validation_results)
        validation_results['overall_status'] = self._determine_overall_status(validation_results['confidence_score'])
        
        # 6. Generate Issues and Recommendations
        validation_results['issues_found'] = self._identify_issues(validation_results)
        validation_results['recommendations'] = self._generate_recommendations(validation_results)
        
        # 7. LLM-powered Analysis
        if self.llm_client:
            validation_results['llm_analysis'] = self._llm_validate_candidate(original_candidate, research_results, validation_results)
        
        return validation_results
    
    def _verify_identity(self, original_candidate: Dict, research_results: Dict) -> Dict:
        """Verify that all research results belong to the same candidate"""
        
        identity_verification = {
            'name_consistency': {},
            'contact_consistency': {},
            'biographical_consistency': {},
            'overall_identity_score': 0.0,
            'identity_confidence': 'Low'
        }
        
        # Extract original candidate information
        original_name = original_candidate.get('personal_info', {}).get('name', '')
        original_emails = original_candidate.get('contact_info', {}).get('emails', [])
        original_location = original_candidate.get('personal_info', {}).get('location', '')
        
        # 1. Name Consistency Check
        identity_verification['name_consistency'] = self._check_name_consistency(
            original_name, research_results
        )
        
        # 2. Contact Consistency Check
        identity_verification['contact_consistency'] = self._check_contact_consistency(
            original_emails, research_results
        )
        
        # 3. Biographical Consistency (simplified)
        identity_verification['biographical_consistency'] = {
            'score': 70,  # Default to somewhat consistent
            'matches': [],
            'discrepancies': [],
            'confidence': 'Medium'
        }
        
        # Calculate overall identity score
        scores = [
            identity_verification['name_consistency'].get('score', 0),
            identity_verification['contact_consistency'].get('score', 0),
            identity_verification['biographical_consistency'].get('score', 0)
        ]
        
        identity_verification['overall_identity_score'] = sum(scores) / len(scores) if scores else 0
        
        # Determine confidence level
        if identity_verification['overall_identity_score'] >= 80:
            identity_verification['identity_confidence'] = 'High'
        elif identity_verification['overall_identity_score'] >= 60:
            identity_verification['identity_confidence'] = 'Medium'
        else:
            identity_verification['identity_confidence'] = 'Low'
        
        return identity_verification
    
    def _check_biographical_consistency(self, original_candidate: Dict, research_results: Dict) -> Dict:
        """Check biographical information consistency"""
        bio_check = {
            'score': 70,  # Default to somewhat consistent
            'matches': [],
            'discrepancies': [],
            'confidence': 'Medium'
        }
        
        original_name = original_candidate.get('personal_info', {}).get('name', '').lower()
        if not original_name:
            bio_check['score'] = 50  # Neutral if no name provided
            bio_check['confidence'] = 'Low'
            return bio_check
        
        # Check name across platforms
        platforms = {
            'github': research_results.get('github', {}).get('profile', {}).get('name', ''),
            'linkedin': research_results.get('linkedin', {}).get('profile', {}).get('name', ''),
            'portfolio': research_results.get('portfolio_sites', [{}])[0].get('author', '')
        }
        
        matches = 0
        total_platforms = 0
        
        for platform, name in platforms.items():
            if name:
                total_platforms += 1
                if self._names_match(original_name, name.lower()):
                    matches += 1
                    bio_check['matches'].append(f"Name match found on {platform}")
                else:
                    bio_check['discrepancies'].append(
                        f"Name mismatch on {platform}: '{name}' vs '{original_name}'"
                    )
        
        if total_platforms > 0:
            bio_check['score'] = (matches / total_platforms) * 100
        
        if bio_check['score'] >= 80:
            bio_check['confidence'] = 'High'
        elif bio_check['score'] >= 50:
            bio_check['confidence'] = 'Medium'
        else:
            bio_check['confidence'] = 'Low'
        
        return bio_check
    
    def _check_location_consistency(self, original_location: str, research_results: Dict) -> Dict:
        """Check location consistency across platforms"""
        location_check = {
            'score': 50,  # Default to neutral
            'matches': [],
            'discrepancies': [],
            'confidence': 'Low'
        }
        
        if not original_location:
            return location_check
        
        original_location = original_location.lower()
        
        # Extract locations from different platforms
        locations = {
            'github': research_results.get('github', {}).get('profile', {}).get('location', ''),
            'linkedin': research_results.get('linkedin', {}).get('profile', {}).get('location', '')
        }
        
        # Portfolio location - safely handle potential list index error
        portfolio_sites = research_results.get('portfolio_sites', [])
        if portfolio_sites and len(portfolio_sites) > 0:
            locations['portfolio'] = portfolio_sites[0].get('location', '')
        else:
            locations['portfolio'] = ''
        
        matches = 0
        total_locations = 0
        
        for platform, location in locations.items():
            if location:
                total_locations += 1
                if self._locations_match(original_location, location.lower()):
                    matches += 1
                    location_check['matches'].append(f"Location match found on {platform}")
                else:
                    location_check['discrepancies'].append(
                        f"Location mismatch on {platform}: '{location}' vs '{original_location}'"
                    )
        
        if total_locations > 0:
            location_check['score'] = (matches / total_locations) * 100
        else:
            location_check['score'] = 50  # Neutral if no locations found
        
        # Set confidence level
        if location_check['score'] >= 80:
            location_check['confidence'] = 'High'
        elif location_check['score'] >= 50:
            location_check['confidence'] = 'Medium'
        else:
            location_check['confidence'] = 'Low'
        
        return location_check
    
    def _check_skill_consistency(self, original_skills: List[str], research_results: Dict) -> Dict:
        """Check skill consistency across platforms"""
        skill_check = {
            'score': 50,  # Start neutral
            'verified_skills': [],
            'unverified_skills': [],
            'additional_skills': [],
            'confidence': 'Low'
        }
        
        if not original_skills:
            return skill_check
        
        original_skills_clean = [skill.lower().strip() for skill in original_skills]
        research_skills = set()
        
        # GitHub repository languages
        github_repos = research_results.get('github', {}).get('repositories', [])
        for repo in github_repos:
            if repo.get('language'):
                research_skills.add(repo['language'].lower())
            for topic in repo.get('topics', []):
                research_skills.add(topic.lower())
        
        # Portfolio site technologies - safely access
        portfolio_sites = research_results.get('portfolio_sites', [])
        for site in portfolio_sites:
            for tech in site.get('technologies', []):
                research_skills.add(tech.lower())
        
        # Compare skills
        verified_count = 0
        for original_skill in original_skills_clean:
            if original_skill in research_skills:
                verified_count += 1
                skill_check['verified_skills'].append(original_skill)
            else:
                skill_check['unverified_skills'].append(original_skill)
        
        # Additional skills found in research
        skill_check['additional_skills'] = list(
            research_skills - set(original_skills_clean)
        )
        
        # Calculate score
        if original_skills_clean:
            skill_check['score'] = (verified_count / len(original_skills_clean)) * 100
        
        # Set confidence level
        if skill_check['score'] >= 80:
            skill_check['confidence'] = 'High'
        elif skill_check['score'] >= 50:
            skill_check['confidence'] = 'Medium'
        else:
            skill_check['confidence'] = 'Low'
        
        return skill_check

    # Helper methods for matching
    def _names_match(self, name1: str, name2: str) -> bool:
        """Check if names match using fuzzy matching"""
        if not name1 or not name2:
            return False
        
        try:
            from fuzzywuzzy import fuzz
            ratio = fuzz.ratio(name1.lower(), name2.lower())
            return ratio >= 85  # High threshold for names
        except ImportError:
            # Fallback if fuzzywuzzy is not available
            return name1.lower() in name2.lower() or name2.lower() in name1.lower()
    
    def _locations_match(self, loc1: str, loc2: str) -> bool:
        """Check if locations match using fuzzy matching"""
        if not loc1 or not loc2:
            return False
        
        try:
            from fuzzywuzzy import fuzz
            
            # Handle common location formats
            loc1 = loc1.replace(',', ' ').lower()
            loc2 = loc2.replace(',', ' ').lower()
            
            # First try exact match of city or state
            words1 = set(loc1.split())
            words2 = set(loc2.split())
            
            if words1 & words2:  # If there's any word overlap
                return True
            
            # Fall back to fuzzy matching
            ratio = fuzz.ratio(loc1, loc2)
            return ratio >= 70  # Lower threshold for locations
        except ImportError:
            # Fallback if fuzzywuzzy is not available
            return loc1.lower() in loc2.lower() or loc2.lower() in loc1.lower()
    
    def _skills_similar(self, skill1: str, skill2: str) -> bool:
        """Check if skills are similar using fuzzy matching"""
        if not skill1 or not skill2:
            return False
        
        try:
            from fuzzywuzzy import fuzz
            
            # Normalize skills
            skill1 = skill1.lower().replace('.js', '').replace('-', ' ')
            skill2 = skill2.lower().replace('.js', '').replace('-', ' ')
            
            # Common variations
            variations = {
                'javascript': ['js'],
                'typescript': ['ts'],
                'python': ['py'],
                'java': ['jdk'],
                'react': ['reactjs'],
                'node': ['nodejs'],
                'postgres': ['postgresql']
            }
            
            # Check if skills are variations of each other
            for main_skill, variants in variations.items():
                if skill1 == main_skill and skill2 in variants:
                    return True
                if skill2 == main_skill and skill1 in variants:
                    return True
            
            # Fall back to fuzzy matching
            ratio = fuzz.ratio(skill1, skill2)
            return ratio >= 85  # High threshold for skills
        except ImportError:
            # Fallback if fuzzywuzzy is not available
            return skill1.lower() in skill2.lower() or skill2.lower() in skill1.lower()

    def _assess_platform_credibility(self, platform_data: Dict) -> Dict:
        """Assess coding platform credibility"""
        credibility = {
            'score': 50,  # Neutral default
            'platforms_found': [],
            'indicators': []
        }
        
        if not platform_data:
            return credibility
        
        score = 0
        
        # Check each platform
        for platform, data in platform_data.items():
            credibility['platforms_found'].append(platform)
            
            # Account reputation
            if data.get('reputation', 0) > 1000:
                score += 20
                credibility['indicators'].append(f"High reputation on {platform}")
            elif data.get('reputation', 0) > 100:
                score += 10
                credibility['indicators'].append(f"Good reputation on {platform}")
            
            # Contributions/Activity
            if data.get('contributions', 0) > 50:
                score += 15
                credibility['indicators'].append(f"Active contributor on {platform}")
            elif data.get('contributions', 0) > 10:
                score += 5
                credibility['indicators'].append(f"Regular contributor on {platform}")
            
            # Achievements/Badges
            if data.get('achievements', []):
                score += 10
                credibility['indicators'].append(
                    f"Has {len(data['achievements'])} achievements on {platform}"
                )
            
            # Competition participation
            if data.get('competitions_participated', 0) > 0:
                score += 15
                credibility['indicators'].append(
                    f"Participated in {data['competitions_participated']} competitions on {platform}"
                )
        
        # Average score across platforms
        if platform_data:
            score = score / len(platform_data)
        
        credibility['score'] = min(score, 100)
        return credibility

    def _extract_candidate_name(self, candidate: Dict) -> str:
        """Extract candidate name from candidate data
        
        Args:
            candidate: Candidate data dictionary
        
        Returns:
            Candidate name or default if not found
        """
        # Try different possible locations for the name
        if 'personal_info' in candidate and isinstance(candidate['personal_info'], dict):
            name = candidate['personal_info'].get('name')
            if name:
                return name
        
        # Try direct keys
        for key in ['name', 'Student Name', 'candidate_name']:
            if key in candidate and candidate[key]:
                return candidate[key]
        
        # Try original data if available
        if 'original_data' in candidate and isinstance(candidate['original_data'], dict):
            for key in ['Student Name', 'name', 'candidate_name']:
                if key in candidate['original_data'] and candidate['original_data'][key]:
                    return candidate['original_data'][key]
        
        # Return a default if nothing found
        return f"Candidate {candidate.get('candidate_id', 'Unknown')}"

    def _check_name_consistency(self, original_name: str, research_results: Dict) -> Dict:
        """Check name consistency across platforms"""
        name_check = {
            'score': 0,
            'matches': [],
            'discrepancies': [],
            'confidence': 'Low'
        }
        
        if not original_name:
            name_check['score'] = 50  # Neutral if no name provided
            return name_check
        
        original_name = original_name.lower()
        
        # Extract names from different platforms
        names = {
            'github': research_results.get('github', {}).get('profile', {}).get('name', ''),
            'linkedin': research_results.get('linkedin', {}).get('profile', {}).get('name', ''),
        }
        
        # Safely get portfolio author if available
        portfolio_sites = research_results.get('portfolio_sites', [])
        if portfolio_sites and len(portfolio_sites) > 0:
            names['portfolio'] = portfolio_sites[0].get('author', '')
        else:
            names['portfolio'] = ''
        
        matches = 0
        total_names = 0
        
        for platform, name in names.items():
            if name:
                total_names += 1
                if self._names_match(original_name, name.lower()):
                    matches += 1
                    name_check['matches'].append(f"Name match found on {platform}")
                else:
                    name_check['discrepancies'].append(
                        f"Name mismatch on {platform}: '{name}' vs '{original_name}'"
                    )
        
        if total_names > 0:
            name_check['score'] = (matches / total_names) * 100
        else:
            name_check['score'] = 50  # Neutral if no names found
        
        if name_check['score'] >= 80:
            name_check['confidence'] = 'High'
        elif name_check['score'] >= 50:
            name_check['confidence'] = 'Medium'
        else:
            name_check['confidence'] = 'Low'
        
        return name_check

    def _check_contact_consistency(self, original_emails: List[str], research_results: Dict) -> Dict:
        """Check contact information consistency"""
        contact_check = {
            'score': 50,  # Default to neutral
            'matches': [],
            'discrepancies': [],
            'confidence': 'Low'
        }
        
        if not original_emails:
            return contact_check
        
        # Normalize original emails
        original_emails = [email.lower() for email in original_emails if email]
        
        # Extract emails from research results
        found_emails = []
        
        # GitHub email
        github_email = research_results.get('github', {}).get('profile', {}).get('email', '')
        if github_email:
            found_emails.append(github_email.lower())
        
        # LinkedIn email (rarely available)
        linkedin_email = research_results.get('linkedin', {}).get('profile', {}).get('email', '')
        if linkedin_email:
            found_emails.append(linkedin_email.lower())
        
        # Portfolio site email - safely access
        portfolio_sites = research_results.get('portfolio_sites', [])
        for site in portfolio_sites:
            site_email = site.get('contact_email', '')
            if site_email:
                found_emails.append(site_email.lower())
        
        # Check for matches
        matches = 0
        for original_email in original_emails:
            for found_email in found_emails:
                if original_email == found_email:
                    matches += 1
                    contact_check['matches'].append(f"Email match found: {original_email}")
                    break
        
        # Calculate score
        if found_emails:
            contact_check['score'] = (matches / len(original_emails)) * 100
        
        # If no emails found but we had original emails, slightly lower score
        if not found_emails and original_emails:
            contact_check['score'] = 40
            contact_check['discrepancies'].append("No contact information found in research results")
        
        # Set confidence level
        if contact_check['score'] >= 80:
            contact_check['confidence'] = 'High'
        elif contact_check['score'] >= 50:
            contact_check['confidence'] = 'Medium'
        else:
            contact_check['confidence'] = 'Low'
        
        return contact_check

    def _check_information_consistency(self, original_candidate: Dict, research_results: Dict) -> Dict:
        """Check information consistency across platforms"""
        consistency_check = {
            'skill_consistency': {},
            'location_consistency': {},
            'timeline_consistency': {},
            'overall_consistency_score': 0.0,
            'consistency_confidence': 'Low'
        }
        
        # 1. Skill Consistency
        original_skills = original_candidate.get('skills', {}).get('technical', [])
        consistency_check['skill_consistency'] = self._check_skill_consistency(original_skills, research_results)
        
        # 2. Location Consistency
        original_location = original_candidate.get('personal_info', {}).get('location', '')
        consistency_check['location_consistency'] = self._check_location_consistency(original_location, research_results)
        
        # 3. Timeline Consistency (simplified)
        consistency_check['timeline_consistency'] = {
            'score': 70,  # Default to somewhat consistent
            'issues': [],
            'confidence': 'Medium'
        }
        
        # Calculate overall consistency score
        scores = [
            consistency_check['skill_consistency'].get('score', 0),
            consistency_check['location_consistency'].get('score', 0),
            consistency_check['timeline_consistency'].get('score', 0)
        ]
        
        consistency_check['overall_consistency_score'] = sum(scores) / len(scores) if scores else 0
        
        # Determine confidence level
        if consistency_check['overall_consistency_score'] >= 80:
            consistency_check['consistency_confidence'] = 'High'
        elif consistency_check['overall_consistency_score'] >= 60:
            consistency_check['consistency_confidence'] = 'Medium'
        else:
            consistency_check['consistency_confidence'] = 'Low'
        
        return consistency_check

    def _assess_source_credibility(self, research_results: Dict) -> Dict:
        """Assess the credibility of research sources"""
        credibility = {
            'github_credibility': {},
            'linkedin_credibility': {},
            'portfolio_credibility': {},
            'coding_platform_credibility': {},
            'overall_credibility_score': 0.0,
            'credibility_confidence': 'Low'
        }
        
        # 1. GitHub Credibility
        github_data = research_results.get('github', {})
        if github_data:
            credibility['github_credibility'] = {
                'score': 70,  # Default to somewhat credible
                'indicators': []
            }
            
            # Check for profile completeness
            profile = github_data.get('profile', {})
            if profile.get('name') and profile.get('bio') and profile.get('location'):
                credibility['github_credibility']['score'] += 10
                credibility['github_credibility']['indicators'].append("Complete GitHub profile")
            
            # Check for repositories
            repos = github_data.get('repositories', [])
            if len(repos) > 5:
                credibility['github_credibility']['score'] += 10
                credibility['github_credibility']['indicators'].append(f"Active GitHub account with {len(repos)} repositories")
            
            # Check for contributions
            if github_data.get('contributions', 0) > 100:
                credibility['github_credibility']['score'] += 10
                credibility['github_credibility']['indicators'].append("Regular GitHub contributions")
        
        # 2. LinkedIn Credibility
        linkedin_data = research_results.get('linkedin', {})
        if linkedin_data:
            credibility['linkedin_credibility'] = {
                'score': 70,  # Default to somewhat credible
                'indicators': []
            }
            
            # Check for profile completeness
            profile = linkedin_data.get('profile', {})
            if profile.get('name') and profile.get('headline') and profile.get('location'):
                credibility['linkedin_credibility']['score'] += 10
                credibility['linkedin_credibility']['indicators'].append("Complete LinkedIn profile")
            
            # Check for experience
            experience = linkedin_data.get('experience', [])
            if len(experience) > 2:
                credibility['linkedin_credibility']['score'] += 10
                credibility['linkedin_credibility']['indicators'].append(f"LinkedIn profile with {len(experience)} experiences")
            
            # Check for education
            education = linkedin_data.get('education', [])
            if education:
                credibility['linkedin_credibility']['score'] += 10
                credibility['linkedin_credibility']['indicators'].append("LinkedIn profile with education history")
        
        # 3. Portfolio Credibility
        portfolio_sites = research_results.get('portfolio_sites', [])
        if portfolio_sites:
            credibility['portfolio_credibility'] = {
                'score': 70,  # Default to somewhat credible
                'indicators': []
            }
            
            # Check for portfolio completeness
            if portfolio_sites[0].get('author') and portfolio_sites[0].get('projects'):
                credibility['portfolio_credibility']['score'] += 15
                credibility['portfolio_credibility']['indicators'].append("Complete portfolio with projects")
            
            # Check for technologies
            if portfolio_sites[0].get('technologies'):
                credibility['portfolio_credibility']['score'] += 15
                credibility['portfolio_credibility']['indicators'].append("Portfolio with listed technologies")
        
        # 4. Coding Platform Credibility
        coding_platforms = research_results.get('coding_platforms', {})
        if coding_platforms:
            credibility['coding_platform_credibility'] = self._assess_platform_credibility(coding_platforms)
        
        # Calculate overall credibility score
        scores = []
        if 'github_credibility' in credibility and credibility['github_credibility']:
            scores.append(credibility['github_credibility'].get('score', 0))
        if 'linkedin_credibility' in credibility and credibility['linkedin_credibility']:
            scores.append(credibility['linkedin_credibility'].get('score', 0))
        if 'portfolio_credibility' in credibility and credibility['portfolio_credibility']:
            scores.append(credibility['portfolio_credibility'].get('score', 0))
        if 'coding_platform_credibility' in credibility and credibility['coding_platform_credibility']:
            scores.append(credibility['coding_platform_credibility'].get('score', 0))
        
        credibility['overall_credibility_score'] = sum(scores) / len(scores) if scores else 0
        
        # Determine confidence level
        if credibility['overall_credibility_score'] >= 80:
            credibility['credibility_confidence'] = 'High'
        elif credibility['overall_credibility_score'] >= 60:
            credibility['credibility_confidence'] = 'Medium'
        else:
            credibility['credibility_confidence'] = 'Low'
        
        return credibility

    def _validate_data_quality(self, research_results: Dict) -> Dict:
        """Validate the quality of research data"""
        quality = {
            'completeness': {},
            'accuracy': {},
            'recency': {},
            'overall_quality_score': 0.0,
            'quality_confidence': 'Low'
        }
        
        # 1. Completeness
        quality['completeness'] = {
            'score': 50,  # Default to medium completeness
            'indicators': []
        }
        
        # Check for key platforms
        platforms_found = []
        if research_results.get('github'):
            platforms_found.append('GitHub')
        if research_results.get('linkedin'):
            platforms_found.append('LinkedIn')
        if research_results.get('portfolio_sites'):
            platforms_found.append('Portfolio')
        if research_results.get('coding_platforms'):
            platforms_found.append('Coding Platforms')
        
        # Score based on platforms found
        if len(platforms_found) >= 3:
            quality['completeness']['score'] = 90
            quality['completeness']['indicators'].append(f"Found {len(platforms_found)} platforms: {', '.join(platforms_found)}")
        elif len(platforms_found) >= 2:
            quality['completeness']['score'] = 70
            quality['completeness']['indicators'].append(f"Found {len(platforms_found)} platforms: {', '.join(platforms_found)}")
        elif len(platforms_found) >= 1:
            quality['completeness']['score'] = 50
            quality['completeness']['indicators'].append(f"Found only {len(platforms_found)} platform: {', '.join(platforms_found)}")
        else:
            quality['completeness']['score'] = 20
            quality['completeness']['indicators'].append("No platforms found")
        
        # 2. Accuracy (simplified)
        quality['accuracy'] = {
            'score': 70,  # Default to somewhat accurate
            'indicators': []
        }
        
        # 3. Recency (simplified)
        quality['recency'] = {
            'score': 70,  # Default to somewhat recent
            'indicators': []
        }
        
        # Calculate overall quality score
        scores = [
            quality['completeness'].get('score', 0),
            quality['accuracy'].get('score', 0),
            quality['recency'].get('score', 0)
        ]
        
        quality['overall_quality_score'] = sum(scores) / len(scores) if scores else 0
        
        # Determine confidence level
        if quality['overall_quality_score'] >= 80:
            quality['quality_confidence'] = 'High'
        elif quality['overall_quality_score'] >= 60:
            quality['quality_confidence'] = 'Medium'
        else:
            quality['quality_confidence'] = 'Low'
        
        return quality

    def _calculate_overall_confidence(self, validation_results: Dict) -> float:
        """Calculate overall confidence score"""
        scores = [
            validation_results['identity_verification'].get('overall_identity_score', 0),
            validation_results['information_consistency'].get('overall_consistency_score', 0),
            validation_results['source_credibility'].get('overall_credibility_score', 0),
            validation_results['data_quality'].get('overall_quality_score', 0)
        ]
        
        return sum(scores) / len(scores) if scores else 0

    def _determine_overall_status(self, confidence_score: float) -> str:
        """Determine overall validation status based on confidence score"""
        if confidence_score >= 80:
            return "Verified"
        elif confidence_score >= 60:
            return "Questionable"
        else:
            return "Invalid"

    def _identify_issues(self, validation_results: Dict) -> List[str]:
        """Identify issues from validation results"""
        issues = []
        
        # Identity verification issues
        if validation_results['identity_verification'].get('overall_identity_score', 0) < 60:
            issues.append("Low identity verification confidence")
        
        # Add discrepancies from name consistency
        for discrepancy in validation_results['identity_verification'].get('name_consistency', {}).get('discrepancies', []):
            issues.append(discrepancy)
        
        # Add discrepancies from contact consistency
        for discrepancy in validation_results['identity_verification'].get('contact_consistency', {}).get('discrepancies', []):
            issues.append(discrepancy)
        
        # Information consistency issues
        if validation_results['information_consistency'].get('overall_consistency_score', 0) < 60:
            issues.append("Low information consistency confidence")
        
        # Source credibility issues
        if validation_results['source_credibility'].get('overall_credibility_score', 0) < 60:
            issues.append("Low source credibility confidence")
        
        # Data quality issues
        if validation_results['data_quality'].get('overall_quality_score', 0) < 60:
            issues.append("Low data quality confidence")
        
        return issues

    def _generate_recommendations(self, validation_results: Dict) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Overall status-based recommendations
        if validation_results['overall_status'] == "Verified":
            recommendations.append("Proceed with candidate evaluation")
        elif validation_results['overall_status'] == "Questionable":
            recommendations.append("Manual review recommended")
        else:
            recommendations.append("Reject or request additional information")
        
        # Specific recommendations based on issues
        if validation_results['identity_verification'].get('overall_identity_score', 0) < 60:
            recommendations.append("Verify candidate identity through direct contact")
        
        if validation_results['information_consistency'].get('overall_consistency_score', 0) < 60:
            recommendations.append("Request clarification on inconsistent information")
        
        if validation_results['source_credibility'].get('overall_credibility_score', 0) < 60:
            recommendations.append("Seek additional sources to verify candidate information")
        
        if validation_results['data_quality'].get('overall_quality_score', 0) < 60:
            recommendations.append("Gather more comprehensive data on the candidate")
        
        return recommendations

    def _llm_validate_candidate(self, original_candidate: Dict, research_results: Dict, validation_results: Dict) -> Dict:
        """Use LLM to validate candidate information"""
        try:
            # Prepare input for LLM
            candidate_name = original_candidate.get('personal_info', {}).get('name', 'Unknown')
            
            prompt = f"""
            Validate the following candidate information:
            
            CANDIDATE NAME: {candidate_name}
            
            ORIGINAL CANDIDATE DATA:
            {json.dumps(original_candidate, indent=2)}
            
            RESEARCH RESULTS:
            {json.dumps({k: v for k, v in research_results.items() if k in ['github', 'linkedin', 'portfolio_sites']}, indent=2)}
            
            VALIDATION RESULTS SO FAR:
            {json.dumps(validation_results, indent=2)}
            
            Please analyze this information and provide:
            1. An overall assessment of the candidate's identity verification
            2. Any inconsistencies or red flags you notice
            3. A confidence score (0-100) for the validation
            4. Recommendations for further verification if needed
            
            Format your response as JSON with the following structure:
            {{
                "overall_assessment": "string",
                "inconsistencies": ["string"],
                "confidence_score": number,
                "recommendations": ["string"]
            }}
            """
            
            # Call LLM
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a validation expert analyzing candidate information."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse response
            llm_analysis = json.loads(response.choices[0].message.content)
            
            return llm_analysis
        
        except Exception as e:
            logger.error(f"Error in LLM validation: {str(e)}")
            return {
                "overall_assessment": "Error in LLM validation",
                "inconsistencies": [],
                "confidence_score": 0,
                "recommendations": ["Manual review required due to LLM error"]
            }
