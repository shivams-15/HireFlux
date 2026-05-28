from crewai import Agent, Task
import logging
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import json
import os
import time
from utils.gemini_llm import GeminiClient, get_crewai_llm, map_model_name
from utils.web_search import WebSearchManager

logger = logging.getLogger(__name__)

class ResearchAgent:
    def __init__(self, model="gemini-3.0-pro"):
        """
        Initialize Research Agent
        
        Args:
            model: Gemini model for research analysis (default: gemini-3.0-pro)
                  Uses Gemini 3.0+ for intelligent web research and analysis
        """
        self.model_name = map_model_name(model)
        self.llm_client = GeminiClient(model=self.model_name)
        
        # Unified web search (free, no API keys needed)
        self.web_search = WebSearchManager()
        
        # Rate limiting
        self.last_request_time = {}
        self.request_delay = 1.5  # seconds between requests
        
        self.agent = Agent(
            role="Deep Research Agent",
            goal="Conduct comprehensive online research using free web search to gather detailed information about top candidates",
            backstory="""You are an expert digital investigator specializing in candidate research. 
            You excel at finding relevant professional information from various online sources using 
            intelligent web search. You understand how to verify information accuracy, cross-reference 
            sources, and compile comprehensive candidate profiles while respecting privacy and 
            ethical boundaries. You use advanced AI to analyze web content and extract meaningful 
            insights about candidates' professional presence and capabilities.""",
            verbose=True,
            llm=get_crewai_llm(model=self.model_name),
            allow_delegation=False
        )
    
    def create_tasks(self, top_candidates: List[Dict]) -> List[Task]:
        """Create research tasks for top candidates"""
        
        comprehensive_research_task = Task(
            description=f"""Conduct comprehensive web research on {len(top_candidates)} top candidates 
using free web search tools.

CANDIDATES TO RESEARCH:
{json.dumps([{
    'name': c.get('candidate', {}).get('personal_info', {}).get('name', ''),
    'email': c.get('candidate', {}).get('contact_info', {}).get('emails', []),
    'links': c.get('candidate', {}).get('links', {}),
    'skills': c.get('candidate', {}).get('skills', {}).get('technical', [])[:5],
    'score': c.get('overall_score', 0)
} for c in top_candidates], indent=2)}

For each candidate, use intelligent web search to find:

1. **Professional Profiles**:
   - GitHub: repositories, code quality, contributions, activity
   - LinkedIn: professional history, skills, endorsements
   - Stack Overflow: technical expertise and community help
   - Professional portfolios and personal websites

2. **Technical Presence**:
   - Code repositories and projects
   - Technical blog posts and articles
   - Open source contributions
   - Coding platform profiles (LeetCode, HackerRank, Kaggle, etc.)

3. **Community & Thought Leadership**:
   - Technical articles and publications
   - Conference talks or presentations
   - Social media technical discussions
   - Academic publications or research

4. **Verification & Insights**:
   - Cross-reference claimed skills with actual projects
   - Assess activity level and recent engagement
   - Identify specializations and unique strengths
   - Note any red flags or inconsistencies

RESEARCH METHODOLOGY:
- Use web search to find candidate's professional presence
- Visit and analyze found profiles and pages
- Use AI to extract meaningful insights from web content
- Cross-reference information for accuracy
- Compile comprehensive profiles with verified information

IMPORTANT: 
- Only gather publicly available information
- Use free web search (no API keys required)
- Focus on quality over quantity of sources
- Respect privacy and ethical boundaries""",
            expected_output="""Comprehensive research profiles for each candidate including:
- Professional presence across web platforms
- Technical skills validation through actual work
- Community involvement and contributions
- Recent activity and current projects  
- Unique strengths and specializations
- Professional network and influence
- Learning trajectory and growth evidence
- Verified information with sources
- AI-powered analysis and insights
- Overall digital presence assessment""",
            agent=self.agent
        )
        
        return [comprehensive_research_task]
    
    async def research_candidates(self, top_candidates: List[Dict]) -> List[Dict]:
        """Research all top candidates using unified web search"""
        researched_candidates = []
        
        for i, candidate_data in enumerate(top_candidates):
            candidate = candidate_data.get('candidate', {})
            name = candidate.get('personal_info', {}).get('name', f'Candidate {i+1}')
            
            logger.info(f"Researching candidate {i+1}/{len(top_candidates)}: {name}")
            
            try:
                research_result = await self._comprehensive_candidate_research(candidate)
                
                researched_candidate = {
                    'original_candidate_data': candidate_data,
                    'research_results': research_result,
                    'research_successful': True,
                    'research_timestamp': time.time()
                }
                
                researched_candidates.append(researched_candidate)
                
                # Rate limiting
                await asyncio.sleep(self.request_delay)
                
            except Exception as e:
                logger.error(f"Error researching candidate {name}: {str(e)}")
                researched_candidates.append({
                    'original_candidate_data': candidate_data,
                    'research_results': {'error': str(e)},
                    'research_successful': False,
                    'research_timestamp': time.time()
                })
        
        return researched_candidates
    
    async def _comprehensive_candidate_research(self, candidate: Dict) -> Dict:
        """Conduct comprehensive research on a single candidate using unified web search"""
        research_results = {
            'web_search_results': {},
            'github_findings': [],
            'linkedin_findings': [],
            'portfolio_findings': [],
            'technical_content': [],
            'community_presence': [],
            'verified_skills': [],
            'ai_analysis': {}
        }
        
        # Extract basic info
        name = candidate.get('personal_info', {}).get('name', '')
        emails = candidate.get('contact_info', {}).get('emails', [])
        links = candidate.get('links', {})
        skills = candidate.get('skills', {}).get('technical', [])
        
        # 1. Unified Web Search
        logger.info(f"Performing web search for: {name}")
        email = emails[0] if emails else None
        search_results = await self.web_search.search_candidate(name, skills, email)
        research_results['web_search_results'] = search_results
        
        # 2. Analyze GitHub results
        if search_results.get('github'):
            github_findings = await self._analyze_github_findings(
                search_results['github'], name
            )
            research_results['github_findings'] = github_findings
        
        # 3. Analyze LinkedIn results  
        if search_results.get('linkedin'):
            linkedin_findings = await self._analyze_linkedin_findings(
                search_results['linkedin'], name
            )
            research_results['linkedin_findings'] = linkedin_findings
        
        # 4. Analyze Portfolio and other professional sites
        portfolio_results = search_results.get('portfolio', []) + search_results.get('other', [])
        if portfolio_results:
            portfolio_findings = await self._analyze_portfolio_findings(
                portfolio_results[:5], name
            )
            research_results['portfolio_findings'] = portfolio_findings
        
        # 5. Analyze Stack Overflow presence
        if search_results.get('stackoverflow'):
            so_findings = await self._analyze_stackoverflow_findings(
                search_results['stackoverflow'], name
            )
            research_results['community_presence'].extend(so_findings)
        
        # 6. Extract technical content
        all_results = []
        for category in ['github', 'portfolio', 'other']:
            all_results.extend(search_results.get(category, []))
        
        if all_results:
            technical_content = await self._extract_technical_content(all_results[:10])
            research_results['technical_content'] = technical_content
        
        # 7. AI-powered comprehensive analysis
        logger.info(f"Performing AI analysis for: {name}")
        ai_analysis = await self._llm_enhance_research(research_results, candidate)
        research_results['ai_analysis'] = ai_analysis
        
        return research_results
    
    async def _analyze_github_findings(self, github_results: List[Dict], name: str) -> List[Dict]:
        """Analyze GitHub search results"""
        findings = []
        
        for result in github_results[:5]:  # Top 5 GitHub results
            try:
                url = result.get('url', '')
                if 'github.com' in url:
                    # Extract info from URL
                    parts = url.split('github.com/')
                    if len(parts) > 1:
                        path = parts[1].strip('/')
                        
                        finding = {
                            'url': url,
                            'title': result.get('title', ''),
                            'snippet': result.get('snippet', ''),
                            'type': 'profile' if not '/' in path or path.count('/') == 0 else 'repository',
                            'relevance': 'high' if name.lower() in url.lower() else 'medium'
                        }
                        findings.append(finding)
            except Exception as e:
                logger.warning(f"Error analyzing GitHub result: {e}")
        
        return findings
    
    async def _analyze_linkedin_findings(self, linkedin_results: List[Dict], name: str) -> List[Dict]:
        """Analyze LinkedIn search results"""
        findings = []
        
        for result in linkedin_results[:3]:  # Top 3 LinkedIn results
            finding = {
                'url': result.get('url', ''),
                'title': result.get('title', ''),
                'snippet': result.get('snippet', ''),
                'relevance': 'high' if name.lower() in result.get('title', '').lower() else 'medium'
            }
            findings.append(finding)
        
        return findings
    
    async def _analyze_portfolio_findings(self, portfolio_results: List[Dict], name: str) -> List[Dict]:
        """Analyze portfolio and personal website findings"""
        findings = []
        
        for result in portfolio_results:
            # Try to fetch page content
            content = await self.web_search.fetch_page_content(result.get('url', ''))
            
            finding = {
                'url': result.get('url', ''),
                'title': result.get('title', ''),
                'snippet': result.get('snippet', ''),
                'content_preview': content[:500] if content else '',
                'has_portfolio': 'portfolio' in result.get('url', '').lower() or 
                                'portfolio' in result.get('title', '').lower()
            }
            findings.append(finding)
        
        return findings
    
    async def _analyze_stackoverflow_findings(self, so_results: List[Dict], name: str) -> List[Dict]:
        """Analyze Stack Overflow presence"""
        findings = []
        
        for result in so_results[:3]:
            finding = {
                'platform': 'Stack Overflow',
                'url': result.get('url', ''),
                'title': result.get('title', ''),
                'snippet': result.get('snippet', ''),
                'type': 'profile' if '/users/' in result.get('url', '') else 'question/answer'
            }
            findings.append(finding)
        
        return findings
    
    async def _extract_technical_content(self, results: List[Dict]) -> List[Dict]:
        """Extract technical content from search results"""
        technical_content = []
        
        for result in results:
            url = result.get('url', '').lower()
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '')
            
            # Identify technical content
            technical_indicators = [
                'blog', 'article', 'tutorial', 'guide', 'documentation',
                'medium.com', 'dev.to', 'hashnode', 'substack'
            ]
            
            is_technical = any(indicator in url or indicator in title for indicator in technical_indicators)
            
            if is_technical:
                content = {
                    'url': result.get('url', ''),
                    'title': result.get('title', ''),
                    'snippet': snippet,
                    'content_type': 'blog/article',
                    'platform': self._identify_platform(url)
                }
                technical_content.append(content)
        
        return technical_content
    
    def _identify_platform(self, url: str) -> str:
        """Identify platform from URL"""
        url_lower = url.lower()
        
        if 'medium.com' in url_lower:
            return 'Medium'
        elif 'dev.to' in url_lower:
            return 'Dev.to'
        elif 'hashnode' in url_lower:
            return 'Hashnode'
        elif 'substack' in url_lower:
            return 'Substack'
        elif 'github.com' in url_lower:
            return 'GitHub'
        elif 'stackoverflow.com' in url_lower:
            return 'Stack Overflow'
        elif 'linkedin.com' in url_lower:
            return 'LinkedIn'
        else:
            return 'Personal Site'
    
    async def _llm_enhance_research(self, research_results: Dict, candidate: Dict) -> Dict:
        """Use Gemini LLM to analyze and enhance research results"""
        if not self.llm_client:
            return {'note': 'LLM analysis not available'}
        
        try:
            # Prepare research summary for LLM analysis
            candidate_name = candidate.get('personal_info', {}).get('name', '')
            resume_skills = candidate.get('skills', {}).get('technical', [])
            
            prompt = f"""Analyze the web research results for this candidate and provide insights:

CANDIDATE: {candidate_name}
RESUME SKILLS: {', '.join(resume_skills[:10])}

RESEARCH FINDINGS:
{json.dumps(research_results, indent=2)[:4000]}

Provide a comprehensive analysis covering:
1. Technical expertise validation - do online activities match resume skills?
2. Professional activity level - recent contributions, active development
3. Community involvement and thought leadership
4. Unique strengths discovered through research
5. Areas of specialization not evident from resume
6. Overall professional digital presence assessment
7. Red flags or inconsistencies (if any)
8. Growth trajectory and learning evidence

Provide a concise but insightful analysis."""
            
            analysis = self.llm_client.generate_content(prompt)
            
            return {
                'llm_analysis': analysis,
                'research_quality_score': self._calculate_research_quality_score(research_results),
                'key_findings': self._extract_key_findings(research_results)
            }
            
        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
            return {'llm_analysis_error': str(e)}
    
    def _calculate_research_quality_score(self, research_results: Dict) -> float:
        """Calculate quality score of research findings"""
        score = 0
        max_score = 100
        
        # GitHub presence (30 points)
        github_findings = research_results.get('github_findings', [])
        if github_findings:
            score += min(len(github_findings) * 6, 30)
        
        # LinkedIn presence (15 points)
        linkedin_findings = research_results.get('linkedin_findings', [])
        if linkedin_findings:
            score += 15
        
        # Portfolio sites (25 points)
        portfolio_findings = research_results.get('portfolio_findings', [])
        if portfolio_findings:
            score += min(len(portfolio_findings) * 8, 25)
        
        # Technical content (20 points)
        technical_content = research_results.get('technical_content', [])
        if technical_content:
            score += min(len(technical_content) * 5, 20)
        
        # Community presence (10 points)
        community_presence = research_results.get('community_presence', [])
        if community_presence:
            score += 10
        
        return min(score, max_score)
    
    def _extract_key_findings(self, research_results: Dict) -> List[str]:
        """Extract key findings from research"""
        findings = []
        
        # GitHub findings
        github_findings = research_results.get('github_findings', [])
        if github_findings:
            findings.append(f"Found {len(github_findings)} GitHub references")
        
        # LinkedIn findings
        linkedin_findings = research_results.get('linkedin_findings', [])
        if linkedin_findings:
            findings.append(f"Found LinkedIn profile")
        
        # Portfolio findings
        portfolio_findings = research_results.get('portfolio_findings', [])
        if portfolio_findings:
            findings.append(f"Found {len(portfolio_findings)} portfolio/personal sites")
        
        # Technical content
        technical_content = research_results.get('technical_content', [])
        if technical_content:
            platforms = set(content.get('platform', '') for content in technical_content)
            findings.append(f"Technical content on: {', '.join(platforms)}")
        
        # Community presence
        community_presence = research_results.get('community_presence', [])
        if community_presence:
            findings.append(f"Active on Stack Overflow")
        
        return findings[:8]  # Limit to top 8 findings
