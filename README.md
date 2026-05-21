# HireFlux

An AI-powered HR recruitment system using a team of specialized agents to find the best candidates for your job openings.

## Features

- **Orchestrator Agent**: Central coordinator managing the workflow and communication
- **Resume Analysis Agent**: Processes resumes and extracts key information
- **Matching Agent**: Evaluates candidates against job requirements
- **Research Agent**: Gathers supplementary information from external sources
- **Validation Agent**: Ensures accurate candidate identification and information verification
- **Summarization Agent**: Creates comprehensive candidate profiles

## System Requirements

- Python 3.9+
- Google Gemini API key

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd HireFlux
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your API keys:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   
   # Optional API keys for enhanced functionality
   GITHUB_API_TOKEN=your_github_token_here
   GOOGLE_API_KEY=your_google_api_key_here
   GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
   LINKEDIN_API_KEY=your_linkedin_api_key_here
   LINKEDIN_API_SECRET=your_linkedin_api_secret_here
   KAGGLE_USERNAME=your_kaggle_username_here
   KAGGLE_KEY=your_kaggle_key_here
   ```

4. Get your Gemini API key from: https://makersuite.google.com/app/apikey

## Usage

### Command Line Interface

Run the recruitment process using the command line:

```bash
python app/main.py --input /path/to/candidates.xlsx --job /path/to/job_description.txt
```

### Web Interface

Launch the Streamlit web interface:

```bash
streamlit run ui/streamlit_app.py
```

Then, follow the instructions in the web interface:
1. Enter your API keys 
2. Upload a spreadsheet with candidate information
3. Enter or upload a job description
4. Click "Start Candidate Processing"

## Input Format

The system expects a spreadsheet (Excel or CSV) with the following columns:
- `Student Name`: The name of the candidate
- `Skills`: A list of the candidate's skills
- `CV`: URL to the candidate's resume (e.g., Google Docs link)

## API Requirements

The system can use several APIs to enhance the research capabilities:

1. **Google Gemini API** (required): For AI agent functionality
2. **GitHub API** (optional): For researching candidates' code repositories
3. **Google Custom Search API** (optional): For general web research
4. **LinkedIn API** (optional): For professional profile research
5. **Kaggle API** (optional): For data science project research

## Agent Workflow

1. **Resume Analysis**: Extract structured information from resumes
2. **Candidate Matching**: Compare candidates to job requirements
3. **Deep Research**: Find additional information about top candidates
4. **Validation**: Verify that the information is accurate and belongs to the right person
5. **Summarization**: Create detailed profiles and rank candidates

## Limitations

- **LinkedIn API**: LinkedIn's API has strict limitations and requires partner program enrollment
- **Resume Parsing**: The system works best with accessible document formats (Google Docs, plain text)
- **Research Depth**: The quality of research depends on the candidate's online presence

## License

[License information here]
