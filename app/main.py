#!/usr/bin/env python3
"""
AI-Powered HR Recruitment System - Main Application
===================================================

This is the main command-line interface for the HR recruitment system.
It provides a complete pipeline for candidate evaluation using AI agents.

Usage:
    python app/main.py --input candidates.xlsx --job job_description.txt
    python app/main.py --help

Features:
- Gemini-powered resume analysis
- Advanced candidate matching
- Comprehensive web research
- Identity validation and verification
- Executive-ready reports

Requirements:
- Google Gemini API key (required)
- Optional: GitHub, Google, LinkedIn API keys for enhanced functionality
"""

import logging
import os
import sys
import argparse
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import our modules
from app.crew_manager import HRRecruitmentCrew
from utils.document_parser import LLMDocumentParser
import traceback

# Set up logging
def setup_logging(verbose: bool = False):
    """Set up logging configuration"""
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(logs_dir / f"hr_recruitment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger(__name__)

def validate_environment():
    """Validate that required environment variables are set"""
    required_keys = ['GEMINI_API_KEY']
    missing_keys = []
    
    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)
    
    if missing_keys:
        print(f"❌ Error: Missing required environment variables: {', '.join(missing_keys)}")
        print("\nPlease set up your .env file with the required API keys.")
        print("Get your Gemini API key from: https://makersuite.google.com/app/apikey")
        return False
    
    # Check optional keys and inform about enhanced features
    optional_keys = {
        'GITHUB_API_TOKEN': 'Enhanced GitHub analysis',
        'GOOGLE_API_KEY': 'Web search capabilities',
        'LINKEDIN_API_KEY': 'LinkedIn profile analysis',
        'GOOGLE_APPLICATION_CREDENTIALS': 'Google Docs access'
    }
    
    configured_optional = []
    missing_optional = []
    
    for key, description in optional_keys.items():
        if os.getenv(key):
            configured_optional.append(f"{key} ({description})")
        else:
            missing_optional.append(f"{key} ({description})")
    
    print("🔑 API Configuration Status:")
    print(f"✅ Required: Google Gemini API configured")
    
    if configured_optional:
        print(f"✅ Optional configured: {len(configured_optional)} APIs")
        for api in configured_optional:
            print(f"   • {api}")
    
    if missing_optional:
        print(f"⚠️  Optional not configured: {len(missing_optional)} APIs")
        print("   Note: These APIs enhance functionality but are not required")
    
    return True

def validate_input_files(input_file: str, job_file: str) -> bool:
    """Validate that input files exist and are readable"""
    errors = []
    
    # Check input file
    if not os.path.exists(input_file):
        errors.append(f"Input file not found: {input_file}")
    elif not input_file.lower().endswith(('.xlsx', '.csv', '.xls')):
        errors.append(f"Input file must be Excel (.xlsx, .xls) or CSV (.csv): {input_file}")
    
    # Check job description file
    if not os.path.exists(job_file):
        errors.append(f"Job description file not found: {job_file}")
    elif not job_file.lower().endswith(('.txt', '.md', '.doc', '.docx')):
        errors.append(f"Job description file must be text (.txt, .md) or Word (.doc, .docx): {job_file}")
    
    if errors:
        print("❌ Input Validation Errors:")
        for error in errors:
            print(f"   • {error}")
        return False
    
    return True

def preview_input_data(input_file: str) -> Optional[Dict]:
    """Preview the input data and validate structure"""
    try:
        print(f"\n📋 Previewing input data from: {input_file}")
        
        # Verify the file exists
        if not os.path.isfile(input_file):
            print(f"❌ File not found: {input_file}")
            return None
        
        # Log file details
        file_size = os.path.getsize(input_file)
        _, file_extension = os.path.splitext(input_file)
        print(f"📄 File size: {file_size} bytes, extension: {file_extension}")
        
        # Parse the spreadsheet
        parser = LLMDocumentParser()
        candidates_data = parser.parse_spreadsheet(input_file)
        
        print(f"✅ Successfully loaded {len(candidates_data)} candidates")
        
        # Display sample data
        if candidates_data:
            sample_candidate = candidates_data[0]
            print("\n📊 Sample candidate data:")
            print(f"  Name: {sample_candidate.get('name', 'N/A')}")
            print(f"  Skills: {', '.join(sample_candidate.get('skills', []))[:100]}...")
            print(f"  CV URL: {sample_candidate.get('cv_url', 'N/A')}")
            
            # Check for additional fields
            additional_fields = [k for k in sample_candidate.keys() 
                               if k not in ['name', 'skills', 'cv_url']]
            if additional_fields:
                print(f"  Additional fields: {', '.join(additional_fields)}")
        
        return {
            "candidates_count": len(candidates_data),
            "sample": candidates_data[0] if candidates_data else None,
            "columns": list(candidates_data[0].keys()) if candidates_data else []
        }
        
    except Exception as e:
        print(f"❌ Error previewing input data: {str(e)}")
        traceback.print_exc()
        return None

