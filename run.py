#!/usr/bin/env python3
"""
AI-Powered HR Recruitment System - Main Entry Point
===================================================

This is the main entry point for the HR recruitment system.
It provides both web interface and command-line interface options.

Usage:
    python run.py --ui                              # Launch web interface
    python run.py --input candidates.xlsx --job job_description.txt  # CLI mode
    python run.py --help                            # Show help

Features:
- Modern Streamlit web interface
- Command-line interface for automation
- Complete AI-powered recruitment pipeline
- Executive-ready reports and analysis

Requirements:
- Python 3.8+
- Google Gemini API key (required)
- Optional: GitHub, Google, LinkedIn API keys for enhanced functionality
"""

import os
import sys
import argparse
from pathlib import Path

def main():
    """Main entry point for the HR Recruiting Agent System"""
    
    # ASCII art header
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║    🤖 AI-POWERED HR RECRUITMENT SYSTEM                        ║
    ║                                                               ║
    ║    Advanced candidate evaluation using specialized AI agents  ║
    ║    ✓ Dynamic resume parsing    ✓ Deep web research           ║
    ║    ✓ Semantic matching        ✓ Identity validation          ║
    ║    ✓ Executive reports        ✓ Risk assessment              ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    parser = argparse.ArgumentParser(
        description='AI-Powered HR Recruitment System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🚀 Quick Start Examples:

  # Launch modern web interface
  python run.py --ui
  
  # Process candidates via command line
  python run.py --input candidates.xlsx --job job_description.txt
  
  # Preview data only
  python run.py --input candidates.xlsx --job job_description.txt --preview-only

📋 Input Requirements:

  Candidate File (Excel/CSV):
    - Must contain columns: 'Student Name', 'Skills', 'CV'
    - CV column should contain URLs to resumes (Google Docs, PDFs, etc.)
    - Skills column should list technical skills (comma-separated)
  
  Job Description:
    - Text file (.txt), Markdown (.md), or Word document (.docx)
    - Should include requirements, responsibilities, and qualifications

🔑 Environment Setup:

  Required:
    - OPENAI_API_KEY (for core AI functionality)
  
  Optional (for enhanced features):
    - GITHUB_API_TOKEN (repository analysis)
    - GOOGLE_API_KEY (web search)
    - LINKEDIN_API_KEY (profile analysis)
  
  See .env.example for complete configuration details.

💡 Pro Tips:

  1. Use the web interface for interactive analysis and real-time progress
  2. Use CLI mode for automation and batch processing
  3. Start with --preview-only to validate your data format
  4. Configure optional APIs for comprehensive candidate research
  5. Check the output/ directory for detailed reports and analysis

📊 What You'll Get:

  - ✅ Verified candidate identities and information
  - 📊 Detailed technical skill assessments  
  - 🔍 Comprehensive background research from multiple sources
  - 📈 Professional ranking and recommendations
  - 📋 Executive summary ready for decision makers
  - 💼 Interview strategies and next steps
  - ⚠️  Risk assessments and mitigation strategies
        """
    )
    
    # Add mutually exclusive group for UI vs CLI
    mode_group = parser.add_mutually_exclusive_group(required=True)
    
    mode_group.add_argument(
        '--ui', 
        action='store_true', 
        help='Launch the web interface (Streamlit UI) - Recommended for interactive use'
    )
    
    mode_group.add_argument(
        '--input', '-i', 
        help='Path to the input file (Excel/CSV) with candidate data - Required for CLI mode'
    )
    
    parser.add_argument(
        '--job', '-j', 
        help='Path to the job description file - Required for CLI mode'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging and detailed progress information'
    )
    
    parser.add_argument(
        '--preview-only',
        action='store_true',
        help='Only preview and validate input data without processing'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8501,
        help='Port for the web interface (default: 8501)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='AI-Powered HR Recruitment System v1.0.0'
    )
    
    args = parser.parse_args()
    
    # Environment check
    print("🔍 Checking environment...")
    
    # Check if .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("📝 Please copy .env.example to .env and configure your API keys")
        print("   Minimum required: OPENAI_API_KEY")
        print()
    
    # Check for required API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found in environment")
        print("🔑 Please set up your OpenAI API key:")
        print("   1. Copy .env.example to .env")
        print("   2. Add your OpenAI API key to the .env file")
        print("   3. Restart the application")
        print()
        print("💡 Get your API key from: https://platform.openai.com/api-keys")
        sys.exit(1)
    else:
        print("✅ OpenAI API key configured")
    
    # Check optional APIs
    optional_apis = {
        'GITHUB_API_TOKEN': 'GitHub repository analysis',
        'GOOGLE_API_KEY': 'Web search capabilities',
        'LINKEDIN_API_KEY': 'LinkedIn profile analysis'
    }
    
    configured_optional = 0
    for api_key, description in optional_apis.items():
        if os.getenv(api_key):
            print(f"✅ {api_key} configured - {description}")
            configured_optional += 1
        else:
            print(f"⚪ {api_key} not configured - {description} (optional)")
    
    print(f"📊 Total APIs configured: {1 + configured_optional}/{1 + len(optional_apis)}")
    
    if args.ui:
        # Launch the Streamlit UI
        print(f"\n🚀 Starting web interface on port {args.port}...")
        print(f"🌐 Open your browser to: http://localhost:{args.port}")
        print("📱 The interface is mobile-friendly and supports real-time progress tracking")
        print()
        print("💡 Tip: Keep this terminal open to see backend processing logs")
        print("⚠️  Press Ctrl+C to stop the server")
        print()
        
        # Import and run Streamlit
        try:
            import streamlit.web.cli as stcli
            import streamlit as st
            
            # Set up Streamlit configuration
            st_args = [
                "streamlit", "run", "ui/streamlit_app.py",
                "--server.port", str(args.port),
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false",
                "--theme.base", "light"
            ]
            
            sys.argv = st_args
            stcli.main()
            
        except ImportError:
            print("❌ Streamlit not installed. Please install it with:")
            print("   pip install streamlit")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n👋 Web interface stopped by user")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error starting web interface: {str(e)}")
            sys.exit(1)
    
    else:
        # CLI mode - validate required arguments
        if not args.job:
            print("❌ Error: --job argument is required for CLI mode")
            parser.print_help()
            sys.exit(1)
        
        print(f"\n💻 Running in CLI mode...")
        print(f"📁 Input file: {args.input}")
        print(f"📄 Job description: {args.job}")
        
        if args.preview_only:
            print("👀 Preview mode: Will validate data without processing")
        
        if args.verbose:
            print("🔍 Verbose mode: Detailed logging enabled")
        
        print()
        
        # Run the CLI version
        try:
            # Add CLI arguments to sys.argv for main.py
            cli_args = [
                "app/main.py",
                "--input", args.input,
                "--job", args.job
            ]
            
            if args.verbose:
                cli_args.append("--verbose")
            
            if args.preview_only:
                cli_args.append("--preview-only")
            
            # Store original argv
            original_argv = sys.argv
            sys.argv = cli_args
            
            # Import and run main
            from app.main import main as main_cli
            main_cli()
            
            # Restore original argv
            sys.argv = original_argv
            
        except ImportError as e:
            print(f"❌ Error importing CLI module: {str(e)}")
            print("🔧 Please ensure all dependencies are installed:")
            print("   pip install -r requirements.txt")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n⚠️  Process interrupted by user")
            sys.exit(0)
        except SystemExit as e:
            # Re-raise SystemExit to preserve exit codes from main.py
            raise e
        except Exception as e:
            print(f"❌ Unexpected error in CLI mode: {str(e)}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    main()