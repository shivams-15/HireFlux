"""Document parser utility for handling various file formats."""

import os
import re
import logging
import pandas as pd
import tempfile
from typing import Dict, List, Union, Optional
from io import BytesIO
import json

try:
    import PyPDF2
    import pdfplumber
except ImportError:
    logger.warning("PDF parsing libraries not available. Install PyPDF2 and pdfplumber for PDF support.")

try:
    from utils.gemini_llm import GeminiClient
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentParser:
    """Parser for various document formats"""
    
    def __init__(self, use_gemini: bool = True, gemini_model: str = "gemini-3.1-flash-lite"):
        """Initialize the document parser
        
        Args:
            use_gemini: Whether to use Gemini for enhanced extraction (default: True)
            gemini_model: Gemini model to use for extraction (default: gemini-3.1-flash-lite)
        """
        logger.info("Initializing DocumentParser")
        self.temp_dir = tempfile.mkdtemp()
        self.use_gemini = use_gemini and GEMINI_AVAILABLE
        
        if self.use_gemini:
            try:
                self.gemini_client = GeminiClient(model=gemini_model)
                logger.info(f"Gemini-enhanced document parsing enabled with model: {gemini_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}. Falling back to traditional parsing.")
                self.use_gemini = False
                self.gemini_client = None
        else:
            self.gemini_client = None
            if not GEMINI_AVAILABLE:
                logger.info("Gemini not available. Using traditional document parsing.")
    
    def parse_pdf(self, file_path: str) -> str:
        """Parse PDF file and extract text
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text from PDF
        """
        try:
            logger.info(f"Parsing PDF file: {file_path}")
            text = ""
            
            # Try using pdfplumber first (better text extraction)
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\\n"
                logger.info(f"Extracted {len(text)} characters using pdfplumber")
            except Exception as e:
                logger.warning(f"pdfplumber failed, trying PyPDF2: {str(e)}")
                
                # Fallback to PyPDF2
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        for page in pdf_reader.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\\n"
                    logger.info(f"Extracted {len(text)} characters using PyPDF2")
                except Exception as e2:
                    logger.error(f"Both PDF parsers failed: {str(e2)}")
                    raise ValueError(f"Could not parse PDF file: {str(e2)}")
            
            if not text.strip():
                raise ValueError("No text could be extracted from PDF")
            
            # Optionally enhance with Gemini for better structure and extraction
            if self.use_gemini and self.gemini_client and len(text) > 100:
                try:
                    enhanced_text = self._enhance_extraction_with_gemini(text)
                    if enhanced_text:
                        logger.info("Enhanced PDF extraction using Gemini")
                        return enhanced_text
                except Exception as e:
                    logger.warning(f"Gemini enhancement failed, using standard extraction: {e}")
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            raise
    
    def _enhance_extraction_with_gemini(self, raw_text: str) -> Optional[str]:
        """Enhance extracted text using Gemini for better structure
        
        Args:
            raw_text: Raw text extracted from document
            
        Returns:
            Enhanced, structured text
        """
        try:
            prompt = f"""You are parsing a resume/CV document. The following text was extracted from a PDF but may have formatting issues.
Please clean up the text, preserve all information, and structure it properly:

{raw_text[:4000]}

Return the cleaned and properly structured text maintaining all original information."""
            
            enhanced = self.gemini_client.generate_content(prompt)
            return enhanced if enhanced else raw_text
            
        except Exception as e:
            logger.error(f"Error enhancing with Gemini: {e}")
            return None
        
    def _parse_skills(self, skills_text: Union[str, List]) -> List[str]:
        """Parse skills from text or list
        
        Args:
            skills_text: Skills as text or list
            
        Returns:
            List of skills
        """
        if not skills_text:
            return []
        
        # If already a list, return it
        if isinstance(skills_text, list):
            return [str(skill).strip() for skill in skills_text if skill]
        
        # Convert to string
        skills_str = str(skills_text)
        
        # Try to parse as comma-separated list
        if ',' in skills_str:
            skills = [skill.strip() for skill in skills_str.split(',') if skill.strip()]
            if skills:
                return skills
        
        # Try to parse as semicolon-separated list
        if ';' in skills_str:
            skills = [skill.strip() for skill in skills_str.split(';') if skill.strip()]
            if skills:
                return skills
        
        # Try to parse as newline-separated list
        if '\n' in skills_str:
            skills = [skill.strip() for skill in skills_str.split('\n') if skill.strip()]
            if skills:
                return skills
        
        # If no separators found, treat as a single skill
        if skills_str.strip():
            return [skills_str.strip()]
        
        return []
    
    def parse_spreadsheet(self, file_path_or_content: Union[str, bytes, BytesIO]) -> List[Dict]:
        """Parse an Excel or CSV file containing candidate information
        
        Args:
            file_path_or_content: Path to the spreadsheet file, bytes content, or BytesIO object
            
        Returns:
            List of dictionaries containing candidate information
        """
        try:
            # Log the input type for debugging
            logger.info(f"Input type: {type(file_path_or_content)}")
            if isinstance(file_path_or_content, str):
                logger.info(f"Input string: {file_path_or_content[:100]}...")
            
            # Determine if input is a file path or content
            if isinstance(file_path_or_content, str):
                # Check if it's a valid file path
                if os.path.isfile(file_path_or_content):
                    logger.info(f"Reading spreadsheet from file path: {file_path_or_content}")
                    # For Excel files
                    if file_path_or_content.lower().endswith(('.xlsx', '.xls', '.xlsm', '.xlsb')):
                        df = pd.read_excel(file_path_or_content)
                    # For CSV files
                    elif file_path_or_content.lower().endswith('.csv'):
                        df = pd.read_csv(file_path_or_content)
                    else:
                        # Try to infer file type
                        try:
                            df = pd.read_excel(file_path_or_content)
                        except Exception:
                            try:
                                df = pd.read_csv(file_path_or_content)
                            except Exception as e:
                                logger.error(f"Could not determine file type for {file_path_or_content}: {str(e)}")
                                raise ValueError(f"Unsupported file format. Please use Excel or CSV files.")
                # Check if it's a URL
                elif file_path_or_content.startswith(('http://', 'https://')):
                    logger.info(f"Reading spreadsheet from URL: {file_path_or_content}")
                    try:
                        # Try to read as Excel first
                        df = pd.read_excel(file_path_or_content)
                    except Exception:
                        try:
                            # Try to read as CSV
                            df = pd.read_csv(file_path_or_content)
                        except Exception as e:
                            logger.error(f"Could not read URL as Excel or CSV: {str(e)}")
                            raise ValueError(f"Could not read URL as Excel or CSV: {file_path_or_content}")
                else:
                    logger.error(f"Input string is not a valid file path or URL: {file_path_or_content}")
                    raise ValueError("Input string must be a valid file path or URL")
            elif isinstance(file_path_or_content, (bytes, BytesIO)):
                logger.info("Reading spreadsheet from bytes or BytesIO")
                # Try to read as Excel first
                try:
                    df = pd.read_excel(file_path_or_content)
                except Exception as e1:
                    logger.warning(f"Failed to read as Excel: {str(e1)}")
                    # Try to read as CSV
                    try:
                        if isinstance(file_path_or_content, bytes):
                            file_obj = BytesIO(file_path_or_content)
                        else:
                            file_obj = file_path_or_content
                            file_obj.seek(0)
                        df = pd.read_csv(file_obj)
                    except Exception as e2:
                        logger.error(f"Could not read content as Excel or CSV: {str(e2)}")
                        raise ValueError("Could not parse content as Excel or CSV")
            else:
                logger.error(f"Invalid input type: {type(file_path_or_content)}")
                raise ValueError(f"Input must be a file path, URL, bytes, or BytesIO object. Got {type(file_path_or_content)}")
            
            # Log the dataframe shape and columns for debugging
            logger.info(f"Successfully read dataframe with shape {df.shape} and columns: {list(df.columns)}")
            
            # Clean column names (strip whitespace and handle case sensitivity)
            df.columns = df.columns.str.strip()
            
            # Map column names to expected format (case-insensitive)
            column_mapping = {}
            required_columns = ['Student Name', 'Skills', 'CV']
            
            for req_col in required_columns:
                for col in df.columns:
                    if col.lower().replace(' ', '') == req_col.lower().replace(' ', ''):
                        column_mapping[req_col] = col
                        break
            
            # Check if we found all required columns
            missing_columns = [col for col in required_columns if col not in column_mapping]
            
            if missing_columns:
                logger.warning(f"Missing required columns: {', '.join(missing_columns)}")
                logger.warning(f"Available columns: {', '.join(df.columns)}")
                
                # Try to make educated guesses for missing columns
                for missing_col in missing_columns:
                    if missing_col == 'Student Name':
                        # Look for columns that might contain names
                        for col in df.columns:
                            if any(name_key in col.lower() for name_key in ['name', 'student', 'candidate', 'applicant']):
                                column_mapping['Student Name'] = col
                                logger.info(f"Mapped 'Student Name' to '{col}'")
                                break
                    elif missing_col == 'Skills':
                        # Look for columns that might contain skills
                        for col in df.columns:
                            if any(skill_key in col.lower() for skill_key in ['skill', 'technology', 'tech', 'language', 'framework']):
                                column_mapping['Skills'] = col
                                logger.info(f"Mapped 'Skills' to '{col}'")
                                break
                    elif missing_col == 'CV':
                        # Look for columns that might contain CV/resume links
                        for col in df.columns:
                            if any(cv_key in col.lower() for cv_key in ['cv', 'resume', 'document', 'link', 'url', 'file']):
                                column_mapping['CV'] = col
                                logger.info(f"Mapped 'CV' to '{col}'")
                                break
            
            # If we still have missing columns after guessing, use the first few columns
            still_missing = [col for col in required_columns if col not in column_mapping]
            if still_missing and len(df.columns) >= 3:
                for i, missing_col in enumerate(still_missing):
                    if i < len(df.columns):
                        column_mapping[missing_col] = df.columns[i]
                        logger.warning(f"Forced mapping '{missing_col}' to column '{df.columns[i]}'")
            
            # Process each row
            candidates = []
            for idx, row in df.iterrows():
                # Create candidate dictionary with mapped columns
                candidate = {}
                
                # Add required fields with proper mapping
                for req_col in required_columns:
                    if req_col in column_mapping:
                        col_value = row[column_mapping[req_col]]
                        # Handle NaN values
                        if pd.isna(col_value):
                            col_value = ""
                        
                        if req_col == 'Student Name':
                            candidate['name'] = str(col_value)
                        elif req_col == 'Skills':
                            candidate['skills'] = self._parse_skills(col_value)
                        elif req_col == 'CV':
                            candidate['cv_url'] = str(col_value)
                    else:
                        # Use empty defaults for missing required columns
                        if req_col == 'Student Name':
                            candidate['name'] = f"Candidate {idx+1}"
                        elif req_col == 'Skills':
                            candidate['skills'] = []
                        elif req_col == 'CV':
                            candidate['cv_url'] = ""
                
                # Add any additional columns as extra information
                for col in df.columns:
                    if col not in column_mapping.values():
                        col_key = col.lower().replace(' ', '_')
                        col_value = row[col]
                        # Handle NaN values
                        if pd.isna(col_value):
                            col_value = ""
                        candidate[col_key] = str(col_value)
                
                candidates.append(candidate)
            
            logger.info(f"Successfully parsed {len(candidates)} candidates")
            
            # If we have no candidates, something went wrong
            if not candidates:
                logger.error("No candidates were parsed from the file")
                raise ValueError("No candidates found in the input file")
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error parsing spreadsheet: {str(e)}")
            # Instead of using fallback data, raise the exception to make the error visible
            raise

    def parse_resume(self, candidate_data: Dict) -> Dict:
        """Parse a resume from a URL or file path
        
        Args:
            candidate_data: Dictionary containing candidate information including CV URL or resume_text
            
        Returns:
            Dictionary containing parsed resume data
        """
        try:
            logger.info(f"Parsing resume for candidate: {candidate_data.get('name', candidate_data.get('Student Name', 'Unknown'))}")
            
            # Check if resume text is already provided (for PDF uploads)
            resume_text = candidate_data.get('resume_text', '')
            
            # Get the CV URL from candidate data
            cv_url = candidate_data.get('cv_url', candidate_data.get('CV URL', ''))
            
            if not cv_url and not resume_text:
                logger.warning(f"No CV URL or resume text provided for candidate: {candidate_data.get('name', candidate_data.get('Student Name', 'Unknown'))}")
                return {
                    'error': 'No CV URL or resume text provided',
                    'source_url': '',
                    'personal_info': {'name': candidate_data.get('name', candidate_data.get('Student Name', 'Unknown'))},
                    'contact_info': {},
                    'education': [],
                    'experience': [],
                    'skills': {'technical': [], 'soft': [], 'all_skills': []},
                    'projects': [],
                    'links': {},
                    'additional': {}
                }
            
            if cv_url:
                logger.info(f"CV URL: {cv_url}")
            else:
                logger.info(f"Using provided resume text ({len(resume_text)} characters)")
            
            # If we have resume text, use Gemini to extract structured data
            if resume_text and self.use_gemini and self.gemini_client:
                logger.info(f"Using Gemini to extract structured data from resume text ({len(resume_text)} chars)")
                resume_data = self._extract_structured_data_with_gemini(resume_text, cv_url)
            else:
                # Fallback: use simple approach that extracts information from the candidate data
                logger.warning("Gemini not available or no resume text - using basic extraction")
                
                # Extract skills from candidate data
                skills = candidate_data.get('skills', candidate_data.get('Skills', []))
                if isinstance(skills, str):
                    skills = self._parse_skills(skills)
                
                # Create a basic resume structure
                resume_data = {
                    'source_url': cv_url,
                    'resume_text': resume_text,
                    'personal_info': {
                        'name': candidate_data.get('name', candidate_data.get('Student Name', 'Unknown')),
                        'location': candidate_data.get('location', candidate_data.get('Location', '')),
                        'summary': candidate_data.get('summary', candidate_data.get('Summary', ''))
                    },
                    'contact_info': {
                        'emails': [candidate_data.get('email', candidate_data.get('Email', ''))] if candidate_data.get('email') or candidate_data.get('Email') else [],
                        'phones': [candidate_data.get('phone', candidate_data.get('Phone', ''))] if candidate_data.get('phone') or candidate_data.get('Phone') else []
                    },
                    'education': [],
                    'experience': [],
                    'skills': {
                        'technical': skills,
                        'soft': [],
                        'all_skills': skills
                    },
                    'projects': [],
                    'links': {
                        'linkedin': candidate_data.get('linkedin', candidate_data.get('LinkedIn', '')),
                        'github': candidate_data.get('github', candidate_data.get('GitHub', '')),
                        'portfolio': candidate_data.get('portfolio', candidate_data.get('Portfolio', ''))
                    },
                    'additional': {}
                }
                
                # Add any education information if available
                if 'education' in candidate_data:
                    resume_data['education'] = [{'institution': candidate_data['education']}]
                
                # Add any experience information if available
                if 'experience' in candidate_data:
                    resume_data['experience'] = [{'company': candidate_data['experience']}]
            
            logger.info(f"Successfully parsed resume for candidate: {resume_data.get('personal_info', {}).get('name', 'Unknown')}")
            return resume_data
            
        except Exception as e:
            logger.error(f"Error parsing resume: {str(e)}")
            return {
                'error': str(e),
                'source_url': candidate_data.get('cv_url', ''),
                'personal_info': {'name': candidate_data.get('name', 'Unknown')},
                'contact_info': {},
                'education': [],
                'experience': [],
                'skills': {'technical': [], 'soft': [], 'all_skills': []},
                'projects': [],
                'links': {},
                'additional': {}
            }
    
    def _extract_structured_data_with_gemini(self, resume_text: str, source_url: str = '') -> Dict:
        """Extract structured data from resume text using Gemini
        
        Args:
            resume_text: Raw text extracted from resume
            source_url: Source URL of the resume
            
        Returns:
            Structured resume data dictionary
        """
        try:
            prompt = f"""You are an expert resume parser. Extract ALL information from this resume into a structured JSON format.

RESUME TEXT:
{resume_text}

Extract and return a valid JSON object with this exact structure:
{{
  "personal_info": {{
    "name": "Full name of the candidate",
    "location": "City, State/Country",
    "summary": "Professional summary or objective"
  }},
  "contact_info": {{
    "emails": ["email addresses found"],
    "phones": ["phone numbers found"],
    "linkedin": "LinkedIn URL if found",
    "github": "GitHub URL if found",
    "portfolio": "Portfolio URL if found",
    "other_links": ["other professional URLs"]
  }},
  "education": [
    {{
      "degree": "Degree name",
      "field": "Field of study",
      "institution": "University/College name",
      "location": "Location",
      "graduation_date": "Graduation date or year",
      "gpa": "GPA if mentioned",
      "honors": "Honors/awards if any"
    }}
  ],
  "experience": [
    {{
      "title": "Job title",
      "company": "Company name",
      "location": "Location",
      "start_date": "Start date",
      "end_date": "End date or Present",
      "description": "Job description",
      "responsibilities": ["List of responsibilities"],
      "achievements": ["List of achievements"]
    }}
  ],
  "skills": {{
    "technical": ["All technical skills, programming languages, frameworks, tools"],
    "soft": ["Soft skills like leadership, communication"],
    "certifications": ["Certifications"],
    "languages": ["Human languages with proficiency"]
  }},
  "projects": [
    {{
      "name": "Project name",
      "description": "Project description",
      "technologies": ["Technologies used"],
      "url": "Project URL if available",
      "highlights": ["Key achievements/features"]
    }}
  ],
  "additional": {{
    "awards": ["Awards and recognitions"],
    "publications": ["Publications"],
    "volunteer": ["Volunteer experience"],
    "interests": ["Professional interests"]
  }}
}}

IMPORTANT:
- Extract EVERY piece of information found in the resume
- If a field is not found, use empty string "" or empty array []
- Ensure all technical skills are captured (languages, frameworks, tools, platforms)
- Extract ALL URLs (LinkedIn, GitHub, portfolio, project links)
- Return ONLY valid JSON, no additional text
- Be thorough and accurate"""

            response = self.gemini_client.generate_content(prompt)
            
            # Clean the response to extract JSON
            response_text = response.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            elif response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            import json
            extracted_data = json.loads(response_text)
            
            # Merge contact URLs into links
            contact = extracted_data.get('contact_info', {})
            links = {
                'linkedin': contact.get('linkedin', ''),
                'github': contact.get('github', ''),
                'portfolio': contact.get('portfolio', ''),
                'other': contact.get('other_links', [])
            }
            
            # Create final structured data
            structured_data = {
                'source_url': source_url,
                'resume_text': resume_text[:500] + '...' if len(resume_text) > 500 else resume_text,  # Store preview
                'personal_info': extracted_data.get('personal_info', {}),
                'contact_info': {
                    'emails': contact.get('emails', []),
                    'phones': contact.get('phones', [])
                },
                'education': extracted_data.get('education', []),
                'experience': extracted_data.get('experience', []),
                'skills': extracted_data.get('skills', {'technical': [], 'soft': [], 'all_skills': []}),
                'projects': extracted_data.get('projects', []),
                'links': links,
                'additional': extracted_data.get('additional', {})
            }
            
            # Ensure all_skills combines technical and soft skills
            if 'all_skills' not in structured_data['skills']:
                structured_data['skills']['all_skills'] = (
                    structured_data['skills'].get('technical', []) + 
                    structured_data['skills'].get('soft', [])
                )
            
            logger.info(f"Successfully extracted structured data: {structured_data['personal_info'].get('name', 'Unknown')}")
            return structured_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini response: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            # Return basic structure with error
            return {
                'error': f'JSON parsing error: {str(e)}',
                'source_url': source_url,
                'resume_text': resume_text[:500] + '...',
                'personal_info': {'name': 'Extraction Failed'},
                'contact_info': {},
                'education': [],
                'experience': [],
                'skills': {'technical': [], 'soft': [], 'all_skills': []},
                'projects': [],
                'links': {},
                'additional': {}
            }
        except Exception as e:
            logger.error(f"Error extracting structured data with Gemini: {e}")
            return {
                'error': str(e),
                'source_url': source_url,
                'resume_text': resume_text[:500] + '...',
                'personal_info': {'name': 'Extraction Error'},
                'contact_info': {},
                'education': [],
                'experience': [],
                'skills': {'technical': [], 'soft': [], 'all_skills': []},
                'projects': [],
                'links': {},
                'additional': {}
            }
