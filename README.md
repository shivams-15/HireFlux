# HireFlux

An AI-powered HR recruitment system using a team of specialized agents to analyze resumes, research candidates, and provide comprehensive hiring recommendations—**completely free** with only a Gemini API key required.

## ✨ Key Features

- 🤖 **Multi-Agent AI System**: Specialized agents working together for comprehensive candidate evaluation
- 📄 **Intelligent Resume Parsing**: Gemini-powered extraction of structured data from PDF resumes
- 🔍 **Free Web Research**: Automatic candidate research across GitHub, LinkedIn, portfolios, and more—no API keys needed
- ✅ **Cross-Platform Verification**: Validates candidate information across multiple sources
- 📊 **Comprehensive Reporting**: Detailed profiles with verified sources, skills assessment, and match scores
- 🌐 **Modern Web Interface**: Next.js frontend with real-time progress tracking
- 🚀 **FastAPI Backend**: High-performance asynchronous processing

## 🎯 Agent Team

1. **Resume Analysis Agent** - Extracts structured information from resumes using Gemini 3.1 Flash Lite
2. **Matching Agent** - Evaluates candidates against job requirements with detailed scoring
3. **Research Agent** - Gathers information from GitHub, LinkedIn, portfolios, StackOverflow via free DuckDuckGo search
4. **Validation Agent** - Cross-references information for accuracy and consistency
5. **Summarization Agent** - Creates comprehensive candidate profiles with source attribution

## 💰 Cost-Effective Design

**Only 1 API Key Needed**: Google Gemini API (free tier available)

- ✅ Free DuckDuckGo web search (no API key)
- ✅ Free PDF parsing with Gemini Flash Lite (budget-friendly)
- ✅ No GitHub API, LinkedIn API, or Google Custom Search required
- ✅ Generous free tier: Gemini Flash models are very cost-effective

## 🛠️ System Requirements

