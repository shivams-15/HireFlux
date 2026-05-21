from crewai import Agent, Task
import logging
from typing import Dict, List, Tuple
import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
from utils.gemini_llm import GeminiClient, get_gemini_llm, map_model_name

logger = logging.getLogger(__name__)

class MatchingAgent:
    def __init__(self, model="gemini-3.5-flash"):
        self.model_name = map_model_name(model)
        self.llm_client = GeminiClient(model=self.model_name)
        
        self.agent = Agent(
            role="AI Matching Agent",
            goal="Intelligently evaluate candidates against job requirements using advanced matching algorithms",
            backstory="""You are an expert AI recruiter with deep understanding of job requirements 
            and candidate evaluation. You use advanced AI techniques including semantic similarity, 
            contextual understanding, and intelligent scoring algorithms to identify the best 
            candidates for each position. You understand that perfect matches are rare and focus 
            on finding candidates with the highest potential and transferable skills.""",
            verbose=True,
            llm=get_gemini_llm(model=self.model_name),
            allow_delegation=False
        )
    
    def create_tasks(self, job_description: str, processed_candidates: List[Dict]) -> List[Task]:
        """Create tasks for candidate matching"""
        
        analyze_job_task = Task(
            description=f"""Analyze the job description using advanced AI techniques to extract and structure all requirements.

JOB DESCRIPTION:
{job_description}

Extract and structure:
1. Required technical skills (must-have)
2. Preferred technical skills (nice-to-have)
3. Required soft skills and competencies
4. Required experience level and type
5. Required education/qualifications
6. Preferred background or industry experience
7. Key responsibilities and their importance
8. Company culture fit indicators
9. Growth potential requirements
10. Any domain-specific knowledge needed

Use AI to understand context and identify implicit requirements that may not be explicitly stated.
Assign importance weights to each requirement category based on the job description context.""",
            expected_output="""A comprehensive structured analysis of job requirements with:
- Categorized skills with importance weights
- Experience requirements with specificity levels
- Education requirements with flexibility indicators
- Cultural and soft skill requirements
- Implicit requirements derived from context
- Scoring criteria for candidate evaluation""",
            agent=self.agent
        )
        
        match_candidates_task = Task(
            description=f"""Evaluate and rank all {len(processed_candidates)} candidates against the job requirements using advanced AI matching.

PROCESSED CANDIDATES:
{json.dumps([{
    'id': c.get('candidate_id', i),
    'name': c.get('personal_info', {}).get('name', ''),
    'skills': c.get('skills', {}),
    'experience': c.get('experience', []),
    'education': c.get('education', [])
} for i, c in enumerate(processed_candidates)], indent=2)}

For each candidate:
1. Calculate semantic similarity scores for technical skills
2. Evaluate experience relevance and transferability
3. Assess education alignment and potential
4. Analyze project portfolio for practical skills demonstration
5. Evaluate soft skills and cultural fit indicators
6. Calculate overall match score with detailed breakdown
7. Identify key strengths and potential development areas
8. Assess growth potential and adaptability

Use advanced algorithms including:
- Semantic similarity for skill matching
- Contextual understanding for experience evaluation
- AI-powered gap analysis
- Potential assessment for emerging talents

Select the top 7-10 candidates for detailed research, ensuring diversity in backgrounds and approaches.""",
            expected_output="""A comprehensive ranking of all candidates with:
- Overall match scores (0-100) with detailed breakdown
- Top 7-10 candidates selected for further research
- Detailed scoring per category for each candidate
- Strengths and development areas for each candidate
- Justification for ranking decisions
- Alternative candidates worth considering
- Diversity and potential assessments""",
            agent=self.agent
        )
        
        return [analyze_job_task, match_candidates_task]
    
    def analyze_job_requirements(self, job_description: str) -> Dict:
        """Analyze job description using LLM to extract structured requirements"""
        if not self.llm_client:
            return self._fallback_job_analysis(job_description)
        
        try:
            prompt = f"""
Analyze this job description and extract structured requirements. Use AI to understand both explicit and implicit requirements.

JOB DESCRIPTION:
{job_description}

Extract and structure the following information:

1. **Technical Skills**:
   - Required (must-have) technical skills
   - Preferred (nice-to-have) technical skills
   - Assign importance weights (1-10) for each skill

2. **Experience Requirements**:
   - Minimum years of experience required
   - Type of experience needed (industry, role, technologies)
   - Leadership/management experience requirements
   - Specific domain knowledge needed

3. **Education Requirements**:
   - Required degree level and field
   - Preferred qualifications
   - Alternative qualifications accepted
   - Certification requirements

4. **Soft Skills & Competencies**:
   - Communication skills required
   - Teamwork and collaboration needs
   - Problem-solving abilities
   - Leadership qualities
   - Cultural fit indicators

5. **Role Context**:
   - Key responsibilities in order of importance
   - Team structure and collaboration needs
   - Growth opportunities and career path
   - Company stage and culture indicators

6. **Implicit Requirements**:
   - Skills that are implied but not explicitly mentioned
   - Industry knowledge that would be beneficial
   - Personality traits that would excel in this role

Return as JSON with importance weights and flexibility indicators.

RESPONSE FORMAT:
```json
{{
  "technical_skills": {{
    "required": [
      {{"skill": "Python", "weight": 9, "required": true}},
      {{"skill": "Machine Learning", "weight": 8, "required": true}}
    ],
    "preferred": [
      {{"skill": "Docker", "weight": 6, "required": false}},
      {{"skill": "AWS", "weight": 7, "required": false}}
    ]
  }},
  "experience": {{
    "min_years": 3,
    "required_types": ["Software Development", "API Development"],
    "preferred_types": ["Startup Experience", "Agile Environment"],
    "leadership_required": false
  }},
  "education": {{
    "required_level": "Bachelor's",
    "required_field": "Computer Science or related",
    "alternatives_accepted": true,
    "certifications": []
  }},
  "soft_skills": {{
    "communication": {{"weight": 8, "required": true}},
    "teamwork": {{"weight": 7, "required": true}},
    "problem_solving": {{"weight": 9, "required": true}},
    "leadership": {{"weight": 5, "required": false}}
  }},
  "role_context": {{
    "key_responsibilities": ["Develop software", "Collaborate with team"],
    "team_size": "Small",
    "growth_potential": "High",
    "company_stage": "Startup"
  }},
  "implicit_requirements": {{
    "adaptability": {{"weight": 7, "reasoning": "Startup environment requires flexibility"}},
    "learning_agility": {{"weight": 8, "reasoning": "Fast-paced technology changes"}}
  }},
  "scoring_weights": {{
    "technical_skills": 0.4,
    "experience": 0.25,
    "education": 0.15,
    "soft_skills": 0.15,
    "potential": 0.05
  }}
}}
```
"""
            
            # Use Gemini to generate response
            full_prompt = """You are an expert recruiter and job analyst. Extract comprehensive job requirements including implicit needs.

""" + prompt
            
            response_text = self.llm_client.generate_content(full_prompt)
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```\s*$', '', response_text)
            
            return json.loads(response_text)
            
        except Exception as e:
            logger.error(f"LLM job analysis failed: {e}")
            return self._fallback_job_analysis(job_description)
    
    def match_candidates(self, candidates: List[Dict], job_requirements: Dict) -> List[Dict]:
        """Match and rank candidates against job requirements"""
        scored_candidates = []
        
        for candidate in candidates:
            try:
                score_breakdown = self._calculate_comprehensive_score(candidate, job_requirements)
                
                scored_candidate = {
                    'candidate': candidate,
                    'overall_score': score_breakdown['overall_score'],
                    'score_breakdown': score_breakdown,
                    'strengths': self._identify_strengths(candidate, job_requirements),
                    'development_areas': self._identify_development_areas(candidate, job_requirements),
                    'potential_assessment': self._assess_potential(candidate, job_requirements),
                    'cultural_fit': self._assess_cultural_fit(candidate, job_requirements)
                }
                
                scored_candidates.append(scored_candidate)
                
            except Exception as e:
                logger.error(f"Error scoring candidate {candidate.get('personal_info', {}).get('name', 'Unknown')}: {e}")
                # Add candidate with error
                scored_candidates.append({
                    'candidate': candidate,
                    'overall_score': 0,
                    'error': str(e)
                })
        
        # Sort by overall score
        scored_candidates.sort(key=lambda x: x.get('overall_score', 0), reverse=True)
        
        # Select top candidates for research
        top_candidates = self._select_top_candidates(scored_candidates, min_candidates=7, max_candidates=10)
        
        return {
            'all_candidates': scored_candidates,
            'top_candidates': top_candidates,
            'selection_criteria': self._get_selection_criteria(job_requirements),
            'diversity_analysis': self._analyze_diversity(top_candidates)
        }
    
    def _calculate_comprehensive_score(self, candidate: Dict, job_requirements: Dict) -> Dict:
        """Calculate comprehensive matching score using multiple algorithms"""
        
        weights = job_requirements.get('scoring_weights', {
            'technical_skills': 0.4,
            'experience': 0.25,
            'education': 0.15,
            'soft_skills': 0.15,
            'potential': 0.05
        })
        
        scores = {}
        
        # Technical Skills Score
        scores['technical_skills'] = self._score_technical_skills(candidate, job_requirements)
        
        # Experience Score
        scores['experience'] = self._score_experience(candidate, job_requirements)
        
        # Education Score
        scores['education'] = self._score_education(candidate, job_requirements)
        
        # Soft Skills Score
        scores['soft_skills'] = self._score_soft_skills(candidate, job_requirements)
        
        # Potential Score
        scores['potential'] = self._score_potential(candidate, job_requirements)
        
        # Calculate weighted overall score
        overall_score = sum(scores[category] * weights.get(category, 0) for category in scores)
        
        return {
            'overall_score': round(overall_score, 2),
            'category_scores': scores,
            'weights_used': weights,
            'max_possible_score': 100
        }
    
    def _score_technical_skills(self, candidate: Dict, job_requirements: Dict) -> float:
        """Score technical skills using semantic similarity"""
        candidate_skills = candidate.get('skills', {}).get('technical', [])
        if not candidate_skills:
            return 0.0
        
        required_skills = job_requirements.get('technical_skills', {}).get('required', [])
        preferred_skills = job_requirements.get('technical_skills', {}).get('preferred', [])
        
        if not required_skills and not preferred_skills:
            return 50.0  # Neutral score if no requirements specified
        
        # Calculate semantic similarity scores
        required_score = self._calculate_skill_similarity(candidate_skills, required_skills, weight=0.7)
        preferred_score = self._calculate_skill_similarity(candidate_skills, preferred_skills, weight=0.3)
        
        total_score = required_score + preferred_score
        return min(total_score * 100, 100.0)
    
    def _calculate_skill_similarity(self, candidate_skills: List[str], required_skills: List[Dict], weight: float) -> float:
        """Calculate semantic similarity between candidate and required skills"""
        if not candidate_skills or not required_skills:
            return 0.0
        
        # Convert to text for TF-IDF
        candidate_text = ' '.join(candidate_skills).lower()
        required_texts = []
        skill_weights = []
        
        for skill_item in required_skills:
            if isinstance(skill_item, dict):
                skill_name = skill_item.get('skill', '')
                skill_weight = skill_item.get('weight', 5) / 10  # Normalize to 0-1
            else:
                skill_name = str(skill_item)
                skill_weight = 0.5
            
            required_texts.append(skill_name.lower())
            skill_weights.append(skill_weight)
        
        if not required_texts:
            return 0.0
        
        try:
            # Use TF-IDF for semantic similarity
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
            all_texts = [candidate_text] + required_texts
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            
            # Calculate similarity with each required skill
            candidate_vector = tfidf_matrix[0]
            similarities = []
            
            for i, skill_weight in enumerate(skill_weights):
                required_vector = tfidf_matrix[i + 1]
                similarity = cosine_similarity(candidate_vector, required_vector)[0][0]
                weighted_similarity = similarity * skill_weight
                similarities.append(weighted_similarity)
            
            # Average weighted similarity
            if similarities:
                avg_similarity = sum(similarities) / len(similarities)
                return avg_similarity * weight
            
        except Exception as e:
            logger.warning(f"TF-IDF similarity calculation failed: {e}")
            # Fallback to exact matching
            return self._exact_skill_matching(candidate_skills, required_texts, skill_weights, weight)
        
        return 0.0
    
    def _exact_skill_matching(self, candidate_skills: List[str], required_skills: List[str], weights: List[float], weight: float) -> float:
        """Fallback exact matching for skills"""
        candidate_skills_lower = [skill.lower() for skill in candidate_skills]
        matches = 0
        total_weight = 0
        
        for required_skill, skill_weight in zip(required_skills, weights):
            total_weight += skill_weight
            
            # Check for exact or partial matches
            for candidate_skill in candidate_skills_lower:
                if (required_skill.lower() in candidate_skill or 
                    candidate_skill in required_skill.lower() or
                    required_skill.lower() == candidate_skill):
                    matches += skill_weight
                    break
        
        if total_weight > 0:
            return (matches / total_weight) * weight
        return 0.0
    
    def _score_experience(self, candidate: Dict, job_requirements: Dict) -> float:
        """Score work experience relevance"""
        candidate_experience = candidate.get('experience', [])
        experience_req = job_requirements.get('experience', {})
        
        if not candidate_experience:
            return 0.0
        
        # Calculate total years of experience
        total_years = len(candidate_experience)  # Simplified calculation
        min_years = experience_req.get('min_years', 0)
        
        # Years score (0-40 points)
        if min_years > 0:
            years_score = min(total_years / min_years, 1.0) * 40
        else:
            years_score = 20  # Default if no requirement
        
        # Relevance score (0-60 points)
        required_types = experience_req.get('required_types', [])
        preferred_types = experience_req.get('preferred_types', [])
        
        relevance_score = 0
        for exp in candidate_experience:
            exp_title = exp.get('title', '').lower()
            exp_company = exp.get('company', '').lower()
            exp_description = exp.get('description', '').lower()
            
            # Check against required types
            for req_type in required_types:
                if req_type.lower() in exp_title or req_type.lower() in exp_description:
                    relevance_score += 30 / len(required_types) if required_types else 0
            
            # Check against preferred types
            for pref_type in preferred_types:
                if pref_type.lower() in exp_title or pref_type.lower() in exp_description:
                    relevance_score += 20 / len(preferred_types) if preferred_types else 0
        
        relevance_score = min(relevance_score, 60)
        
        return min(years_score + relevance_score, 100.0)
    
    def _score_education(self, candidate: Dict, job_requirements: Dict) -> float:
        """Score education alignment"""
        candidate_education = candidate.get('education', [])
        education_req = job_requirements.get('education', {})
        
        if not candidate_education:
            if education_req.get('alternatives_accepted', True):
                return 30.0  # Partial score if alternatives accepted
            return 0.0
        
        # Education level mapping
        level_scores = {
            'high school': 20,
            'associate': 40,
            'bachelor': 60,
            'master': 80,
            'phd': 100,
            'doctorate': 100
        }
        
        required_level = education_req.get('required_level', '').lower()
        required_field = education_req.get('required_field', '').lower()
        
        best_score = 0
        for edu in candidate_education:
            degree = edu.get('degree', '').lower()
            field = edu.get('field', '').lower()
            
            # Score education level
            level_score = 0
            for level, score in level_scores.items():
                if level in degree:
                    level_score = score
                    break
            
            # Score field relevance
            field_score = 0
            if required_field:
                if any(req_field.strip().lower() in field for req_field in required_field.split(' or ')):
                    field_score = 40
                elif 'computer' in field or 'engineering' in field or 'science' in field:
                    field_score = 20  # Related field
            else:
                field_score = 20  # No specific field required
            
            total_score = min(level_score + field_score, 100)
            best_score = max(best_score, total_score)
        
        return best_score
    
    def _score_soft_skills(self, candidate: Dict, job_requirements: Dict) -> float:
        """Score soft skills based on projects and experience descriptions"""
        soft_skills_req = job_requirements.get('soft_skills', {})
        if not soft_skills_req:
            return 70.0  # Default score if no specific requirements
        
        # Extract text from candidate profile for analysis
        candidate_text = []
        
        # Add experience descriptions
        for exp in candidate.get('experience', []):
            if exp.get('description'):
                candidate_text.append(exp['description'])
        
        # Add project descriptions
        for project in candidate.get('projects', []):
            if project.get('description'):
                candidate_text.append(project['description'])
        
        # Add summary
        summary = candidate.get('personal_info', {}).get('summary', '')
        if summary:
            candidate_text.append(summary)
        
        full_text = ' '.join(candidate_text).lower()
        
        if not full_text:
            return 30.0  # Low score if no descriptive text
        
        # Score each required soft skill
        total_score = 0
        total_weight = 0
        
        soft_skill_indicators = {
            'communication': ['communication', 'present', 'collaborate', 'explain', 'document', 'write'],
            'teamwork': ['team', 'collaborate', 'group', 'together', 'partnership', 'coordination'],
            'leadership': ['lead', 'manage', 'supervise', 'mentor', 'guide', 'direct', 'coordinate'],
            'problem_solving': ['solve', 'debug', 'troubleshoot', 'analyze', 'optimize', 'improve'],
            'adaptability': ['adapt', 'flexible', 'change', 'learn', 'new', 'different'],
            'creativity': ['creative', 'innovative', 'design', 'invent', 'original', 'unique']
        }
        
        for skill_name, skill_req in soft_skills_req.items():
            if isinstance(skill_req, dict):
                skill_weight = skill_req.get('weight', 5)
                required = skill_req.get('required', False)
            else:
                skill_weight = 5
                required = False
            
            total_weight += skill_weight
            
            # Check for indicators of this soft skill
            indicators = soft_skill_indicators.get(skill_name.lower(), [skill_name.lower()])
            skill_score = 0
            
            for indicator in indicators:
                if indicator in full_text:
                    skill_score = skill_weight
                    break
            
            if not skill_score and not required:
                skill_score = skill_weight * 0.3  # Partial credit for non-required skills
            
            total_score += skill_score
        
        if total_weight > 0:
            return min((total_score / total_weight) * 100, 100.0)
        
        return 50.0
    
    def _score_potential(self, candidate: Dict, job_requirements: Dict) -> float:
        """Score candidate potential for growth and learning"""
        potential_indicators = {
            'learning_projects': 0,
            'diverse_technologies': 0,
            'recent_skills': 0,
            'open_source': 0,
            'continuous_learning': 0
        }
        
        # Analyze projects for learning indicators
        projects = candidate.get('projects', [])
        unique_technologies = set()
        
        for project in projects:
            technologies = project.get('technologies', [])
            unique_technologies.update([tech.lower() for tech in technologies])
            
            # Check for personal/learning projects
            project_name = project.get('name', '').lower()
            project_desc = project.get('description', '').lower()
            
            if any(indicator in project_desc for indicator in ['learn', 'tutorial', 'practice', 'experiment']):
                potential_indicators['learning_projects'] += 1
        
        # Score diversity of technologies
        potential_indicators['diverse_technologies'] = min(len(unique_technologies) / 5, 1) * 20
        
        # Check for GitHub/open source presence
        links = candidate.get('links', {})
        if links.get('github') or 'github' in str(links.get('other', [])):
            potential_indicators['open_source'] = 20
        
        # Check for continuous learning indicators
        all_skills = candidate.get('skills', {}).get('all_skills', [])
        modern_tech_indicators = ['react', 'vue', 'angular', 'docker', 'kubernetes', 'aws', 'azure', 'ai', 'ml', 'tensorflow', 'pytorch']
        modern_skills = sum(1 for skill in all_skills if any(modern in skill.lower() for modern in modern_tech_indicators))
        potential_indicators['continuous_learning'] = min(modern_skills / 3, 1) * 20
        
        # Learning projects score
        potential_indicators['learning_projects'] = min(potential_indicators['learning_projects'] * 10, 20)
        
        # Recent skills (assume if they have modern technologies, they're keeping up)
        potential_indicators['recent_skills'] = min(modern_skills / 2, 1) * 20
        
        total_potential = sum(potential_indicators.values())
        return min(total_potential, 100.0)
    
    def _identify_strengths(self, candidate: Dict, job_requirements: Dict) -> List[str]:
        """Identify candidate's key strengths relevant to the role"""
        strengths = []
        
        # Technical strengths
        candidate_skills = candidate.get('skills', {}).get('technical', [])
        required_skills = job_requirements.get('technical_skills', {}).get('required', [])
        
        for skill_item in required_skills:
            skill_name = skill_item.get('skill', '') if isinstance(skill_item, dict) else str(skill_item)
            
            for candidate_skill in candidate_skills:
                if skill_name.lower() in candidate_skill.lower() or candidate_skill.lower() in skill_name.lower():
                    strengths.append(f"Strong {skill_name} skills")
                    break
        
        # Experience strengths
        experience = candidate.get('experience', [])
        if len(experience) >= job_requirements.get('experience', {}).get('min_years', 0):
            strengths.append("Meets experience requirements")
        
        # Project portfolio strength
        projects = candidate.get('projects', [])
        if len(projects) >= 3:
            strengths.append("Strong project portfolio demonstrating practical skills")
        
        # Professional presence
        links = candidate.get('links', {})
        if links.get('github'):
            strengths.append("Active GitHub presence")
        if links.get('linkedin'):
            strengths.append("Professional LinkedIn profile")
        
        return strengths[:5]  # Return top 5 strengths
    
    def _identify_development_areas(self, candidate: Dict, job_requirements: Dict) -> List[str]:
        """Identify areas where candidate could improve"""
        development_areas = []
        
        # Missing technical skills
        candidate_skills = set(skill.lower() for skill in candidate.get('skills', {}).get('technical', []))
        required_skills = job_requirements.get('technical_skills', {}).get('required', [])
        
        missing_skills = []
        for skill_item in required_skills:
            skill_name = skill_item.get('skill', '') if isinstance(skill_item, dict) else str(skill_item)
            
            if not any(skill_name.lower() in candidate_skill for candidate_skill in candidate_skills):
                missing_skills.append(skill_name)
        
        if missing_skills:
            development_areas.append(f"Could benefit from learning: {', '.join(missing_skills[:3])}")
        
        # Experience gaps
        min_years = job_requirements.get('experience', {}).get('min_years', 0)
        candidate_years = len(candidate.get('experience', []))
        
        if candidate_years < min_years:
            development_areas.append(f"Could benefit from {min_years - candidate_years} more years of experience")
        
        # Missing certifications
        required_certs = job_requirements.get('education', {}).get('certifications', [])
        candidate_certs = candidate.get('skills', {}).get('certifications', [])
        
        if required_certs and not candidate_certs:
            development_areas.append("Consider obtaining relevant certifications")
        
        return development_areas[:3]  # Return top 3 development areas
    
    def _assess_potential(self, candidate: Dict, job_requirements: Dict) -> Dict:
        """Assess candidate's growth potential"""
        potential_score = self._score_potential(candidate, job_requirements)
        
        assessment = {
            'score': potential_score,
            'level': 'High' if potential_score >= 70 else 'Medium' if potential_score >= 40 else 'Low',
            'indicators': []
        }
        
        # Add specific indicators
        if candidate.get('projects'):
            assessment['indicators'].append("Demonstrates initiative through personal projects")
        
        if candidate.get('links', {}).get('github'):
            assessment['indicators'].append("Active in open source development")
        
        modern_skills = sum(1 for skill in candidate.get('skills', {}).get('all_skills', [])
                          if any(modern in skill.lower() for modern in ['react', 'docker', 'aws', 'ai', 'ml']))
        
        if modern_skills >= 2:
            assessment['indicators'].append("Stays current with modern technologies")
        
        return assessment
    
    def _assess_cultural_fit(self, candidate: Dict, job_requirements: Dict) -> Dict:
        """Assess cultural fit based on role context"""
        role_context = job_requirements.get('role_context', {})
        company_stage = role_context.get('company_stage', '').lower()
        team_size = role_context.get('team_size', '').lower()
        
        fit_score = 70  # Default neutral score
        fit_indicators = []
        
        # Startup fit
        if 'startup' in company_stage:
            if candidate.get('projects') and len(candidate.get('projects', [])) > 2:
                fit_score += 10
                fit_indicators.append("Self-starter with personal projects")
            
            diverse_skills = len(candidate.get('skills', {}).get('all_skills', []))
            if diverse_skills > 8:
                fit_score += 10
                fit_indicators.append("Versatile skill set suitable for startup environment")
        
        # Small team fit
        if 'small' in team_size:
            if candidate.get('links', {}).get('github'):
                fit_score += 5
                fit_indicators.append("Collaborative development experience")
        
        return {
            'score': min(fit_score, 100),
            'level': 'High' if fit_score >= 80 else 'Medium' if fit_score >= 60 else 'Low',
            'indicators': fit_indicators
        }
    
    def _select_top_candidates(self, scored_candidates: List[Dict], min_candidates: int = 7, max_candidates: int = 10) -> List[Dict]:
        """Select top candidates ensuring quality and diversity"""
        # Filter out candidates with errors
        valid_candidates = [c for c in scored_candidates if 'error' not in c]
        
        if len(valid_candidates) <= min_candidates:
            return valid_candidates
        
        # Ensure minimum score threshold
        score_threshold = 40  # Minimum viable score
        qualified_candidates = [c for c in valid_candidates if c.get('overall_score', 0) >= score_threshold]
        
        if len(qualified_candidates) < min_candidates:
            # If not enough qualified candidates, include top scorers regardless of threshold
            return valid_candidates[:max_candidates]
        
        # Select top candidates with diversity consideration
        selected = qualified_candidates[:max_candidates]
        
        return selected
    
    def _get_selection_criteria(self, job_requirements: Dict) -> Dict:
        """Get the criteria used for candidate selection"""
        return {
            'scoring_weights': job_requirements.get('scoring_weights', {}),
            'minimum_score_threshold': 40,
            'selection_method': 'Weighted scoring with diversity consideration',
            'key_requirements': {
                'technical_skills': len(job_requirements.get('technical_skills', {}).get('required', [])),
                'experience_years': job_requirements.get('experience', {}).get('min_years', 0),
                'education_required': job_requirements.get('education', {}).get('required_level', 'Not specified')
            }
        }
    
    def _analyze_diversity(self, candidates: List[Dict]) -> Dict:
        """Analyze diversity in selected candidates"""
        if not candidates:
            return {'total_candidates': 0}
        
        # Analyze skill diversity
        all_skills = set()
        for candidate in candidates:
            candidate_skills = candidate.get('candidate', {}).get('skills', {}).get('all_skills', [])
            all_skills.update(candidate_skills)
        
        # Analyze experience diversity
        experience_types = set()
        for candidate in candidates:
            for exp in candidate.get('candidate', {}).get('experience', []):
                if exp.get('title'):
                    experience_types.add(exp['title'].lower())
        
        return {
            'total_candidates': len(candidates),
            'unique_skills_represented': len(all_skills),
            'experience_diversity': len(experience_types),
            'score_range': {
                'highest': max(c.get('overall_score', 0) for c in candidates),
                'lowest': min(c.get('overall_score', 0) for c in candidates),
                'average': sum(c.get('overall_score', 0) for c in candidates) / len(candidates)
            }
        }
    
    def _fallback_job_analysis(self, job_description: str) -> Dict:
        """Fallback job analysis when LLM fails"""
        # Basic keyword extraction for fallback
        tech_keywords = ['python', 'java', 'javascript', 'react', 'sql', 'aws', 'docker', 'git']
        soft_keywords = ['communication', 'teamwork', 'leadership', 'problem solving']
        
        found_tech = [keyword for keyword in tech_keywords if keyword.lower() in job_description.lower()]
        found_soft = [keyword for keyword in soft_keywords if keyword.lower() in job_description.lower()]
        
        return {
            'technical_skills': {
                'required': [{'skill': skill, 'weight': 7, 'required': True} for skill in found_tech],
                'preferred': []
            },
            'experience': {
                'min_years': 2,  # Default
                'required_types': ['Software Development'],
                'preferred_types': [],
                'leadership_required': False
            },
            'education': {
                'required_level': "Bachelor's",
                'required_field': 'Computer Science or related',
                'alternatives_accepted': True,
                'certifications': []
            },
            'soft_skills': {skill: {'weight': 6, 'required': True} for skill in found_soft},
            'scoring_weights': {
                'technical_skills': 0.4,
                'experience': 0.25,
                'education': 0.15,
                'soft_skills': 0.15,
                'potential': 0.05
            }
        }