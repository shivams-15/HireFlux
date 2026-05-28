"""
FastAPI Backend for HireFlux - AI-Powered HR Recruitment System
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import sys
import tempfile
import json
import asyncio
import uuid
from pathlib import Path
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.crew_manager import HRRecruitmentCrew
from utils.document_parser import DocumentParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HireFlux API",
    description="AI-Powered HR Recruitment System API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for job statuses (replace with Redis/DB in production)
job_status_store = {}

# Pydantic models
class APIKeyConfig(BaseModel):
    gemini_api_key: str
    github_api_token: Optional[str] = None
    google_api_key: Optional[str] = None
    linkedin_api_key: Optional[str] = None

class JobDescriptionInput(BaseModel):
    text: str

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    current_step: str
    message: Optional[str] = None
    result: Optional[Dict] = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "HireFlux API",
        "version": "1.0.0"
    }

@app.get("/api/config")
async def get_api_config():
    """Get API configuration status from environment"""
    try:
        return {
            "configured": bool(os.getenv("GEMINI_API_KEY")),
            "services": {
                "gemini": bool(os.getenv("GEMINI_API_KEY")),
                "github": bool(os.getenv("GITHUB_API_TOKEN")),
                "google_search": bool(os.getenv("GOOGLE_API_KEY")),
                "linkedin": bool(os.getenv("LINKEDIN_API_KEY"))
            }
        }
    except Exception as e:
        logger.error(f"Config check error: {str(e)}")
        return {
            "configured": False,
            "services": {}
        }

@app.post("/api/upload-candidates")
async def upload_candidates(file: UploadFile = File(...)):
    """Upload and validate candidate spreadsheet or resume PDF"""
    try:
        # Save uploaded file to temporary location
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        parser = DocumentParser()
        
        # Check if it's a PDF resume or spreadsheet
        if file.filename.lower().endswith('.pdf'):
            # Parse single PDF resume and extract structured data
            resume_text = parser.parse_pdf(file_path)
            
            # Use Gemini to extract basic info for preview
            parsed_resume = parser._extract_structured_data_with_gemini(resume_text, file_path)
            
            candidates_data = [{
                'Student Name': parsed_resume.get('personal_info', {}).get('name', 'Candidate'),
                'name': parsed_resume.get('personal_info', {}).get('name', 'Candidate'),
                'CV URL': file_path,
                'cv_url': file_path,
                'Email': parsed_resume.get('contact_info', {}).get('emails', [''])[0],
                'email': parsed_resume.get('contact_info', {}).get('emails', [''])[0],
                'resume_text': resume_text,
                'source_file': file.filename
            }]
            file_type = 'resume'
        else:
            # Parse spreadsheet
            candidates_data = parser.parse_spreadsheet(file_path)
            file_type = 'spreadsheet'
        
        return {
            "success": True,
            "file_path": file_path,
            "file_type": file_type,
            "candidates_count": len(candidates_data),
            "preview": candidates_data[0] if candidates_data else None,
            "message": f"Successfully loaded {len(candidates_data)} candidate{'s' if len(candidates_data) != 1 else ''}"
        }
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@app.post("/api/process")
async def start_processing(
    background_tasks: BackgroundTasks,
    candidates_file: str = Form(...),
    job_description: str = Form(...)
):
    """Start the AI recruitment processing pipeline"""
    try:
        # Check if API keys are configured
        if not os.getenv("GEMINI_API_KEY"):
            raise HTTPException(
                status_code=400, 
                detail="GEMINI_API_KEY not found in backend .env file. Please configure it."
            )
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        job_status_store[job_id] = {
            "status": "started",
            "progress": 0.0,
            "current_step": "Initializing...",
            "started_at": datetime.now().isoformat()
        }
        
        # Start processing in background (API keys loaded from .env)
        background_tasks.add_task(
            process_recruitment_pipeline,
            job_id,
            candidates_file,
            job_description
        )
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "Processing started successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process start error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a processing job"""
    if job_id not in job_status_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_status_store[job_id]