def preview_job_description(job_file: str) -> bool:
    """Preview the job description"""
    try:
        print(f"\n📋 Previewing job description from: {job_file}")
        
        with open(job_file, 'r', encoding='utf-8') as f:
            job_content = f.read()
        
        print(f"✅ Job description loaded ({len(job_content)} characters)")
        
        # Show preview
        preview_length = 300
        preview = job_content[:preview_length]
        if len(job_content) > preview_length:
            preview += "..."
        
        print(f"\n📄 Job description preview:")
        print(f"   {preview}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading job description: {str(e)}")
        return False

class ProgressTracker:
    """Simple progress tracker for command-line interface"""
    
    def __init__(self):
        self.current_stage = ""
        self.stage_progress = 0
        
    def update(self, stage: str, progress: int, message: str = ""):
        """Update progress"""
        if stage != self.current_stage:
            if self.current_stage:
                print()  # New line for new stage
            self.current_stage = stage
            print(f"\n🔄 {stage.replace('_', ' ').title()}")
        
        # Simple progress indicator
        if progress == 0:
            print(f"   ⏳ {message}")
        elif progress == 100:
            print(f"   ✅ {message}")
        else:
            print(f"   🔄 {message} ({progress}%)")

def run_recruitment_pipeline(input_file: str, job_file: str, verbose: bool = False) -> bool:
    """Run the complete recruitment pipeline"""
    
    print("\n" + "="*60)
    print("🤖 AI-POWERED HR RECRUITMENT SYSTEM")
    print("="*60)
    
    try:
        # Initialize progress tracker
        progress_tracker = ProgressTracker()
        
        # Initialize the crew manager
        print("\n🚀 Initializing AI recruitment system...")
        crew_manager = HRRecruitmentCrew(model="gpt-4o-mini")
        
        # Load input data
        print("\n📁 Loading input data...")
        candidates_data = crew_manager.load_candidates_from_file(input_file)
        job_description = crew_manager.load_job_description_from_file(job_file)
        
        print(f"✅ Loaded {len(candidates_data)} candidates")
        print(f"✅ Loaded job description ({len(job_description)} characters)")
        
        # Define progress callback
        def progress_callback(stage: str, progress: int, message: str):
            progress_tracker.update(stage, progress, message)
        
        # Run the complete process
        print("\n🎯 Starting comprehensive candidate analysis...")
        print("This may take several minutes depending on the number of candidates and API response times.")
        
        start_time = datetime.now()
        
        results = crew_manager.run_complete_recruitment_process(
            progress_callback=progress_callback
        )
        
        end_time = datetime.now()
        processing_time = end_time - start_time
        
        print(f"\n🎉 Processing completed successfully!")
        print(f"⏱️  Total processing time: {processing_time}")
        
        # Display results summary
        display_results_summary(results, crew_manager)
        
        # Save results
        save_results(results, crew_manager)
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        return False
        
    except Exception as e:
        print(f"\n❌ Error during processing: {str(e)}")
        if verbose:
            print(f"\nDetailed error information:")
            traceback.print_exc()
        return False

def display_results_summary(results: Dict, crew_manager: HRRecruitmentCrew):
    """Display a summary of the results"""
    
    print("\n" + "="*60)
    print("📊 RECRUITMENT RESULTS SUMMARY")
    print("="*60)
    
    try:
        # Get process summary
        summary = crew_manager.get_process_summary()
        
        # Display key metrics
        print("\n📈 Key Metrics:")
        candidate_metrics = summary.get('candidate_metrics', {})
        print(f"   • Total candidates processed: {candidate_metrics.get('total_processed', 0)}")
        print(f"   • Top candidates selected: {candidate_metrics.get('top_selected', 0)}")
        print(f"   • Final candidates validated: {candidate_metrics.get('final_validated', 0)}")
        
        # Display top candidates
        top_candidates = crew_manager.get_top_candidates(limit=5)
        
        if top_candidates:
            print(f"\n🏆 Top {len(top_candidates)} Candidates:")
            
            for i, candidate in enumerate(top_candidates, 1):
                basic_info = candidate.get('basic_information', {})
                recommendation = candidate.get('overall_recommendation', {})
                validation = candidate.get('validation_assessment', {})
                
                name = basic_info.get('name', 'Unknown')
                confidence = recommendation.get('confidence_level', 0)
                rec_status = recommendation.get('recommendation', 'PENDING')
                val_status = validation.get('overall_status', 'Unknown')
                
                print(f"\n   {i}. {name}")
                print(f"      📊 Overall Score: {confidence}%")
                print(f"      💼 Recommendation: {rec_status}")
                print(f"      ✅ Validation: {val_status}")
                
                # Show key strengths
                strengths = candidate.get('strengths_and_concerns', {}).get('key_strengths', [])
                if strengths:
                    print(f"      🌟 Key Strengths: {strengths[0]}")
        
        # Display key findings
        key_findings = summary.get('key_findings', [])
        if key_findings:
            print(f"\n🔍 Key Findings:")
            for finding in key_findings[:3]:
                print(f"   • {finding}")
        
        # Display recommendations
        recommendations = summary.get('recommendations', {})
        immediate_actions = recommendations.get('immediate_action', [])
        if immediate_actions:
            print(f"\n📌 Immediate Recommendations:")
            for action in immediate_actions[:3]:
                print(f"   • {action}")
        
    except Exception as e:
        print(f"❌ Error displaying results summary: {str(e)}")

