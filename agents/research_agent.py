from crewai import Agent, Task
import logging
import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import json
import os
import re
from urllib.parse import urljoin, urlparse
import time
from utils.gemini_llm import GeminiClient, get_crewai_llm, map_model_name

logger = logging.getLogger(__name__)

class ResearchAgent:
    def __init__(self, model="gemini-3.5-flash"):
        self.model_name = map_model_name(model)
        self.llm_client = GeminiClient(model=self.model_name)
        
        # API tokens (optional)
        self.github_token = os.getenv('GITHUB_API_TOKEN')
        self.linkedin_token = os.getenv('LINKEDIN_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.google_cse_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        
        # Rate limiting
        self.last_request_time = {}
        self.request_delay = 1  # seconds between requests
        
        self.agent = Agent(
            role="Deep Research Agent",
            goal="Conduct comprehensive online research to gather detailed information about top candidates",
            backstory="""You are an expert digital investigator specializing in candidate research. 
            You excel at finding relevant professional information from various online sources including 
            LinkedIn, GitHub, personal websites, publications, social media, coding platforms, 
            and professional networks. You understand how to verify information accuracy and 
            compile comprehensive candidate profiles while respecting privacy and ethical boundaries.""",
            verbose=True,
            llm=get_crewai_llm(model=self.model_name),
            allow_delegation=False
        )
    
    def create_tasks(self, top_candidates: List[Dict]) -> List[Task]:
        """Create research tasks for top candidates"""
        
        comprehensive_research_task = Task(
            description=f"""Conduct comprehensive research on {len(top_candidates)} top candidates.

CANDIDATES TO RESEARCH:
{json.dumps([{
    'name': c.get('candidate', {}).get('personal_info', {}).get('name', ''),
    'email': c.get('candidate', {}).get('contact_info', {}).get('emails', []),
    'links': c.get('candidate', {}).get('links', {}),
    'skills': c.get('candidate', {}).get('skills', {}).get('technical', [])[:5],
    'score': c.get('overall_score', 0)
} for c in top_candidates], indent=2)}

For each candidate, research and gather information from:

1. **Professional Platforms**:
   - LinkedIn: Employment history, skills, recommendations, education, certifications
   - GitHub: Repositories, contributions, code quality, activity level, collaboration
   - GitLab, Bitbucket: Alternative code repositories
   - Stack Overflow: Technical expertise, community involvement
   - AngelList: Startup experience and interests

2. **Portfolio and Personal Sites**:
   - Personal websites/portfolios: Projects, blog posts, technical writing
   - Medium, Dev.to: Technical articles and thought leadership
   - Personal blogs: Insights into expertise and communication skills

3. **Professional Networks**:
   - ResearchGate: Academic publications and research
   - ORCID: Research contributions and citations
   - Professional associations and memberships

4. **Coding Platforms**:
   - LeetCode: Problem-solving skills and algorithm knowledge
   - HackerRank: Programming challenges and certifications
   - Codepen: Frontend development skills
   - Kaggle: Data science competitions and datasets

5. **Social and Community**:
   - Twitter: Professional opinions, industry engagement
   - YouTube: Technical presentations or tutorials
   - Conference speaking: Technical talks and presentations
   - Open source contributions: Community involvement

6. **Educational and Certification**:
   - Coursera, edX, Udacity: Online learning and certifications
   - University pages: Academic achievements
   - Professional certifications: Verify credentials

7. **Patents and Publications**:
   - Google Scholar: Academic papers and citations
   - Patent databases: Innovation and intellectual property
   - Technical publications: Industry contributions

RESEARCH METHODOLOGY:
- Start with provided links and expand search systematically
- Use multiple search strategies and sources
- Cross-reference information for accuracy
- Look for recent activity and current engagement
- Identify unique strengths and specialized expertise
- Note any red flags or inconsistencies

IMPORTANT: Only gather publicly available information. Do not attempt to access private or restricted content.""",
            expected_output="""Comprehensive research profiles for each candidate including:
- Professional background verification and expansion
- Technical skills validation through actual work/projects
- Community involvement and thought leadership
- Recent activity and current projects
- Unique strengths and specializations
- Areas of expertise beyond resume
- Professional network and influence
- Learning and growth trajectory
- Any additional relevant information found
- Source verification and credibility assessment""",
            agent=self.agent
        )
        
        return [comprehensive_research_task]
    
    async def research_candidates(self, top_candidates: List[Dict]) -> List[Dict]:
        """Research all top candidates comprehensively"""
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
        """Conduct comprehensive research on a single candidate"""
        research_results = {
            'linkedin': {},
            'github': {},
            'portfolio_sites': [],
            'professional_platforms': {},
            'coding_platforms': {},
            'social_presence': {},
            'publications': [],
            'certifications': [],
            'projects': [],
            'community_involvement': [],
            'recent_activity': [],
            'additional_findings': []
        }
        
        # Extract basic info
        name = candidate.get('personal_info', {}).get('name', '')
        emails = candidate.get('contact_info', {}).get('emails', [])
        links = candidate.get('links', {})
        skills = candidate.get('skills', {}).get('technical', [])
        
        # 1. LinkedIn Research
        if links.get('linkedin'):
            research_results['linkedin'] = await self._research_linkedin(links['linkedin'], name)
        
        # 2. GitHub Research
        if links.get('github'):
            research_results['github'] = await self._research_github(links['github'], name)
        
        # 3. Portfolio and Personal Sites
        portfolio_urls = [links.get('portfolio')] + links.get('other', [])
        for url in portfolio_urls:
            if url:
                portfolio_info = await self._research_portfolio_site(url)
                if portfolio_info:
                    research_results['portfolio_sites'].append(portfolio_info)
        
        # 4. Search-based Research
        search_results = await self._search_based_research(name, emails, skills)
        research_results.update(search_results)
        
        # 5. Platform-specific Research
        platform_results = await self._research_coding_platforms(name, emails)
        research_results['coding_platforms'].update(platform_results)
        
        # 6. Publication and Academic Research
        publication_results = await self._research_publications(name)
        research_results['publications'] = publication_results
        
        # 7. Social and Community Research
        social_results = await self._research_social_presence(name, skills)
        research_results['social_presence'] = social_results
        
        # 8. LLM-powered Analysis
        enhanced_analysis = await self._llm_enhance_research(research_results, candidate)
        research_results['ai_analysis'] = enhanced_analysis
        
        return research_results
    
    async def _research_linkedin(self, linkedin_url: str, name: str) -> Dict:
        """Research LinkedIn profile"""
        try:
            # Note: LinkedIn scraping is limited due to their anti-scraping measures
            # This is a basic implementation - in production, you'd use LinkedIn API
            
            linkedin_info = {
                'url': linkedin_url,
                'accessible': False,
                'profile_info': {},
                'note': 'LinkedIn scraping limited due to platform restrictions'
            }
            
            # Try basic profile access
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(linkedin_url, timeout=10) as response:
                        if response.status == 200:
                            linkedin_info['accessible'] = True
                            # Basic info extraction would go here
                            # Due to LinkedIn's restrictions, we can only get limited public info
                            linkedin_info['profile_info'] = {
                                'status': 'Profile found and accessible',
                                'recommendation': 'Manual review recommended for detailed information'
                            }
                except:
                    linkedin_info['note'] = 'Profile not publicly accessible'
            
            return linkedin_info
            
        except Exception as e:
            return {'error': str(e), 'url': linkedin_url}
    
    async def _research_github(self, github_url: str, name: str) -> Dict:
        """Research GitHub profile comprehensively"""
        try:
            username = github_url.split('github.com/')[-1].strip('/')
            
            github_info = {
                'username': username,
                'url': github_url,
                'profile': {},
                'repositories': [],
                'activity': {},
                'contributions': {},
                'languages': {},
                'notable_projects': []
            }
            
            # GitHub API research
            if self.github_token:
                github_info.update(await self._github_api_research(username))
            else:
                github_info.update(await self._github_scraping_research(github_url))
            
            return github_info
            
        except Exception as e:
            return {'error': str(e), 'url': github_url}
    
    async def _github_api_research(self, username: str) -> Dict:
        """Research using GitHub API"""
        try:
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            results = {
                'api_used': True,
                'profile': {},
                'repositories': [],
                'activity': {}
            }
            
            async with aiohttp.ClientSession() as session:
                # Get user profile
                async with session.get(f'https://api.github.com/users/{username}', headers=headers) as response:
                    if response.status == 200:
                        profile_data = await response.json()
                        results['profile'] = {
                            'name': profile_data.get('name'),
                            'bio': profile_data.get('bio'),
                            'location': profile_data.get('location'),
                            'public_repos': profile_data.get('public_repos'),
                            'followers': profile_data.get('followers'),
                            'following': profile_data.get('following'),
                            'created_at': profile_data.get('created_at'),
                            'updated_at': profile_data.get('updated_at')
                        }
                
                # Get repositories
                async with session.get(f'https://api.github.com/users/{username}/repos?sort=updated&per_page=50', headers=headers) as response:
                    if response.status == 200:
                        repos_data = await response.json()
                        
                        for repo in repos_data[:10]:  # Top 10 repos
                            repo_info = {
                                'name': repo.get('name'),
                                'description': repo.get('description'),
                                'language': repo.get('language'),
                                'stars': repo.get('stargazers_count'),
                                'forks': repo.get('forks_count'),
                                'updated_at': repo.get('updated_at'),
                                'size': repo.get('size'),
                                'topics': repo.get('topics', []),
                                'url': repo.get('html_url')
                            }
                            results['repositories'].append(repo_info)
                
                # Get recent activity
                async with session.get(f'https://api.github.com/users/{username}/events/public?per_page=30', headers=headers) as response:
                    if response.status == 200:
                        events_data = await response.json()
                        
                        recent_activity = []
                        for event in events_data[:10]:
                            activity = {
                                'type': event.get('type'),
                                'repo': event.get('repo', {}).get('name'),
                                'created_at': event.get('created_at')
                            }
                            recent_activity.append(activity)
                        
                        results['activity'] = {
                            'recent_events': recent_activity,
                            'total_events_checked': len(events_data)
                        }
            
            return results
            
        except Exception as e:
            logger.error(f"GitHub API research failed: {e}")
            return {'api_error': str(e)}
    
    async def _github_scraping_research(self, github_url: str) -> Dict:
        """Fallback GitHub scraping when API not available"""
        try:
            results = {
                'api_used': False,
                'profile': {},
                'repositories': [],
                'scraping_used': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(github_url, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract basic profile info
                        profile_info = {}
                        
                        # Name
                        name_elem = soup.find('span', {'class': 'p-name'})
                        if name_elem:
                            profile_info['name'] = name_elem.get_text().strip()
                        
                        # Bio
                        bio_elem = soup.find('div', {'class': 'p-note'})
                        if bio_elem:
                            profile_info['bio'] = bio_elem.get_text().strip()
                        
                        # Stats
                        stats = soup.find_all('span', {'class': 'text-bold'})
                        if len(stats) >= 3:
                            profile_info['repos'] = stats[0].get_text().strip()
                            profile_info['followers'] = stats[1].get_text().strip()
                            profile_info['following'] = stats[2].get_text().strip()
                        
                        results['profile'] = profile_info
                        
                        # Extract repository info
                        repo_elements = soup.find_all('div', {'class': 'wb-break-all'})
                        for repo_elem in repo_elements[:10]:
                            repo_link = repo_elem.find('a')
                            if repo_link:
                                repo_name = repo_link.get_text().strip()
                                repo_url = urljoin(github_url, repo_link.get('href', ''))
                                
                                # Get additional repo info
                                repo_info = await self._scrape_repository_details(repo_url)
                                repo_info['name'] = repo_name
                                repo_info['url'] = repo_url
                                
                                results['repositories'].append(repo_info)
            
            return results
            
        except Exception as e:
            return {'scraping_error': str(e)}
    
    async def _scrape_repository_details(self, repo_url: str) -> Dict:
        """Scrape individual repository details"""
        try:
            repo_info = {}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(repo_url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Description
                        desc_elem = soup.find('p', {'class': 'f4'})
                        if desc_elem:
                            repo_info['description'] = desc_elem.get_text().strip()
                        
                        # Language
                        lang_elem = soup.find('span', {'class': 'ml-0'})
                        if lang_elem:
                            repo_info['language'] = lang_elem.get_text().strip()
                        
                        # Stars and forks
                        social_count = soup.find_all('span', {'class': 'text-small'})
                        for elem in social_count:
                            text = elem.get_text().strip()
                            if 'star' in text.lower():
                                repo_info['stars'] = text
                            elif 'fork' in text.lower():
                                repo_info['forks'] = text
                        
                        # Topics
                        topic_elements = soup.find_all('a', {'class': 'topic-tag'})
                        topics = [elem.get_text().strip() for elem in topic_elements]
                        repo_info['topics'] = topics
            
            return repo_info
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _research_portfolio_site(self, url: str) -> Optional[Dict]:
        """Research personal portfolio or website"""
        try:
            if not url or not url.startswith(('http://', 'https://')):
                return None
            
            portfolio_info = {
                'url': url,
                'content': {},
                'technologies_found': [],
                'projects_found': [],
                'blog_posts': [],
                'contact_info': {}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract title and meta description
                        title = soup.find('title')
                        if title:
                            portfolio_info['content']['title'] = title.get_text().strip()
                        
                        meta_desc = soup.find('meta', {'name': 'description'})
                        if meta_desc:
                            portfolio_info['content']['description'] = meta_desc.get('content', '')
                        
                        # Extract technologies mentioned
                        tech_keywords = ['python', 'javascript', 'react', 'vue', 'angular', 'node', 'django', 'flask', 'java', 'spring', 'docker', 'kubernetes', 'aws', 'azure', 'tensorflow', 'pytorch']
                        page_text = soup.get_text().lower()
                        
                        found_techs = [tech for tech in tech_keywords if tech in page_text]
                        portfolio_info['technologies_found'] = found_techs
                        
                        # Look for project sections
                        project_sections = soup.find_all(['section', 'div'], {'class': re.compile(r'project|portfolio|work', re.I)})
                        for section in project_sections:
                            project_links = section.find_all('a')
                            for link in project_links:
                                href = link.get('href')
                                text = link.get_text().strip()
                                if href and text:
                                    portfolio_info['projects_found'].append({
                                        'title': text,
                                        'url': urljoin(url, href)
                                    })
                        
                        # Look for blog posts
                        blog_sections = soup.find_all(['article', 'div'], {'class': re.compile(r'blog|post|article', re.I)})
                        for article in blog_sections[:5]:  # Limit to 5 posts
                            title_elem = article.find(['h1', 'h2', 'h3'])
                            if title_elem:
                                portfolio_info['blog_posts'].append({
                                    'title': title_elem.get_text().strip(),
                                    'content_preview': article.get_text()[:200] + '...'
                                })
                        
                        # Extract additional contact info
                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                        emails = re.findall(email_pattern, page_text)
                        if emails:
                            portfolio_info['contact_info']['emails'] = list(set(emails))
                        
                        # Extract social links
                        social_links = {}
                        all_links = soup.find_all('a', href=True)
                        for link in all_links:
                            href = link.get('href', '').lower()
                            if 'linkedin.com' in href:
                                social_links['linkedin'] = link.get('href')
                            elif 'github.com' in href:
                                social_links['github'] = link.get('href')
                            elif 'twitter.com' in href:
                                social_links['twitter'] = link.get('href')
                        
                        portfolio_info['contact_info']['social_links'] = social_links
            
            return portfolio_info
            
        except Exception as e:
            return {'url': url, 'error': str(e)}
    
    async def _search_based_research(self, name: str, emails: List[str], skills: List[str]) -> Dict:
        """Conduct search-based research using search engines"""
        search_results = {
            'google_results': [],
            'additional_profiles': [],
            'mentions': [],
            'professional_activities': []
        }
        
        if not self.google_api_key or not self.google_cse_id:
            logger.warning("Google Search API not configured, skipping search-based research")
            return search_results
        
        try:
            # Create search queries
            search_queries = [
                f'"{name}" developer programmer',
                f'"{name}" {" ".join(skills[:3])}',
                f'"{name}" github portfolio',
                f'"{name}" linkedin profile'
            ]
            
            if emails:
                search_queries.append(f'"{emails[0]}" developer')
            
            async with aiohttp.ClientSession() as session:
                for query in search_queries[:3]:  # Limit to 3 searches
                    try:
                        search_url = f"https://www.googleapis.com/customsearch/v1"
                        params = {
                            'key': self.google_api_key,
                            'cx': self.google_cse_id,
                            'q': query,
                            'num': 5
                        }
                        
                        async with session.get(search_url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                items = data.get('items', [])
                                
                                for item in items:
                                    result = {
                                        'title': item.get('title'),
                                        'link': item.get('link'),
                                        'snippet': item.get('snippet'),
                                        'query_used': query
                                    }
                                    search_results['google_results'].append(result)
                        
                        # Rate limiting
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Search query failed: {e}")
                        continue
            
            # Analyze search results for additional profiles
            search_results['additional_profiles'] = self._extract_profiles_from_search(search_results['google_results'])
            
        except Exception as e:
            search_results['search_error'] = str(e)
        
        return search_results
    
    def _extract_profiles_from_search(self, google_results: List[Dict]) -> List[Dict]:
        """Extract professional profiles from search results"""
        profiles = []
        
        for result in google_results:
            link = result.get('link', '')
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            
            # Identify platform
            platform = None
            if 'stackoverflow.com' in link:
                platform = 'Stack Overflow'
            elif 'medium.com' in link:
                platform = 'Medium'
            elif 'dev.to' in link:
                platform = 'Dev.to'
            elif 'kaggle.com' in link:
                platform = 'Kaggle'
            elif 'leetcode.com' in link:
                platform = 'LeetCode'
            elif 'hackerrank.com' in link:
                platform = 'HackerRank'
            elif 'researchgate.net' in link:
                platform = 'ResearchGate'
            
            if platform:
                profiles.append({
                    'platform': platform,
                    'url': link,
                    'title': title,
                    'description': snippet
                })
        
        return profiles
    
    async def _research_coding_platforms(self, name: str, emails: List[str]) -> Dict:
        """Research coding platforms like LeetCode, HackerRank, etc."""
        platform_results = {}
        
        # This is a simplified implementation
        # In practice, you'd need API access or specific scraping for each platform
        
        platforms = {
            'stackoverflow': f'https://stackoverflow.com/users?tab=Reputation&filter=all&search={name.replace(" ", "+")}',
            'leetcode': f'https://leetcode.com/{name.replace(" ", "").lower()}',
            'kaggle': f'https://www.kaggle.com/{name.replace(" ", "").lower()}',
            'hackerrank': f'https://www.hackerrank.com/{name.replace(" ", "").lower()}'
        }
        
        for platform, url in platforms.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            platform_results[platform] = {
                                'found': True,
                                'url': url,
                                'status': 'Profile appears to exist'
                            }
                        else:
                            platform_results[platform] = {
                                'found': False,
                                'url': url,
                                'status': f'HTTP {response.status}'
                            }
            except Exception as e:
                platform_results[platform] = {
                    'found': False,
                    'url': url,
                    'error': str(e)
                }
            
            # Rate limiting
            await asyncio.sleep(0.5)
        
        return platform_results
    
    async def _research_publications(self, name: str) -> List[Dict]:
        """Research academic publications and papers"""
        publications = []
        
        # Google Scholar search (simplified)
        try:
            search_query = f'"{name}" author'
            scholar_url = f"https://scholar.google.com/scholar?q={search_query.replace(' ', '+')}"
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                async with session.get(scholar_url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract paper titles (simplified)
                        paper_elements = soup.find_all('h3', {'class': 'gs_rt'})
                        for paper_elem in paper_elements[:5]:  # Limit to 5 papers
                            title_link = paper_elem.find('a')
                            if title_link:
                                publications.append({
                                    'title': title_link.get_text().strip(),
                                    'source': 'Google Scholar',
                                    'url': title_link.get('href') if title_link.get('href') else 'N/A'
                                })
                        
        except Exception as e:
            logger.error(f"Publication research failed: {e}")
        
        return publications
    
    async def _research_social_presence(self, name: str, skills: List[str]) -> Dict:
        """Research social media and community presence"""
        social_presence = {
            'twitter': {},
            'youtube': {},
            'community_involvement': [],
            'conference_speaking': []
        }
        
        # This is a simplified implementation
        # Twitter API would require special access
        # YouTube search could be implemented with YouTube API
        
        try:
            # Search for conference speaking or tech talks
            conference_keywords = ['speaker', 'talk', 'presentation', 'conference']
            
            for keyword in conference_keywords:
                search_query = f'"{name}" {keyword} {" ".join(skills[:2])}'
                
                # This would use the same Google Search API as before
                # Simplified for this implementation
                social_presence['conference_speaking'].append({
                    'search_query': search_query,
                    'note': 'Manual search recommended for conference speaking'
                })
                
        except Exception as e:
            social_presence['error'] = str(e)
        
        return social_presence
    
    async def _llm_enhance_research(self, research_results: Dict, candidate: Dict) -> Dict:
        """Use LLM to analyze and enhance research results"""
        if not self.llm_client:
            return {'note': 'LLM analysis not available'}
        
        try:
            # Prepare research summary for LLM analysis
            research_summary = {
                'candidate_name': candidate.get('personal_info', {}).get('name', ''),
                'resume_skills': candidate.get('skills', {}).get('technical', []),
                'github_repos': len(research_results.get('github', {}).get('repositories', [])),
                'portfolio_sites': len(research_results.get('portfolio_sites', [])),
                'additional_profiles': research_results.get('professional_platforms', {}).get('additional_profiles', []),
                'publications': research_results.get('publications', [])
            }
            
            prompt = f"""
Analyze the research results for this candidate and provide insights:

CANDIDATE: {research_summary['candidate_name']}
RESUME SKILLS: {', '.join(research_summary['resume_skills'][:10])}

RESEARCH FINDINGS:
- GitHub repositories found: {research_summary['github_repos']}
- Portfolio sites: {research_summary['portfolio_sites']}
- Additional profiles: {len(research_summary['additional_profiles'])}
- Publications: {len(research_summary['publications'])}

DETAILED RESEARCH DATA:
{json.dumps(research_results, indent=2)[:3000]}...

Provide analysis on:
1. Technical expertise validation (do online activities match resume skills?)
2. Professional activity level (recent contributions, active development)
3. Community involvement and thought leadership
4. Unique strengths discovered through research
5. Areas of specialization not evident from resume
6. Overall professional digital presence assessment
7. Red flags or inconsistencies (if any)
8. Growth trajectory and learning evidence

Provide a concise but comprehensive analysis.
"""
            
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing candidate research data. Provide insights that would be valuable for hiring decisions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            analysis = response.choices[0].message.content
            
            return {
                'llm_analysis': analysis,
                'research_quality_score': self._calculate_research_quality_score(research_results),
                'key_findings': self._extract_key_findings(research_results),
                'verification_status': self._assess_verification_status(research_results, candidate)
            }
            
        except Exception as e:
            return {'llm_analysis_error': str(e)}
    
    def _calculate_research_quality_score(self, research_results: Dict) -> float:
        """Calculate quality score of research findings"""
        score = 0
        max_score = 100
        
        # GitHub presence (30 points)
        github_data = research_results.get('github', {})
        if github_data.get('profile'):
            score += 15
        if github_data.get('repositories'):
            score += 10
            # Bonus for repository quality
            repos = github_data.get('repositories', [])
            if len(repos) >= 5:
                score += 5
        
        # Portfolio sites (20 points)
        portfolio_sites = research_results.get('portfolio_sites', [])
        if portfolio_sites:
            score += 15
            if len(portfolio_sites) > 1:
                score += 5
        
        # Professional platforms (20 points)
        platforms = research_results.get('professional_platforms', {})
        platform_count = len([p for p in platforms.values() if isinstance(p, dict) and p.get('found')])
        score += min(platform_count * 5, 20)
        
        # Publications (15 points)
        publications = research_results.get('publications', [])
        if publications:
            score += min(len(publications) * 3, 15)
        
        # Social presence (15 points)
        social = research_results.get('social_presence', {})
        if social and any(social.values()):
            score += 15
        
        return min(score / max_score * 100, 100)
    
    def _extract_key_findings(self, research_results: Dict) -> List[str]:
        """Extract key findings from research"""
        findings = []
        
        # GitHub findings
        github_data = research_results.get('github', {})
        if github_data.get('repositories'):
            repo_count = len(github_data['repositories'])
            findings.append(f"Found {repo_count} GitHub repositories")
            
            # Language analysis
            languages = set()
            for repo in github_data['repositories']:
                if repo.get('language'):
                    languages.add(repo['language'])
            if languages:
                findings.append(f"Active in programming languages: {', '.join(list(languages)[:5])}")
        
        # Portfolio findings
        portfolio_sites = research_results.get('portfolio_sites', [])
        if portfolio_sites:
            tech_found = set()
            for site in portfolio_sites:
                tech_found.update(site.get('technologies_found', []))
            if tech_found:
                findings.append(f"Portfolio demonstrates: {', '.join(list(tech_found)[:5])}")
        
        # Publication findings
        publications = research_results.get('publications', [])
        if publications:
            findings.append(f"Found {len(publications)} publications/papers")
        
        # Platform findings
        platforms = research_results.get('professional_platforms', {})
        found_platforms = [platform for platform, data in platforms.items() 
                          if isinstance(data, dict) and data.get('found')]
        if found_platforms:
            findings.append(f"Active on platforms: {', '.join(found_platforms)}")
        
        return findings[:10]  # Limit to top 10 findings
    
    def _assess_verification_status(self, research_results: Dict, candidate: Dict) -> Dict:
        """Assess how well research verifies candidate information"""
        verification = {
            'name_verified': False,
            'skills_verified': False,
            'experience_verified': False,
            'contact_verified': False,
            'overall_confidence': 'Low'
        }
        
        candidate_name = candidate.get('personal_info', {}).get('name', '').lower()
        candidate_skills = set(skill.lower() for skill in candidate.get('skills', {}).get('technical', []))
        
        # Name verification
        github_name = research_results.get('github', {}).get('profile', {}).get('name', '').lower()
        if github_name and candidate_name in github_name:
            verification['name_verified'] = True
        
        # Skills verification
        verified_skills = set()
        
        # Check GitHub languages
        github_repos = research_results.get('github', {}).get('repositories', [])
        for repo in github_repos:
            if repo.get('language'):
                verified_skills.add(repo['language'].lower())
        
        # Check portfolio technologies
        portfolio_sites = research_results.get('portfolio_sites', [])
        for site in portfolio_sites:
            verified_skills.update(tech.lower() for tech in site.get('technologies_found', []))
        
        # Calculate skill verification percentage
        if candidate_skills:
            skill_overlap = candidate_skills.intersection(verified_skills)
            skill_verification_rate = len(skill_overlap) / len(candidate_skills)
            verification['skills_verified'] = skill_verification_rate > 0.3  # 30% threshold
            verification['skill_verification_rate'] = skill_verification_rate
        
        # Overall confidence assessment
        confidence_score = 0
        if verification['name_verified']:
            confidence_score += 30
        if verification['skills_verified']:
            confidence_score += 40
        if research_results.get('github', {}).get('repositories'):
            confidence_score += 20
        if research_results.get('portfolio_sites'):
            confidence_score += 10
        
        if confidence_score >= 70:
            verification['overall_confidence'] = 'High'
        elif confidence_score >= 40:
            verification['overall_confidence'] = 'Medium'
        else:
            verification['overall_confidence'] = 'Low'
        
        verification['confidence_score'] = confidence_score
        
        return verification