@app.get("/api/result/{job_id}")
async def get_job_result(job_id: str):
    """Get the result of a completed job"""
    if job_id not in job_status_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = job_status_store[job_id]
    
    if job_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    return {
        "job_id": job_id,
        "result": job_data.get("result"),
        "completed_at": job_data.get("completed_at")
    }

async def process_recruitment_pipeline(job_id: str, candidates_file: str, job_description: str):
    """Background task to process the recruitment pipeline"""
    try:
        # Update status
        def update_status(step: str, progress: float, message: str = ""):
            job_status_store[job_id].update({
                "current_step": step,
                "progress": progress,
                "message": message,
                "status": "processing"
            })
        
        # Initialize components
        parser = DocumentParser()
        crew = HRRecruitmentCrew()
        
        # Step 1: Parse candidates
        update_status("Resume Analysis", 0.1, "Parsing candidate data...")
        
        # Check if it's a PDF resume or spreadsheet
        if candidates_file.lower().endswith('.pdf'):
            # Parse single PDF resume and extract structured data
            resume_text = parser.parse_pdf(candidates_file)
            
            # Use Gemini to extract basic info
            parsed_resume = parser._extract_structured_data_with_gemini(resume_text, candidates_file)
            
            candidates_data = [{
                'Student Name': parsed_resume.get('personal_info', {}).get('name', 'Candidate'),
                'name': parsed_resume.get('personal_info', {}).get('name', 'Candidate'),
                'CV URL': candidates_file,
                'cv_url': candidates_file,
                'Email': parsed_resume.get('contact_info', {}).get('emails', [''])[0],
                'email': parsed_resume.get('contact_info', {}).get('emails', [''])[0],
                'resume_text': resume_text,
                'source_file': os.path.basename(candidates_file)
            }]
        else:
            # Parse spreadsheet
            candidates_data = parser.parse_spreadsheet(candidates_file)
        
        crew.set_candidates_data(candidates_data)
        
        # Step 2: Set job description
        update_status("Resume Analysis", 0.2, "Analyzing job requirements...")
        crew.set_job_description(job_description)
        
        # Step 3: Resume Analysis
        update_status("Resume Analysis", 0.25, f"Processing {len(candidates_data)} resumes with AI...")
        processed_candidates = crew.resume_analysis_agent.process_candidates(candidates_data)
        
        # Step 4: Matching
        update_status("Candidate Matching", 0.4, "Matching candidates to requirements...")
        job_requirements = crew.matching_agent.analyze_job_requirements(job_description)
        matching_results = crew.matching_agent.match_candidates(processed_candidates, job_requirements)
        top_candidates = matching_results['top_candidates']
        
        # Step 5: Research
        update_status("Deep Research", 0.6, f"Researching {len(top_candidates)} top candidates...")
        researched_candidates = await crew.research_agent.research_candidates(top_candidates)
        
        # Step 6: Validation
        update_status("Information Validation", 0.75, "Validating candidate information...")
        validated_candidates = crew.validation_agent.validate_candidates(researched_candidates)
        
        # Step 7: Report Generation
        update_status("Report Generation", 0.9, "Generating comprehensive report...")
        final_report = crew.summarization_agent.generate_comprehensive_report(
            validated_candidates, job_requirements, matching_results
        )
        
        # Save report
        report_file = crew.summarization_agent.save_report(final_report)
        
        # Complete
        job_status_store[job_id].update({
            "status": "completed",
            "progress": 1.0,
            "current_step": "Complete",
            "message": "Processing completed successfully",
            "completed_at": datetime.now().isoformat(),
            "result": {
                "final_report": final_report,
                "report_file": str(report_file),
                "candidates_processed": len(candidates_data),
                "top_candidates_count": len(top_candidates)
            }
        })
        
    except Exception as e:
        logger.error(f"Processing error for job {job_id}: {str(e)}")
        job_status_store[job_id].update({
            "status": "failed",
            "message": str(e),
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
