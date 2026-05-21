"""Utilities for scoring and ranking candidates."""

from typing import Dict, List, Set, Union
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from datetime import datetime
import spacy
import logging

logger = logging.getLogger(__name__)

# Load SpaCy model for semantic analysis
try:
    nlp = spacy.load('en_core_web_sm')
except:
    logger.warning("SpaCy model not found. Installing...")
    import os
    os.system('python -m spacy download en_core_web_sm')
    nlp = spacy.load('en_core_web_sm')

def calculate_skill_match_score(candidate_skills: List[str],
                              required_skills: List[str],
                              preferred_skills: List[str] = None) -> Dict[str, float]:
    """Calculate skill match score between candidate and job requirements"""
    # Normalize skills for comparison
    candidate_skills_norm = {s.lower() for s in candidate_skills}
    required_skills_norm = {s.lower() for s in required_skills}
    preferred_skills_norm = {s.lower() for s in (preferred_skills or [])}
    
    # Calculate required skills match
    required_matched = required_skills_norm & candidate_skills_norm
    required_score = len(required_matched) / len(required_skills_norm) if required_skills_norm else 1.0
    
    # Calculate preferred skills match
    preferred_score = 0
    if preferred_skills_norm:
        preferred_matched = preferred_skills_norm & candidate_skills_norm
        preferred_score = len(preferred_matched) / len(preferred_skills_norm)
    
    # Calculate weighted score (70% required, 30% preferred)
    total_score = (required_score * 0.7) + (preferred_score * 0.3)
    
    return {
        'total_score': total_score * 100,
        'required_score': required_score * 100,
        'preferred_score': preferred_score * 100,
        'matched_required': list(required_matched),
        'matched_preferred': list(preferred_skills_norm & candidate_skills_norm),
        'missing_required': list(required_skills_norm - candidate_skills_norm),
        'missing_preferred': list(preferred_skills_norm - candidate_skills_norm)
    }

def calculate_experience_match(candidate_experience: List[Dict],
                            required_years: int,
                            relevant_titles: List[str] = None,
                            relevant_companies: List[str] = None) -> Dict[str, float]:
    """Calculate experience match score"""
    total_years = 0
    relevant_years = 0
    relevant_positions = []
    
    for position in candidate_experience:
        # Calculate duration
        duration = position.get('duration', '')
        try:
            years = _calculate_years_from_duration(duration)
            total_years += years
            
            # Check if position is relevant
            is_relevant = False
            if relevant_titles:
                title = position.get('title', '').lower()
                if any(rel.lower() in title for rel in relevant_titles):
                    is_relevant = True
            
            if relevant_companies:
                company = position.get('company', '').lower()
                if any(rel.lower() in company for rel in relevant_companies):
                    is_relevant = True
            
            if is_relevant:
                relevant_years += years
                relevant_positions.append(position)
                
        except Exception as e:
            logger.warning(f"Error calculating duration for position: {str(e)}")
            continue
    
    # Calculate scores
    years_score = min(total_years / required_years, 1.0) if required_years > 0 else 1.0
    relevance_score = relevant_years / total_years if total_years > 0 else 0
    
    return {
        'total_score': ((years_score * 0.6) + (relevance_score * 0.4)) * 100,
        'years_score': years_score * 100,
        'relevance_score': relevance_score * 100,
        'total_years': total_years,
        'relevant_years': relevant_years,
        'relevant_positions': relevant_positions
    }

