import streamlit as st
import pandas as pd
import os
import json
import sys
import tempfile
import asyncio
from pathlib import Path
import logging
import time
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Add project root to path BEFORE local imports
project_root = Path(__file__).parent.parent.resolve()
project_root_str = str(project_root)
if project_root_str not in map(str, sys.path):
    sys.path.insert(0, project_root_str)
    print(f"Added {project_root_str} to sys.path")
print(f"sys.path: {sys.path}")

# Import our modules with robust error handling
try:
    from app.crew_manager import HRRecruitmentCrew
    from utils.document_parser import DocumentParser
    from agents.resume_analysis_agent import ResumeAnalysisAgent
    from agents.matching_agent import MatchingAgent
    from agents.research_agent import ResearchAgent
    from agents.validation_agent import ValidationAgent
    from agents.summarization_agent import SummarizationAgent
except ModuleNotFoundError as e:
    print(f"\n[IMPORT ERROR] {e}\n")
    print("\n[HINT] Make sure you are running Streamlit from the PROJECT ROOT directory, e.g.:")
    print("    streamlit run ui/streamlit_app.py\n")
    print(f"Current working directory: {os.getcwd()}")
    print(f"sys.path: {sys.path}")
    raise

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AI-Powered HR Recruitment System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #0D47A1;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .info-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #2196F3;
    }
    .success-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #4CAF50;
    }
    .warning-box {
        background-color: #FFF8E1;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #FF9800;
    }
    .error-box {
        background-color: #FFEBEE;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #F44336;
    }
    .candidate-card {
        background-color: #F8F9FA;
        padding: 1.5rem;
        border-radius: 0.8rem;
        margin-bottom: 1rem;
        border-left: 5px solid #1E88E5;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background-color: #FFFFFF;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        color: white;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .status-verified { background-color: #4CAF50; }
    .status-questionable { background-color: #FF9800; }
    .status-invalid { background-color: #F44336; }
    .status-pending { background-color: #9E9E9E; }
    
    .progress-container {
        background-color: #F5F5F5;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0
    if 'step_progress' not in st.session_state:
        st.session_state.step_progress = {}

def main():
    """Main application function"""
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.markdown('<p class="main-header">🤖 AI HR Recruiter</p>', unsafe_allow_html=True)
        st.markdown("Advanced AI-powered candidate recruitment and evaluation system")
        
        # API Key Management
        with st.expander("🔑 API Configuration", expanded=True):
            gemini_api_key = st.text_input("Google Gemini API Key *", type="password", 
                                         help="Required for AI-powered resume analysis. Get from https://makersuite.google.com/app/apikey")
            
            if gemini_api_key:
                os.environ["GEMINI_API_KEY"] = gemini_api_key
                st.success("✅ Gemini API configured")
            else:
                st.warning("⚠️ Gemini API key required")
            
        with st.expander("🔧 Optional API Keys"):
            github_token = st.text_input("GitHub API Token", type="password",
                                        help="For enhanced GitHub profile analysis")
            if github_token:
                os.environ["GITHUB_API_TOKEN"] = github_token
                st.success("✅ GitHub API configured")
            
            google_api_key = st.text_input("Google API Key", type="password",
                                            help="For web search capabilities")
            if google_api_key:
                os.environ["GOOGLE_API_KEY"] = google_api_key
                st.success("✅ Google API configured")
            
            linkedin_api_key = st.text_input("LinkedIn API Key", type="password",
                                            help="For LinkedIn profile analysis")
            if linkedin_api_key:
                os.environ["LINKEDIN_API_KEY"] = linkedin_api_key
                st.success("✅ LinkedIn API configured")
        
        # System Status
        with st.expander("📊 System Status"):
            if gemini_api_key:
                st.success("🟢 Core AI System: Ready")
            else:
                st.error("🔴 Core AI System: Not Ready")
            
            optional_services = [
                ("GitHub Research", "GITHUB_API_TOKEN"),
                ("Web Search", "GOOGLE_API_KEY"),
                ("LinkedIn Analysis", "LINKEDIN_API_KEY")
            ]
            
            for service, env_var in optional_services:
                if os.getenv(env_var):
                    st.success(f"🟢 {service}: Enabled")
                else:
                    st.info(f"⚪ {service}: Optional")

    # Main content
    st.markdown('<p class="main-header">🎯 AI-Powered Candidate Recruitment System</p>', unsafe_allow_html=True)

    # Information about the application
    with st.expander("ℹ️ About this AI Recruitment System", expanded=False):
        st.markdown("""
        This advanced HR recruitment system uses a team of specialized AI agents to comprehensively evaluate candidates:
        
        **🤖 AI Agent Pipeline:**
        1. **Resume Analysis Agent** - LLM-powered dynamic extraction from any resume format
        2. **Matching Agent** - Advanced semantic similarity and contextual matching
        3. **Research Agent** - Comprehensive web research across multiple platforms
        4. **Validation Agent** - Multi-layer identity and information verification
        5. **Summarization Agent** - Executive-ready reports and recommendations
        
        **🔍 Research Sources:**
        - LinkedIn, GitHub, Portfolio websites
        - Stack Overflow, LeetCode, HackerRank, Kaggle
        - Publications, Patents, Academic papers
        - Conference talks, Blog posts, Social presence
        
        **✅ Validation Features:**
        - Identity verification across platforms
        - Skill validation through actual work
        - Timeline consistency checks
        - Information credibility assessment
        
        **📊 Advanced Analytics:**
        - Semantic skill matching
        - Growth potential assessment
        - Cultural fit analysis
        - Risk assessment and mitigation
        """)

    # File upload section
    st.header("📁 Upload Files")
    with st.expander("Upload candidate and job files", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            uploaded_candidates = st.file_uploader("Upload Candidates Excel/CSV", type=["xlsx", "csv", "xls"])
            if uploaded_candidates:
                # Save the uploaded file to a temporary location
                temp_file_path = os.path.join(tempfile.gettempdir(), uploaded_candidates.name)
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_candidates.getvalue())
                st.session_state.candidates_file = temp_file_path
                st.success(f"Candidates file uploaded: {uploaded_candidates.name}")
                
                # Preview the data
                try:
                    parser = DocumentParser()
                    candidates_data = parser.parse_spreadsheet(temp_file_path)
                    st.write(f"✅ Successfully loaded {len(candidates_data)} candidates")
                    if candidates_data:
                        st.write(f"Sample: {candidates_data[0]['name']}")
                except Exception as e:
                    st.error(f"Error previewing candidates: {str(e)}")

        with col2:
            st.markdown("**Job Description**")
            job_description_method = st.radio(
                "Choose input method:",
                ["Text Input", "File Upload"],
                horizontal=True
            )
            
            if job_description_method == "Text Input":
                job_description = st.text_area(
                    "Paste job description here",
                    height=200,
                    placeholder="Enter the complete job description including requirements, responsibilities, and qualifications..."
                )
            else:
                uploaded_job_file = st.file_uploader(
                    "Upload job description file",
                    type=["txt", "pdf", "docx"],
                    help="Upload a file containing the job description"
                )
                job_description = ""
                if uploaded_job_file:
                    st.success(f"✅ Uploaded: {uploaded_job_file.name}")

    # Processing Section
    st.markdown('<p class="sub-header">🚀 Step 2: Start AI Analysis</p>', unsafe_allow_html=True)

    # Check if ready to process
    ready_to_process = bool(gemini_api_key and uploaded_candidates and 
                          (job_description if job_description_method == "Text Input" else uploaded_job_file))

    if not ready_to_process:
        missing_items = []
        if not gemini_api_key:
            missing_items.append("Gemini API Key")
        if not uploaded_candidates:
            missing_items.append("Candidate spreadsheet")
        if job_description_method == "Text Input" and not job_description:
            missing_items.append("Job description text")
        elif job_description_method == "File Upload" and not uploaded_job_file:
            missing_items.append("Job description file")
        
        st.markdown(f'<div class="warning-box">⚠️ Missing: {", ".join(missing_items)}</div>', 
                  unsafe_allow_html=True)

    # Processing button and status
    col1, col2 = st.columns([1, 3])
    
    with col1:
        start_processing = st.button(
            "🚀 Start AI Analysis",
            disabled=not ready_to_process,
            type="primary",
            use_container_width=True
        )

    with col2:
        if ready_to_process:
            st.markdown('<div class="success-box">✅ Ready to start comprehensive AI analysis</div>', 
                      unsafe_allow_html=True)

    # Processing Pipeline
    if start_processing or st.session_state.processing_complete:
        
        if start_processing and not st.session_state.processing_complete:
            # Get job description
            if job_description_method == "File Upload" and uploaded_job_file:
                # Handle file upload (simplified for this example)
                job_desc_text = "Job description from uploaded file"
                st.warning("📝 File parsing not fully implemented - please use text input for now")
            else:
                job_desc_text = job_description
            
            # Run the processing pipeline
            results = run_ai_recruitment_pipeline(st.session_state.candidates_file, job_desc_text)
            st.session_state.results = results
            st.session_state.processing_complete = True
        
        # Display results
        if st.session_state.results:
            display_results(st.session_state.results)

def run_ai_recruitment_pipeline(candidates_file: str, job_description: str) -> dict:
    """Run the complete AI recruitment pipeline"""
    
    # Initialize progress tracking
    total_steps = 5
    step_names = [
        "🔍 Resume Analysis",
        "🎯 Candidate Matching", 
        "🌐 Deep Research",
        "✅ Information Validation",
        "📊 Report Generation"
    ]
    
    # Create progress containers
    progress_container = st.container()
    status_container = st.container()
    
    with progress_container:
        st.markdown('<div class="progress-container">', unsafe_allow_html=True)
        st.markdown("### 🤖 AI Processing Pipeline")
        
        # Overall progress
        overall_progress = st.progress(0)
        current_step_text = st.empty()
        
        # Individual step progress
        step_progress_bars = {}
        step_status_text = {}
        
        for i, step_name in enumerate(step_names):
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(f"**{step_name}**")
            with col2:
                step_progress_bars[i] = st.progress(0)
                step_status_text[i] = st.empty()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    try:
        # Initialize components
        parser = DocumentParser()
        resume_agent = ResumeAnalysisAgent()
        matching_agent = MatchingAgent()
        research_agent = ResearchAgent()
        validation_agent = ValidationAgent()
        summarization_agent = SummarizationAgent()
        
        results = {}
        
        # Step 1: Resume Analysis
        current_step_text.markdown("**Current Step: 🔍 Resume Analysis**")
        step_status_text[0].markdown("Parsing candidate spreadsheet...")
        step_progress_bars[0].progress(0.2)
        
        candidates_data = parser.parse_spreadsheet(candidates_file)
        step_status_text[0].markdown(f"Processing {len(candidates_data)} resumes with AI...")
        step_progress_bars[0].progress(0.5)
        
        processed_candidates = resume_agent.process_candidates(candidates_data)
        step_status_text[0].markdown("✅ Resume analysis complete")
        step_progress_bars[0].progress(1.0)
        overall_progress.progress(0.2)
        
        # Step 2: Candidate Matching
        current_step_text.markdown("**Current Step: 🎯 Candidate Matching**")
        step_status_text[1].markdown("Analyzing job requirements...")
        step_progress_bars[1].progress(0.3)
        
        job_requirements = matching_agent.analyze_job_requirements(job_description)
        step_status_text[1].markdown("Matching candidates to requirements...")
        step_progress_bars[1].progress(0.7)
        
        matching_results = matching_agent.match_candidates(processed_candidates, job_requirements)
        top_candidates = matching_results['top_candidates']
        step_status_text[1].markdown(f"✅ Selected {len(top_candidates)} top candidates")
        step_progress_bars[1].progress(1.0)
        overall_progress.progress(0.4)
        
        # Step 3: Deep Research
        current_step_text.markdown("**Current Step: 🌐 Deep Research**")
        step_status_text[2].markdown("Researching candidate online presence...")
        step_progress_bars[2].progress(0.2)
        
        # Use asyncio for research
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        step_status_text[2].markdown("Gathering data from multiple platforms...")
        step_progress_bars[2].progress(0.6)
        
        researched_candidates = loop.run_until_complete(
            research_agent.research_candidates(top_candidates)
        )
        
        step_status_text[2].markdown("✅ Research complete")
        step_progress_bars[2].progress(1.0)
        overall_progress.progress(0.6)
        
        # Step 4: Validation
        current_step_text.markdown("**Current Step: ✅ Information Validation**")
        step_status_text[3].markdown("Validating candidate information...")
        step_progress_bars[3].progress(0.4)
        
        validated_candidates = validation_agent.validate_candidates(researched_candidates)
        step_status_text[3].markdown("Cross-referencing data sources...")
        step_progress_bars[3].progress(0.8)
        
        step_status_text[3].markdown("✅ Validation complete")
        step_progress_bars[3].progress(1.0)
        overall_progress.progress(0.8)
        
        # Step 5: Report Generation
        current_step_text.markdown("**Current Step: 📊 Report Generation**")
        step_status_text[4].markdown("Generating comprehensive report...")
        step_progress_bars[4].progress(0.3)
        
        final_report = summarization_agent.generate_comprehensive_report(
            validated_candidates, job_requirements, matching_results
        )
        
        step_status_text[4].markdown("Creating visualizations...")
        step_progress_bars[4].progress(0.7)
        
        # Save report
        report_file = summarization_agent.save_report(final_report)
        step_status_text[4].markdown("✅ Report generation complete")
        step_progress_bars[4].progress(1.0)
        overall_progress.progress(1.0)
        
        current_step_text.markdown("**🎉 Processing Complete!**")
        
        return {
            'candidates_data': candidates_data,
            'processed_candidates': processed_candidates,
            'job_requirements': job_requirements,
            'matching_results': matching_results,
            'researched_candidates': researched_candidates,
            'validated_candidates': validated_candidates,
            'final_report': final_report,
            'report_file': report_file
        }
        
    except Exception as e:
        st.error(f"❌ Processing error: {str(e)}")
        return None

def display_results(results: dict):
    """Display the comprehensive results"""
    
    if not results:
        st.error("❌ No results to display")
        return
    
    st.markdown("---")
    st.markdown('<p class="main-header">📊 Recruitment Results</p>', unsafe_allow_html=True)
    
    final_report = results.get('final_report', {})
    
    # Handle case where final_report or executive_summary might be strings
    if isinstance(final_report, str):
        try:
            # Try to parse it as JSON
            final_report = json.loads(final_report)
        except:
            # If it can't be parsed, create a simple dict
            final_report = {"text": final_report}
    
    executive_summary = final_report.get('executive_summary', {})
    if isinstance(executive_summary, str):
        try:
            # Try to parse it as JSON
            executive_summary = json.loads(executive_summary)
        except:
            # If it can't be parsed, create a simple dict
            executive_summary = {"text": executive_summary}
    
    candidate_profiles = final_report.get('candidate_profiles', [])
    if isinstance(candidate_profiles, str):
        try:
            # Try to parse it as JSON
            candidate_profiles = json.loads(candidate_profiles)
        except:
            # If it can't be parsed, use an empty list
            candidate_profiles = []
    
    # Executive Summary
    with st.expander("📋 Executive Summary", expanded=True):
        display_executive_summary(executive_summary)
    
    # Top Candidates
    with st.expander("🏆 Top Candidates", expanded=True):
        display_top_candidates(candidate_profiles[:5])
    
    # Detailed Analysis
    with st.expander("📈 Detailed Analysis", expanded=False):
        detailed_analysis = final_report.get('detailed_analysis', {})
        if isinstance(detailed_analysis, str):
            try:
                detailed_analysis = json.loads(detailed_analysis)
            except:
                detailed_analysis = {"text": detailed_analysis}
        display_detailed_analysis(detailed_analysis)
    
    # All Candidates
    with st.expander("👥 All Candidates", expanded=False):
        display_all_candidates(candidate_profiles)

def display_executive_summary(executive_summary):
    """Display executive summary"""
    
    # Handle case where executive_summary is a string
    if isinstance(executive_summary, str):
        st.markdown(executive_summary)
        return
    
    process_overview = executive_summary.get('process_overview', {})
    if isinstance(process_overview, str):
        try:
            process_overview = json.loads(process_overview)
        except:
            st.markdown(f"**Process Overview:** {process_overview}")
            process_overview = {}
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Candidates", 
            process_overview.get('total_candidates_processed', 0)
        )
    
    with col2:
        st.metric(
            "Verified Candidates", 
            process_overview.get('candidates_with_verified_identity', 0)
        )
    
    with col3:
        st.metric(
            "Avg Confidence", 
            f"{process_overview.get('average_validation_confidence', 0)}%"
        )
    
    with col4:
        research_sources = process_overview.get('research_sources_utilized', {})
        if isinstance(research_sources, str):
            try:
                research_sources = json.loads(research_sources)
            except:
                research_sources = {}
        total_sources = sum(research_sources.values()) if research_sources else 0
        st.metric("Research Sources", total_sources)
    
    # Key findings
    key_findings = executive_summary.get('key_findings', [])
    if isinstance(key_findings, str):
        try:
            key_findings = json.loads(key_findings)
        except:
            key_findings = [key_findings]
    
    if key_findings:
        st.markdown("**🔍 Key Findings:**")
        for finding in key_findings:
            st.markdown(f"• {finding}")
    
    # Recommendations
    recommendations = executive_summary.get('recommendations', {})
    if isinstance(recommendations, str):
        try:
            recommendations = json.loads(recommendations)
        except:
            st.markdown(f"**📌 Recommendations:** {recommendations}")
            recommendations = {}
    
    if recommendations:
        st.markdown("**📌 Immediate Recommendations:**")
        immediate_actions = recommendations.get('immediate_action', [])
        if isinstance(immediate_actions, str):
            try:
                immediate_actions = json.loads(immediate_actions)
            except:
                immediate_actions = [immediate_actions]
        
        for action in immediate_actions:
            st.markdown(f"• {action}")

def display_top_candidates(top_candidates: list):
    """Display top candidates with enhanced formatting"""
    
    for i, candidate in enumerate(top_candidates):
        with st.container():
            st.markdown(f'<div class="candidate-card">', unsafe_allow_html=True)
            
            # Header
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                name = candidate.get('basic_information', {}).get('name', 'Unknown')
                st.markdown(f"### #{i+1}: {name}")
            
            with col2:
                overall_score = candidate.get('overall_recommendation', {}).get('confidence_level', 0)
                st.metric("Overall Score", f"{overall_score}%")
            
            with col3:
                validation_status = candidate.get('validation_assessment', {}).get('overall_status', 'Unknown')
                status_class = f"status-{validation_status.lower().replace(' ', '-')}"
                st.markdown(f'<span class="status-badge {status_class}">{validation_status}</span>', 
                          unsafe_allow_html=True)
            
            # Details
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📧 Contact:**")
                basic_info = candidate.get('basic_information', {})
                st.markdown(f"• Email: {basic_info.get('email', 'N/A')}")
                st.markdown(f"• Location: {basic_info.get('location', 'N/A')}")
                
                st.markdown("**💼 Experience:**")
                exp_summary = candidate.get('professional_summary', {}).get('experience_summary', {})
                st.markdown(f"• Current Role: {exp_summary.get('current_role', 'N/A')}")
                st.markdown(f"• Company: {exp_summary.get('current_company', 'N/A')}")
                st.markdown(f"• Total Positions: {exp_summary.get('total_positions', 0)}")
            
            with col2:
                st.markdown("**🛠️ Technical Skills:**")
                tech_skills = candidate.get('technical_assessment', {}).get('verified_skills', [])
                if tech_skills:
                    skills_display = ', '.join(tech_skills[:8])
                    if len(tech_skills) > 8:
                        skills_display += f" +{len(tech_skills)-8} more"
                    st.markdown(skills_display)
                else:
                    st.markdown("Skills assessment in progress")
                
                st.markdown("**🌟 Key Strengths:**")
                strengths = candidate.get('strengths_and_concerns', {}).get('key_strengths', [])
                for strength in strengths[:3]:
                    st.markdown(f"• {strength}")
            
            # Recommendation
            recommendation = candidate.get('overall_recommendation', {})
            rec_status = recommendation.get('recommendation', 'PENDING')
            rec_color = {
                'STRONGLY RECOMMEND': 'success',
                'RECOMMEND': 'success', 
                'CONDITIONAL RECOMMEND': 'warning',
                'DO NOT RECOMMEND': 'error'
            }.get(rec_status, 'info')
            
            st.markdown(f"**🎯 Recommendation:** :{rec_color}[{rec_status}]")
            st.markdown(f"*{recommendation.get('rationale', 'Analysis in progress...')}*")
            
            st.markdown('</div>', unsafe_allow_html=True)

def display_detailed_analysis(detailed_analysis: dict):
    """Display detailed analysis with charts"""
    
    # Skill gap analysis
    skill_gaps = detailed_analysis.get('skill_gap_analysis', {})
    if skill_gaps:
        st.markdown("### 📊 Skill Gap Analysis")
        
        coverage_analysis = skill_gaps.get('skill_coverage_analysis', {})
        if coverage_analysis:
            # Create skill coverage chart
            skills = list(coverage_analysis.keys())
            coverage_percentages = [data.get('coverage_percentage', 0) for data in coverage_analysis.values()]
            
            fig = px.bar(
                x=skills,
                y=coverage_percentages,
                title="Skill Coverage Across Candidates",
                labels={'x': 'Skills', 'y': 'Coverage Percentage (%)'},
                color=coverage_percentages,
                color_continuous_scale='RdYlGn'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Market insights
    market_insights = detailed_analysis.get('market_insights', {})
    if market_insights:
        st.markdown("### 💰 Market Insights")
        # Display market insights
        
    # Risk analysis
    risk_analysis = detailed_analysis.get('risk_analysis', {})
    if risk_analysis:
        st.markdown("### ⚠️ Risk Analysis")
        # Display risk analysis

def display_all_candidates(candidate_profiles: list):
    """Display all candidates in a table format"""
    
    if not candidate_profiles:
        st.warning("No candidate profiles available")
        return
    
    # Create summary table
    table_data = []
    for candidate in candidate_profiles:
        basic_info = candidate.get('basic_information', {})
        validation = candidate.get('validation_assessment', {})
        recommendation = candidate.get('overall_recommendation', {})
        
        table_data.append({
            'Rank': candidate.get('rank', 0),
            'Name': basic_info.get('name', 'Unknown'),
            'Email': basic_info.get('email', 'N/A'),
            'Overall Score': f"{recommendation.get('confidence_level', 0)}%",
            'Validation Status': validation.get('overall_status', 'Unknown'),
            'Recommendation': recommendation.get('recommendation', 'PENDING')
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()