- Python 3.9+ (Python 3.13+ recommended)
- Node.js 18+ (for frontend)
- Google Gemini API key (get free at https://makersuite.google.com/app/apikey)

## 📦 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd HireFlux
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

### 4. Environment Configuration

Create a `.env` file in the `backend` directory:

```env
# Required: Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Deprecated API keys (no longer required)
# GITHUB_API_TOKEN=...
# GOOGLE_API_KEY=...
# LINKEDIN_API_KEY=...
```

**Get Your Free Gemini API Key**: https://makersuite.google.com/app/apikey

## 🚀 Usage

### Option 1: Modern Web Interface (Recommended)

1. **Start the Backend** (in project root):
   ```bash
   cd backend
   python main.py
   ```
   Backend will run on http://localhost:8000

2. **Start the Frontend** (in new terminal):
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend will run on http://localhost:3000

3. **Access the Application**:
   - Open http://localhost:3000 in your browser
   - Upload a PDF resume or Excel spreadsheet with candidates
   - Paste or upload your job description
   - Click "Start Processing" and watch real-time progress
   - View comprehensive candidate reports with verified sources

### Option 2: Streamlit Interface (Alternative)

```bash
streamlit run ui/streamlit_app.py
```

### Option 3: Command Line Interface

```bash
python app/main.py --input /path/to/candidates.xlsx --job /path/to/job_description.txt
```

## 📋 Input Formats

### Resume PDF
- Upload a single PDF resume for analysis
- Gemini automatically extracts name, contact info, skills, experience, education, and projects

### Candidate Spreadsheet (Excel/CSV)
Required columns:
- `Student Name` or `name`: Candidate's full name
- `CV URL` or `cv_url`: URL to resume (Google Docs, PDF link)
- `Email` (optional): Contact email

## 🔬 AI Models Used

- **Gemini 3.1 Flash Lite**: Document parsing, resume extraction (ultra-fast, budget-friendly)
- **Gemini 3.0 Pro**: Web research analysis, candidate insights (balanced performance)

Both models are highly cost-effective with generous free tiers!

## 📊 What You Get

### Comprehensive Candidate Reports Include:

1. **Executive Summary**
   - Overall assessment and recommendation
   - Years of experience and specialization
   - Match score with confidence level

2. **Verified Sources**
   - All platforms found during research (GitHub, LinkedIn, etc.)
   - Profile URLs and verification status
   - Metrics from each platform (repos, stars, connections)

3. **Technical Skills Assessment**
   - High-confidence skills (verified on multiple platforms)
   - Medium-confidence skills (verified on single platform)
   - Claimed skills (resume only)
   - Discovered skills (found during research)

4. **Experience Summary**
   - Each position with verification status
   - LinkedIn cross-reference badges
   - Technologies used and achievements

5. **Professional Presence**
   - GitHub activity and repository metrics
   - LinkedIn profile completeness
   - StackOverflow reputation
   - Overall presence score (0-100%)

6. **Projects Portfolio**
   - From resume, GitHub, and portfolios
   - Verification badges
   - Stars, forks, and engagement metrics

7. **Publications & Thought Leadership**
   - Articles and blog posts
   - Talks and presentations
   - Online mentions

8. **Data Completeness Metrics**
   - Resume data completeness %
   - Research data completeness %
   - Overall verification score

## 🔄 Processing Workflow

1. **Resume Analysis** → Extract structured data with Gemini AI
2. **Candidate Matching** → Score candidates against job requirements
3. **Web Research** → Search GitHub, LinkedIn, portfolios via DuckDuckGo
4. **Information Validation** → Cross-verify data across sources
5. **Comprehensive Report** → Generate detailed profiles with source attribution

## 🌐 Free Web Search Technology

The system uses **DuckDuckGo** for free web research:
- ✅ No API keys required
- ✅ No rate limits (with respectful delays)
- ✅ Searches GitHub, LinkedIn, StackOverflow, portfolios
- ✅ Automatic retry logic for reliability
- ✅ Fallback mechanisms for robustness

## 📁 Project Structure

```
HireFlux/
├── backend/           # FastAPI backend
│   ├── main.py       # API server
│   └── reports/      # Generated reports
├── frontend/         # Next.js frontend
│   ├── app/          # Next.js app router
│   ├── components/   # React components
│   └── lib/          # API client
├── agents/           # AI agent implementations
│   ├── resume_analysis_agent.py
│   ├── matching_agent.py
│   ├── research_agent.py
│   ├── validation_agent.py
│   └── summarization_agent.py
├── utils/            # Utility modules
│   ├── gemini_llm.py       # Gemini model management
│   ├── document_parser.py  # PDF/Excel parsing
│   └── web_search.py       # Free DuckDuckGo search
├── app/              # CLI application
└── ui/               # Streamlit interface (alternative)
```

## ⚙️ Configuration

### Model Selection

Edit `agents/*.py` to change AI models:
- **Fast & Cheap**: `gemini-3.1-flash-lite` (document parsing)
- **Balanced**: `gemini-3.0-pro` (research, analysis)
- **Advanced**: `gemini-2.5-pro` (complex reasoning)

### Search Settings

Edit `utils/web_search.py`:
- `request_delay`: Time between searches (default: 3.0s)
- `max_results`: Results per query (default: 10)

## 🚨 Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend won't start
```bash
cd frontend
npm install
npm run dev
```

### DuckDuckGo search issues
- Status 202: Normal - system auto-retries with exponential backoff
- Install reliable library: `pip install duckduckgo-search`
- Increase delay in `web_search.py` if needed

### Gemini API errors
- Verify API key in `backend/.env`
- Check quota: https://console.cloud.google.com/
- Free tier limits: 60 requests/minute

## 🎓 Best Practices

1. **Resume Quality**: Use well-formatted PDFs for best extraction
2. **Job Descriptions**: Be specific about required skills and experience
3. **Rate Limiting**: System respects API limits automatically
4. **Data Privacy**: All processing happens locally; only API calls to Gemini

## 📈 Performance

- **Resume Analysis**: ~5-10 seconds per resume
- **Web Research**: ~30-60 seconds per candidate (varies by online presence)
- **Total Processing**: ~2-3 minutes per candidate end-to-end

## 🔒 Privacy & Security

- No data stored on external servers (except Gemini API calls)
- Candidate information processed locally
- Reports saved locally in `backend/reports/`
- Environment variables keep API keys secure

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- Additional research platforms
- Alternative AI models (OpenAI, Anthropic)
- Advanced matching algorithms
- UI/UX improvements

## 📄 License

[License information here]

## 🙏 Acknowledgments

- Google Gemini for powerful AI capabilities
- DuckDuckGo for free web search
- CrewAI for multi-agent orchestration
- Next.js and FastAPI communities