def calculate_education_match(candidate_education: Dict,
                           required_degree: str = None,
                           preferred_fields: List[str] = None) -> Dict[str, float]:
    """Calculate education match score"""
    degrees = candidate_education.get('degrees', [])
    
    # Calculate degree level match
    degree_level_score = 0
    if required_degree:
        degree_levels = {
            'bachelor': 1,
            'master': 2,
            'phd': 3
        }
        required_level = degree_levels.get(required_degree.lower(), 0)
        candidate_level = 0
        
        for degree in degrees:
            degree_lower = degree.lower()
            if 'phd' in degree_lower:
                candidate_level = max(candidate_level, 3)
            elif 'master' in degree_lower:
                candidate_level = max(candidate_level, 2)
            elif 'bachelor' in degree_lower:
                candidate_level = max(candidate_level, 1)
        
        degree_level_score = 1.0 if candidate_level >= required_level else 0.0
    
    # Calculate field match
    field_score = 0
    if preferred_fields:
        for degree in degrees:
            if any(field.lower() in degree.lower() for field in preferred_fields):
                field_score = 1.0
                break
    
    # Calculate GPA score if available
    gpa_score = 0
    gpa = candidate_education.get('gpa')
    if gpa:
        try:
            gpa_float = float(gpa)
            gpa_score = min((gpa_float - 2.5) / 1.5, 1.0)  # Scale 2.5-4.0 to 0-1
        except:
            pass
    
    # Calculate total score
    weights = {
        'degree_level': 0.5,
        'field': 0.3,
        'gpa': 0.2
    }
    
    total_score = (
        (degree_level_score * weights['degree_level']) +
        (field_score * weights['field']) +
        (gpa_score * weights['gpa'])
    ) * 100
    
    return {
        'total_score': total_score,
        'degree_level_score': degree_level_score * 100,
        'field_score': field_score * 100,
        'gpa_score': gpa_score * 100,
        'degrees': degrees,
        'gpa': gpa
    }

def calculate_overall_match(skill_score: Dict,
                          experience_score: Dict,
                          education_score: Dict,
                          weights: Dict = None) -> Dict[str, float]:
    """Calculate overall match score"""
    # Default weights
    default_weights = {
        'skills': 0.4,
        'experience': 0.35,
        'education': 0.25
    }
    
    # Use provided weights or defaults
    weights = weights or default_weights
    
    # Normalize weights to sum to 1
    total_weight = sum(weights.values())
    weights = {k: v/total_weight for k, v in weights.items()}
    
    # Calculate overall score
    overall_score = (
        (skill_score['total_score'] * weights['skills']) +
        (experience_score['total_score'] * weights['experience']) +
        (education_score['total_score'] * weights['education'])
    )
    
    return {
        'overall_score': overall_score,
        'category_scores': {
            'skills': skill_score['total_score'],
            'experience': experience_score['total_score'],
            'education': education_score['total_score']
        },
        'weights': weights,
        'details': {
            'skills': skill_score,
            'experience': experience_score,
            'education': education_score
        }
    }

def calculate_semantic_match(job_description: str,
                         candidate_description: str) -> float:
    """Calculate semantic similarity between job and candidate descriptions"""
    # Process texts with SpaCy
    job_doc = nlp(job_description)
    candidate_doc = nlp(candidate_description)
    
    # Calculate similarity using SpaCy's built-in word vectors
    similarity = job_doc.similarity(candidate_doc)
    
    return similarity

def _calculate_years_from_duration(duration: str) -> float:
    """Calculate years from duration string"""
    try:
        # Handle "Present" in end date
        if ' - ' not in duration:
            return 0
        
        start_str, end_str = duration.split(' - ')
        start_date = datetime.strptime(start_str, '%B %Y')
        
        if end_str.lower() == 'present':
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(end_str, '%B %Y')
        
        duration_years = (end_date - start_date).days / 365.25
        return duration_years
    
    except Exception as e:
        logger.error(f"Error parsing duration '{duration}': {str(e)}")
        return 0

def normalize_skill_names(skills: List[str]) -> List[str]:
    """Normalize skill names for consistent comparison"""
    # Common variations of the same skill
    skill_aliases = {
        'js': 'javascript',
        'py': 'python',
        'ts': 'typescript',
        'react.js': 'react',
        'node.js': 'node',
        'postgres': 'postgresql',
        'golang': 'go',
        'ML': 'machine learning',
        'AI': 'artificial intelligence'
    }
    
    normalized = []
    for skill in skills:
        skill = skill.lower().strip()
        normalized.append(skill_aliases.get(skill, skill))
    
    return normalized
