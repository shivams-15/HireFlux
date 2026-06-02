"""
Free Web Search Utilities
==========================

This module provides free web search functionality using DuckDuckGo.
No API keys required - completely free to use.
"""

import logging
import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
import json
from bs4 import BeautifulSoup
import urllib.parse
import time
import importlib

logger = logging.getLogger(__name__)

# Prefer the renamed package (`ddgs`) and keep backward compatibility.
DDGS: Any = None
try:
    DDGS = importlib.import_module("ddgs").DDGS
    DDGS_AVAILABLE = True
    DDGS_PROVIDER = "ddgs"
    logger.info("Using ddgs library for web searches")
except (ImportError, AttributeError):
    try:
        DDGS = importlib.import_module("duckduckgo_search").DDGS
        DDGS_AVAILABLE = True
        DDGS_PROVIDER = "duckduckgo_search"
        logger.info("Using duckduckgo_search library for web searches")
    except (ImportError, AttributeError):
        DDGS_AVAILABLE = False
        DDGS_PROVIDER = None
        logger.warning("No DDGS library available, using HTML scraping fallback")


class DuckDuckGoSearch:
    """Free web search using DuckDuckGo (no API key needed)"""
    
    def __init__(self):
        """Initialize DuckDuckGo search client"""
        self.base_url = "https://html.duckduckgo.com/html/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.last_request_time = 0
        self.request_delay = 3.0  # Increased delay to avoid rate limiting (was 1.5)
        self.use_library = DDGS_AVAILABLE
        provider = DDGS_PROVIDER if self.use_library else "HTML scraping"
        logger.info(f"Initialized DuckDuckGo search (free, no API key required) - Using {provider}")
    
    async def search(self, query: str, max_results: int = 10, retry_count: int = 0) -> List[Dict]:
        """
        Search DuckDuckGo and return results
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: 10)
            retry_count: Current retry attempt (internal use)
            
        Returns:
            List of search result dictionaries with 'title', 'url', 'snippet'
        """
        # Use library method if available (more reliable)
        if self.use_library:
            return await self._search_with_library(query, max_results)
        else:
            return await self._search_with_scraping(query, max_results, retry_count)
    
    async def _search_with_library(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search using duckduckgo-search library (preferred method)"""
        try:
            # Rate limiting
            elapsed = time.time() - self.last_request_time
            if elapsed < self.request_delay:
                await asyncio.sleep(self.request_delay - elapsed)
            
            # Run synchronous DDGS in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def sync_search():
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=max_results))
                    return results
            
            raw_results = await loop.run_in_executor(None, sync_search)
            self.last_request_time = time.time()
            
            # Format results
            formatted_results = []
            for result in raw_results:
                formatted_results.append({
                    'title': result.get('title', ''),
                    'url': result.get('href', result.get('link', '')),
                    'snippet': result.get('body', result.get('snippet', '')),
                    'source': 'DuckDuckGo'
                })
            
            logger.info(f"Found {len(formatted_results)} results for query: '{query}' (using library)")
            return formatted_results
            
        except Exception as e:
            logger.error(f"DuckDuckGo library search failed: {e}, falling back to scraping")
            self.use_library = False  # Fallback to scraping for future requests
            return await self._search_with_scraping(query, max_results, 0)
    
    async def _search_with_scraping(self, query: str, max_results: int = 10, retry_count: int = 0) -> List[Dict]:
        """Search using HTML scraping (fallback method)"""
        max_retries = 3
        
        try:
            # Rate limiting
            elapsed = time.time() - self.last_request_time
            if elapsed < self.request_delay:
                await asyncio.sleep(self.request_delay - elapsed)
            
            results = []
            
            async with aiohttp.ClientSession() as session:
                # DuckDuckGo HTML search endpoint
                params = {
                    'q': query,
                    'kl': 'us-en'
                }
                
                async with session.post(
                    self.base_url,
                    data=params,
                    headers=self.headers,
                    timeout=15
                ) as response:
                    
                    self.last_request_time = time.time()
                    
                    # Handle 202 (Accepted - async processing)
                    if response.status == 202:
                        if retry_count < max_retries:
                            wait_time = 2 * (retry_count + 1)  # Exponential backoff
                            logger.info(f"DuckDuckGo returned 202 (processing), retrying in {wait_time}s (attempt {retry_count + 1}/{max_retries})")
                            await asyncio.sleep(wait_time)
                            return await self._search_with_scraping(query, max_results, retry_count + 1)
                        else:
                            logger.warning(f"DuckDuckGo search timed out after {max_retries} retries (status 202)")
                            return []
                    
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract search results
                        result_divs = soup.find_all('div', class_='result')
                        
                        for div in result_divs[:max_results]:
                            try:
                                # Extract title and URL
                                title_elem = div.find('a', class_='result__a')
                                if not title_elem:
                                    continue
                                
                                title = title_elem.get_text().strip()
                                url = title_elem.get('href', '')
                                
                                # Extract snippet
                                snippet_elem = div.find('a', class_='result__snippet')
                                snippet = snippet_elem.get_text().strip() if snippet_elem else ''
                                
                                if title and url:
                                    results.append({
                                        'title': title,
                                        'url': url,
                                        'snippet': snippet,
                                        'source': 'DuckDuckGo'
                                    })
                            except Exception as e:
                                logger.debug(f"Error parsing result: {e}")
                                continue
                        
                        logger.info(f"Found {len(results)} results for query: '{query}' (using HTML scraping)")
                    else:
                        logger.warning(f"DuckDuckGo search returned status {response.status}")
            
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    async def search_candidate(self, name: str, additional_keywords: List[str] = None) -> Dict:
        """
        Search for a candidate across the web
        
        Args:
            name: Candidate name
            additional_keywords: Additional search terms (skills, etc.)
            
        Returns:
            Dictionary containing organized search results
        """
        results = {
            'github': [],
            'linkedin': [],
            'stackoverflow': [],
            'portfolio': [],
            'other': []
        }
        
        # Create comprehensive search queries
        queries = [
            f'"{name}" developer programmer',
            f'"{name}" github portfolio',
            f'"{name}" linkedin profile',
        ]
        
        if additional_keywords:
            keywords = ' '.join(additional_keywords[:3])
            queries.append(f'"{name}" {keywords}')
        
        # Execute searches
        all_results = []
        for query in queries:
            search_results = await self.search(query, max_results=10)
            all_results.extend(search_results)
            await asyncio.sleep(self.request_delay)  # Rate limiting
        
        # Categorize results
        for result in all_results:
            url = result['url'].lower()
            
            if 'github.com' in url:
                if result not in results['github']:
                    results['github'].append(result)
            elif 'linkedin.com' in url:
                if result not in results['linkedin']:
                    results['linkedin'].append(result)
            elif 'stackoverflow.com' in url:
                if result not in results['stackoverflow']:
                    results['stackoverflow'].append(result)
            elif any(domain in url for domain in ['portfolio', 'blog', 'personal']):
                if result not in results['portfolio']:
                    results['portfolio'].append(result)
            else:
                if result not in results['other']:
                    results['other'].append(result)
        
        return results


class WebSearchManager:
    """Unified web search manager supporting multiple search providers"""
    
    def __init__(self):
        """Initialize web search manager with available providers"""
        self.ddg = DuckDuckGoSearch()
        logger.info("WebSearchManager initialized with DuckDuckGo")
    
    async def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search the web using available provider
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of search results
        """
        return await self.ddg.search(query, max_results)
    
    async def search_candidate(self, name: str, skills: List[str] = None, 
                              email: str = None) -> Dict:
        """
        Comprehensive candidate search
        
        Args:
            name: Candidate name
            skills: List of skills/technologies
            email: Email address (if available)
            
        Returns:
            Organized search results with professional profiles
        """
        keywords = skills[:5] if skills else []
        results = await self.ddg.search_candidate(name, keywords)
        
        # If email provided, do additional search
        if email:
            email_results = await self.ddg.search(f'"{email}" developer', max_results=5)
            results['email_search'] = email_results
        
        return results
    
    async def fetch_page_content(self, url: str) -> Optional[str]:
        """
        Fetch and extract main content from a URL
        
        Args:
            url: URL to fetch
            
        Returns:
            Extracted text content or None if failed
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Remove script and style elements
                        for script in soup(['script', 'style']):
                            script.decompose()
                        
                        # Get text
                        text = soup.get_text()
                        
                        # Clean up
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = ' '.join(chunk for chunk in chunks if chunk)
                        
                        return text[:5000]  # Limit to first 5000 chars
        except Exception as e:
            logger.error(f"Error fetching page {url}: {e}")
            return None


# Convenience function
async def search_web(query: str, max_results: int = 10) -> List[Dict]:
    """
    Quick web search function
    
    Args:
        query: Search query
        max_results: Maximum results
        
    Returns:
        List of search results
    """
    searcher = WebSearchManager()
    return await searcher.search(query, max_results)