def save_results(results: Dict, crew_manager: HRRecruitmentCrew):
    """Save results to files"""
    
    print("\n💾 Saving Results:")
    
    try:
        # The results are automatically saved by the crew manager
        report_file = results.get('report_file_path')
        
        if report_file:
            print(f"✅ Complete report saved: {report_file}")
        
        # Export additional formats
        try:
            csv_file = crew_manager.export_results(format_type="csv")
            print(f"✅ CSV summary saved: {csv_file}")
        except Exception as e:
            print(f"⚠️  Could not save CSV: {str(e)}")
        
        # Display file locations
        output_dir = Path("output")
        if output_dir.exists():
            print(f"\n📁 All output files are in: {output_dir.absolute()}")
        
    except Exception as e:
        print(f"❌ Error saving results: {str(e)}")

def main():
    """Main application entry point"""
    
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="AI-Powered HR Recruitment System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app/main.py --input candidates.xlsx --job job_description.txt
  python app/main.py --input data/candidates.csv --job requirements.txt --verbose
  python app/main.py --help

Required Environment Variables:
  OPENAI_API_KEY        - OpenAI API key for LLM processing
  
Optional Environment Variables (for enhanced functionality):
  GITHUB_API_TOKEN      - GitHub API token for repository analysis
  GOOGLE_API_KEY        - Google API key for web search
  LINKEDIN_API_KEY      - LinkedIn API key for profile analysis
  
For complete setup instructions, see the .env.example file.
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to the input file (Excel/CSV) with candidate data. Must contain columns: Student Name, Skills, CV'
    )
    
    parser.add_argument(
        '--job', '-j',
        required=True,
        help='Path to the job description file (text, markdown, or Word document)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging and detailed error messages'
    )
    
    parser.add_argument(
        '--preview-only',
        action='store_true',
        help='Only preview the input data without processing (useful for validation)'
    )
    
    parser.add_argument(
        '--no-validation',
        action='store_true',
        help='Skip input validation checks (not recommended)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(verbose=args.verbose)
    
    # Print header
    print("🤖 AI-Powered HR Recruitment System")
    print("===================================")
    print("Advanced candidate evaluation using specialized AI agents")
    print()
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Validate input files (unless skipped)
    if not args.no_validation:
        if not validate_input_files(args.input, args.job):
            sys.exit(1)
    
    # Preview input data
    input_summary = preview_input_data(args.input)
    if not input_summary:
        print("❌ Could not preview input data. Please check the file format.")
        sys.exit(1)
    
    # Preview job description
    if not preview_job_description(args.job):
        print("❌ Could not preview job description. Please check the file.")
        sys.exit(1)
    
    # If preview-only mode, exit here
    if args.preview_only:
        print("\n✅ Preview completed successfully. Use without --preview-only to process candidates.")
        sys.exit(0)
    
    # Quality check
    data_quality = input_summary.get('data_quality', 0)
    if data_quality < 50:
        print(f"\n⚠️  Warning: Data quality is low ({data_quality:.1f}%)")
        print("   Many candidates are missing CV links or skills information.")
        
        response = input("   Continue anyway? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ Processing cancelled. Please improve data quality and try again.")
            sys.exit(1)
    
    # Confirm processing
    print(f"\n🎯 Ready to process {input_summary['total_candidates']} candidates")
    print("   This will use AI to analyze resumes, research candidates, and generate reports.")
    print("   Estimated processing time: 2-10 minutes depending on candidate count and API speed.")
    
    if not args.verbose:  # Only ask for confirmation in non-verbose mode
        response = input("\n   Start processing? (Y/n): ").strip().lower()
        if response in ['n', 'no']:
            print("❌ Processing cancelled by user.")
            sys.exit(0)
    
    # Run the recruitment pipeline
    success = run_recruitment_pipeline(args.input, args.job, args.verbose)
    
    if success:
        print("\n🎉 Recruitment analysis completed successfully!")
        print("📊 Check the output directory for detailed reports and results.")
        sys.exit(0)
    else:
        print("\n❌ Recruitment analysis failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
