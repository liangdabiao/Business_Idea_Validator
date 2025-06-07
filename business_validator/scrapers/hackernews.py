"""
HackerNews scraping functionality.
"""

import requests
import time
import logging
from typing import List, Dict
from urllib.parse import quote_plus

from business_validator.config import SCRAPERAPI_KEY, HN_DELAY

def scrape_hackernews(keyword: str, page: int = 0) -> dict:
    """Scrape HackerNews search results for a keyword.
    
    Args:
        keyword: The search keyword
        page: The page number to scrape (0-indexed)
        
    Returns:
        Dictionary containing the scraped posts
    """
    # URL encode the keyword to handle spaces and special characters
    encoded_keyword = quote_plus(keyword)
    
    # Build the full HackerNews URL with all parameters
    hn_url = f"https://hn.algolia.com/?dateRange=all&page={page}&prefix=true&query={encoded_keyword}&sort=byPopularity&type=story"
    
    # ScraperAPI payload with proper parameters
    payload = {
        'api_key': SCRAPERAPI_KEY,
        'url': hn_url,
        'wait_for_selector': '.SearchResults_container',
        'device_type': 'desktop',
        'render': 'true',
        'output_format': 'markdown'
    }
    
    try:
        response = requests.get('https://api.scraperapi.com/', params=payload, timeout=30)
        response.raise_for_status()
        
        # Parse the markdown response
        markdown_content = response.text
        posts = parse_hn_markdown(markdown_content)
        
        return {'posts': posts}
        
    except Exception as e:
        logging.error(f"Error scraping HN for keyword '{keyword}' page {page}: {e}")
        return {'posts': []}

def parse_hn_markdown(markdown_content: str) -> List[dict]:
    """Parse HackerNews markdown content to extract posts.
    
    Args:
        markdown_content: The markdown content from ScraperAPI
        
    Returns:
        List of dictionaries containing post information
    """
    posts = []
    lines = markdown_content.split('\n')
    
    current_post = {}
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Look for post titles (usually start with [title](url) format)
        if line.startswith('[') and '](http' in line:
            # Save previous post if exists
            if current_post.get('title'):
                posts.append(current_post.copy())
                current_post = {}
            
            # Extract title and URL
            title_end = line.find('](http')
            if title_end > 1:
                title = line[1:title_end]
                
                # Skip if title contains image extensions or is too short
                if any(ext in title.lower() for ext in ['jpg', 'png', 'jpeg', 'gif']) or len(title) < 20:
                    continue
                    
                url_start = line.find('](') + 2
                url_end = line.find(')', url_start)
                url = line[url_start:url_end] if url_end > url_start else ''
                
                current_post['title'] = title
                current_post['url'] = url
                current_post['points'] = 0
                current_post['comments'] = 0
        
        # Look for points and comments (usually in format like "X points|user|time ago|Y comments")
        elif 'points' in line and 'ago' in line:
            parts = line.split('|')
            for part in parts:
                part = part.strip()
                if 'points' in part:
                    try:
                        points = int(part.split()[0])
                        current_post['points'] = points
                    except:
                        pass
                elif 'comment' in part:
                    try:
                        comments = int(part.split()[0])
                        current_post['comments'] = comments
                    except:
                        pass
    
    # Don't forget the last post
    if current_post.get('title'):
        posts.append(current_post)
    
    return posts
