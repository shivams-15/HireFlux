"""API handlers for various external services."""

import aiohttp
import asyncio
import logging
import json
from typing import Dict, List, Optional
import os
from datetime import datetime, timedelta
import time
from ratelimit import limits, sleep_and_retry
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Rate limiting decorators
ONE_MINUTE = 60
ONE_HOUR = 3600
ONE_DAY = 86400

class RateLimiter:
    """Custom rate limiter for API requests"""

    def __init__(self, calls: int, period: int):
        """Initialize rate limiter
        
        Args:
            calls: Maximum number of calls allowed in the period
            period: Time period in seconds
        """
        self.calls = calls
        self.period = period
        self.timestamps = []

    async def acquire(self):
        """Wait until a request can be made"""
        now = time.time()
        
        # Remove timestamps outside the current window
        self.timestamps = [ts for ts in self.timestamps if now - ts < self.period]
        
        if len(self.timestamps) >= self.calls:
            # Wait until oldest timestamp expires
            sleep_time = self.timestamps[0] + self.period - now
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            # Remove expired timestamps
            self.timestamps = self.timestamps[1:]
        
        self.timestamps.append(now)

    def __call__(self, func):
        """Decorator for rate-limiting async functions"""
        async def wrapper(*args, **kwargs):
            await self.acquire()
            return await func(*args, **kwargs)
        return wrapper

# Add cache support
def setup_cache():
    """Set up request caching"""
    from requests_cache import CachedSession
    from datetime import timedelta
    
    # Create cache with default expiration of 1 hour
    return CachedSession(
        cache_name='hr_recruiter_cache',
        backend='sqlite',
        expire_after=timedelta(hours=1)
    )

# Error handling decorator
def handle_api_errors(func):
    """Decorator for handling API errors"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {str(e)}")
            return None
        except asyncio.TimeoutError:
            logger.error("API request timed out")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in API request: {str(e)}")
            return None
    return wrapper

@handle_api_errors
@sleep_and_retry
@limits(calls=30, period=ONE_MINUTE)
async def fetch_github_profile(username: str, token: str) -> Dict:
    """Fetch GitHub profile and repository information"""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    async with aiohttp.ClientSession() as session:
        # Fetch user profile
        async with session.get(
            f'https://api.github.com/users/{username}',
            headers=headers
        ) as response:
            if response.status == 404:
                return None
            profile = await response.json()
        
        # Fetch repositories
        async with session.get(
            f'https://api.github.com/users/{username}/repos',
            headers=headers,
            params={'sort': 'updated', 'per_page': 100}
        ) as response:
            repos = await response.json()
        
        # Fetch contributions
        year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        async with session.get(
            f'https://api.github.com/users/{username}/events',
            headers=headers,
            params={'since': year_ago}
        ) as response:
            events = await response.json()
        
        return {
            'profile': profile,
            'repositories': repos,
            'recent_activity': events
        }

@handle_api_errors
@sleep_and_retry
@limits(calls=100, period=ONE_HOUR)
async def fetch_linkedin_profile(profile_id: str, token: str) -> Dict:
    """Fetch LinkedIn profile information"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    
    fields = [
        'id',
        'firstName',
        'lastName',
        'headline',
        'summary',
        'positions',
        'skills',
        'certifications',
        'publications',
        'patents',
        'languages',
        'education'
    ]
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f'https://api.linkedin.com/v2/people/{profile_id}',
            headers=headers,
            params={'projection': f"({','.join(fields)})"}
        ) as response:
            if response.status == 404:
                return None
            return await response.json()

@handle_api_errors
@sleep_and_retry
@limits(calls=100, period=ONE_HOUR)
async def fetch_kaggle_profile(username: str, token: str) -> Dict:
    """Fetch Kaggle profile and competition information"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    
    async with aiohttp.ClientSession() as session:
        # Fetch user profile
        async with session.get(
            f'https://www.kaggle.com/api/v1/users/{username}',
            headers=headers
        ) as response:
            if response.status == 404:
                return None
            profile = await response.json()
        
        # Fetch competitions
        async with session.get(
            f'https://www.kaggle.com/api/v1/users/{username}/competitions',
            headers=headers
        ) as response:
            competitions = await response.json()
        
        # Fetch datasets
        async with session.get(
            f'https://www.kaggle.com/api/v1/users/{username}/datasets',
            headers=headers
        ) as response:
            datasets = await response.json()
        
        return {
            'profile': profile,
            'competitions': competitions,
            'datasets': datasets
        }

@handle_api_errors
@sleep_and_retry
@limits(calls=100, period=ONE_DAY)
async def perform_web_search(query: str, api_key: str) -> List[Dict]:
    """Perform a web search using Google Custom Search API"""
    search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    if not search_engine_id:
        raise ValueError("Google Search Engine ID not configured")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            'https://www.googleapis.com/customsearch/v1',
            params={
                'key': api_key,
                'cx': search_engine_id,
                'q': query,
                'num': 10  # Number of results
            }
        ) as response:
            results = await response.json()
            
            if 'items' not in results:
                return []
            
            return [{
                'title': item.get('title'),
                'link': item.get('link'),
                'snippet': item.get('snippet'),
                'date': item.get('pagemap', {}).get('metatags', [{}])[0].get('article:published_time')
            } for item in results['items']]
