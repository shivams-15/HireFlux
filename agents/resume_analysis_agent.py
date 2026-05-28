from crewai import Agent, Task
import logging
from utils.document_parser import DocumentParser
from typing import Dict, List
import json
import os
from utils.gemini_llm import GeminiClient, get_crewai_llm, map_model_name

logger = logging.getLogger(__name__)

class ResumeAnalysisAgent:
    def __init__(self, model="gemini-3.1-flash-lite"):
        """
        Initialize Resume Analysis Agent
        
        Args:
            model: Gemini model for content extraction (default: gemini-3.1-flash-lite)
                  gemini-3.1-flash-lite is optimized for fast, budget-friendly document parsing
        """
        self.model_name = map_model_name(model)
        self.parser = DocumentParser()
        self.llm_client = GeminiClient(model=self.model_name)
        
        self.agent = Agent(
            role="Resume Analysis Agent",
            goal="Extract comprehensive and accurate information from resumes using advanced AI techniques",
            backstory="""You are an expert resume analyzer with advanced AI capabilities. 
            Your expertise lies in processing resumes of any format and extracting structured, 
            comprehensive information including personal details, education, work experience, 
            skills, projects, certifications, achievements, and all professional links.
            You use state-of-the-art LLM technology to understand context and extract 
            information that traditional parsing methods might miss.""",
            verbose=True,
            llm=get_crewai_llm(model=self.model_name),
            allow_delegation=False
        )
    
    def create_tasks(self, candidates_data: List[Dict]) -> List[Task]:
        """Create tasks for processing all candidate resumes"""
        
        extract_resume_task = Task(
            description=f"""Process and analyze {len(candidates_data)} candidate resumes using advanced LLM-powered extraction.

For each candidate in the provided data:
1. Extract the resume content from the CV URL (Google Docs, PDFs, etc.)
2. Use AI to comprehensively analyze and extract ALL available information
3. Structure the information into detailed candidate profiles
4. Ensure ALL links (LinkedIn, GitHub, portfolios, etc.) are properly extracted
5. Cross-reference listed skills with skills found in the resume content
6. Extract projects, achievements, certifications, and any other relevant details
7. Handle different resume formats dynamically without relying on keywords

IMPORTANT REQUIREMENTS:
- Extract information dynamically - do not rely on predefined keywords or formats
- Every resume format should be handled intelligently
- Capture ALL skills mentioned, not just from predefined lists
- Extract ALL URLs and links for further research
- If information is missing or unclear, mark it as such - do not fabricate
- Maintain accuracy and completeness
- Preserve exact names, titles, and technical terms as written

The output should be a comprehensive structured dataset ready for matching analysis.

CANDIDATES TO PROCESS:
{json.dumps(candidates_data, indent=2)}""",
            expected_output="""A comprehensive JSON structure for each candidate containing:
- Complete personal information and contact details
- Detailed education history with all relevant information
- Full work experience with responsibilities and achievements
- Comprehensive skills list (technical, soft skills, certifications)
- All projects with descriptions and technologies used
- All professional links (LinkedIn, GitHub, portfolio, etc.)
- Additional information (languages, volunteer work, publications, awards)
- Source information and any processing notes

The structure should be ready for the matching agent to evaluate against job requirements.""",
            agent=self.agent
        )
        
        return [extract_resume_task]
    
    def process_candidates(self, candidates_data: List[Dict]) -> List[Dict]:
        """Process all candidates and return structured data"""
        processed_candidates = []
        
        for i, candidate in enumerate(candidates_data):
            logger.info(f"Processing candidate {i+1}/{len(candidates_data)}: {candidate.get('Student Name', 'Unknown')}")
            
            try:
                # Extract resume information using LLM parser
                resume_data = self.parser.parse_resume(candidate)
                
                # Enhance with additional processing
                enhanced_data = self._enhance_candidate_data(resume_data, candidate)
                
                processed_candidates.append(enhanced_data)
                
            except Exception as e:
                logger.error(f"Error processing candidate {candidate.get('Student Name', 'Unknown')}: {str(e)}")
                # Add error candidate data
                processed_candidates.append({
                    'candidate_id': i,
                    'original_data': candidate,
                    'error': str(e),
                    'processed': False
                })
        
        return processed_candidates
    
    def _enhance_candidate_data(self, resume_data: Dict, original_candidate: Dict) -> Dict:
        """Enhance the extracted resume data with additional processing"""
        
        # Create enhanced candidate profile
        enhanced_profile = {
            'candidate_id': len(resume_data.get('source_url', '')),  # Simple ID generation
            'original_data': original_candidate,
            'processed': True,
            'extraction_successful': 'error' not in resume_data,
            
            # Personal Information
            'personal_info': {
                'name': resume_data.get('personal_info', {}).get('name') or original_candidate.get('Student Name', ''),
                'location': resume_data.get('personal_info', {}).get('location', ''),
                'summary': resume_data.get('personal_info', {}).get('summary', ''),
            },
            
            # Contact Information
            'contact_info': resume_data.get('contact_info', {}),
            
            # Education
            'education': resume_data.get('education', []),
            
            # Work Experience
            'experience': resume_data.get('experience', []),
            
            # Skills (merged and enhanced)
            'skills': self._merge_and_enhance_skills(
                resume_data.get('skills', {}),
                original_candidate.get('Skills', '')
            ),
            
            # Projects
            'projects': resume_data.get('projects', []),
            
            # Professional Links
            'links': resume_data.get('links', {}),
            
            # Additional Information
            'additional_info': resume_data.get('additional', {}),
            
            # Metadata
            'metadata': {
                'source_url': resume_data.get('source_url', ''),
                'extraction_method': 'LLM-powered',
                'processing_notes': self._generate_processing_notes(resume_data),
                'quality_score': self._calculate_quality_score(resume_data)
            }
        }
        
        return enhanced_profile
    
    def _merge_and_enhance_skills(self, extracted_skills: Dict, listed_skills: str) -> Dict:
        """Merge and enhance skills from different sources"""
        merged_skills = {
            'technical': set(),
            'soft': set(),
            'certifications': set()
        }
        
        # Add extracted skills
        if extracted_skills:
            merged_skills['technical'].update(extracted_skills.get('technical', []))
            merged_skills['soft'].update(extracted_skills.get('soft', []))
            merged_skills['certifications'].update(extracted_skills.get('certifications', []))
        
        # Add listed skills
        if listed_skills:
            listed_skills_list = [skill.strip() for skill in listed_skills.split(',') if skill.strip()]
            # Use LLM to categorize listed skills
            categorized_skills = self._categorize_skills_with_llm(listed_skills_list)
            merged_skills['technical'].update(categorized_skills.get('technical', []))
            merged_skills['soft'].update(categorized_skills.get('soft', []))
            merged_skills['certifications'].update(categorized_skills.get('certifications', []))
        
        # Convert sets back to lists and sort
        return {
            'technical': sorted(list(merged_skills['technical'])),
            'soft': sorted(list(merged_skills['soft'])),
            'certifications': sorted(list(merged_skills['certifications'])),
            'all_skills': sorted(list(
                merged_skills['technical'].union(
                    merged_skills['soft']).union(
                    merged_skills['certifications'])
            ))
        }
    
    def _categorize_skills_with_llm(self, skills_list: List[str]) -> Dict[str, List[str]]:
        """Use LLM to categorize skills into technical/soft/certifications"""
        if not skills_list or not self.llm_client:
            return {'technical': skills_list, 'soft': [], 'certifications': []}
        
        try:
            prompt = f"""
Categorize these skills into three categories: technical, soft, and certifications.

Skills to categorize: {', '.join(skills_list)}

Return a JSON object with three arrays:
- "technical": Programming languages, tools, technologies, frameworks, etc.
- "soft": Communication, leadership, teamwork, problem-solving, etc.
- "certifications": Formal certifications, licenses, credentials

Example format:
{{
  "technical": ["Python", "AWS", "Docker"],
  "soft": ["Leadership", "Communication"],
  "certifications": ["AWS Certified", "PMP"]
}}
"""
            
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at categorizing professional skills. Categorize skills accurately based on their nature."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Error categorizing skills with LLM: {e}")
            # Fallback: assume all are technical
            return {'technical': skills_list, 'soft': [], 'certifications': []}
    
    def _generate_processing_notes(self, resume_data: Dict) -> List[str]:
        """Generate processing notes about the extraction"""
        notes = []
        
        if 'error' in resume_data:
            notes.append(f"Extraction error: {resume_data['error']}")
        
        # Check data completeness
        if not resume_data.get('personal_info', {}).get('name'):
            notes.append("Name not found in resume")
        
        if not resume_data.get('contact_info', {}).get('emails'):
            notes.append("No email addresses found")
        
        if not resume_data.get('experience'):
            notes.append("No work experience found")
        
        if not resume_data.get('education'):
            notes.append("No education information found")
        
        if not resume_data.get('skills', {}).get('technical'):
            notes.append("No technical skills extracted")
        
        # Check for important links
        links = resume_data.get('links', {})
        if not links.get('linkedin') and not links.get('github'):
            notes.append("No professional profiles (LinkedIn/GitHub) found")
        
        # Quality indicators
        total_sections = sum([
            1 if resume_data.get('personal_info', {}).get('name') else 0,
            1 if resume_data.get('contact_info', {}).get('emails') else 0,
            1 if resume_data.get('experience') else 0,
            1 if resume_data.get('education') else 0,
            1 if resume_data.get('skills', {}).get('technical') else 0,
            1 if resume_data.get('projects') else 0
        ])
        
        if total_sections >= 5:
            notes.append("High-quality extraction: Most sections found")
        elif total_sections >= 3:
            notes.append("Medium-quality extraction: Some sections missing")
        else:
            notes.append("Low-quality extraction: Many sections missing")
        
        return notes
    
    def _calculate_quality_score(self, resume_data: Dict) -> float:
        """Calculate a quality score for the extraction (0-1)"""
        if 'error' in resume_data:
            return 0.0
        
        score = 0.0
        max_score = 0.0
        
        # Personal info (20%)
        max_score += 0.2
        if resume_data.get('personal_info', {}).get('name'):
            score += 0.15
        if resume_data.get('personal_info', {}).get('location'):
            score += 0.05
        
        # Contact info (15%)
        max_score += 0.15
        if resume_data.get('contact_info', {}).get('emails'):
            score += 0.1
        if resume_data.get('contact_info', {}).get('phones'):
            score += 0.05
        
        # Experience (25%)
        max_score += 0.25
        experience = resume_data.get('experience', [])
        if experience:
            score += 0.25 * min(len(experience) / 3, 1)  # Max score for 3+ experiences
        
        # Education (15%)
        max_score += 0.15
        education = resume_data.get('education', [])
        if education:
            score += 0.15
        
        # Skills (15%)
        max_score += 0.15
        skills = resume_data.get('skills', {})
        if skills.get('technical'):
            score += 0.1
        if skills.get('soft'):
            score += 0.03
        if skills.get('certifications'):
            score += 0.02
        
        # Projects (5%)
        max_score += 0.05
        if resume_data.get('projects'):
            score += 0.05
        
        # Links (5%)
        max_score += 0.05
        links = resume_data.get('links', {})
        if links.get('linkedin'):
            score += 0.03
        if links.get('github'):
            score += 0.02
        
        return min(score / max_score, 1.0) if max_score > 0 else 0.0