"""
Reddit scraping functionality.
"""

import requests
import re
import logging
from typing import List, Dict
from urllib.parse import quote_plus
from urllib.parse import urlparse
from business_validator.config import (
    SCRAPERAPI_KEY, 
    REDDIT_DELAY, 
    MAX_COMMENTS_PER_POST
)
from bs4 import BeautifulSoup

def scrape_reddit_search(keyword: str, page: int = 0) -> dict:
    """Scrape Reddit search results for a keyword.
    
    Args:
        keyword: The search keyword
        page: The page number to scrape (0-indexed)
        
    Returns:
        Dictionary containing the scraped posts
    """
    # URL encode the keyword to handle spaces and special characters
    encoded_keyword = quote_plus(keyword)
    
    # Reddit search URL (page is handled differently in Reddit)
    reddit_url = f"https://www.reddit.com/search/?q={encoded_keyword}&sort=relevance&t=all"
    
    # Add page parameter if needed (Reddit uses different pagination)
    if page > 0:
        reddit_url += f"&count={page * 25}&after={page}"
    
    # ScraperAPI payload for Reddit - updated based on working example
    payload = {
        'api_key': SCRAPERAPI_KEY,
        'url': reddit_url,
        'wait_for_selector': '.SearchResults_container',
        'device_type': 'desktop',
        'output_format': 'markdown'
    }
    
    try:
        response = requests.get('https://api.scraperapi.com/', params=payload, timeout=30)
        response.raise_for_status()
        
        # Parse the markdown response
        markdown_content = response.text
        posts = parse_reddit_search_markdown(markdown_content)
        
        return {'posts': posts}
        
    except Exception as e:
        logging.error(f"Error scraping Reddit for keyword '{keyword}' page {page}: {e}")
        return {'posts': []}

def parse_reddit_search_markdown(markdown_content: str) -> List[dict]:
    """Parse Reddit search markdown to extract post information.
    
    Args:
        markdown_content: The markdown content from ScraperAPI
        
    Returns:
        List of dictionaries containing post information
    """
    posts = []
    lines = markdown_content.split('\n')
    
    current_post = {}
    in_post_section = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if not line:
            continue
        
        # Look for post titles which are typically in the format: [ Title ](/r/subreddit/...)
        if line.startswith('## [ ') and ' ](/r/' in line:
            # Save previous post if exists
            if current_post.get('title'):
                posts.append(current_post.copy())
                current_post = {}
            
            # Extract title
            title_end = line.find(' ](/r/')
            if title_end > 4:  # "## [ " is 5 chars
                title = line[4:title_end]  # Skip the "## [ " prefix
                
                # Extract URL and subreddit
                url_start = line.find('](/') + 2
                url_end = line.find(')', url_start)
                url = "https://www.reddit.com" + line[url_start:url_end] if url_end > url_start else ''
                
                # Extract subreddit from URL
                subreddit = ""
                if '/r/' in url:
                    subreddit_start = url.find('/r/') + 3
                    subreddit_end = url.find('/', subreddit_start)
                    if subreddit_end > subreddit_start:
                        subreddit = url[subreddit_start:subreddit_end]
                
                current_post['title'] = title
                current_post['url'] = url
                current_post['upvotes'] = 0
                current_post['comments'] = 0
                current_post['subreddit'] = subreddit if subreddit else ""
                in_post_section = True
        
        # Look for explicit subreddit info (r/subreddit format)
        elif in_post_section and line.startswith('r/'):
            current_post['subreddit'] = line.split()[0].replace('r/', '')
        
        # Look for votes and comments info
        elif in_post_section and 'votes' in line and 'comments' in line:
            # This line might contain vote and comment counts
            parts = line.split('·')
            for part in parts:
                part = part.strip()
                if 'votes' in part:
                    numbers = re.findall(r'\d+', part)
                    if numbers:
                        current_post['upvotes'] = int(numbers[0])
                elif 'comments' in part:
                    numbers = re.findall(r'\d+', part)
                    if numbers:
                        current_post['comments'] = int(numbers[0])
        
        # Check if we're starting a new section (which means end of current post)
        elif in_post_section and line.startswith('---'):
            in_post_section = False
    
    # Don't forget the last post
    if current_post.get('title'):
        posts.append(current_post)
    
    return posts

def scrape_reddit_post_comments(post_url: str) -> List[dict]:
    """Scrape comments from a specific Reddit post.
    
    Args:
        post_url: The URL of the Reddit post
        
    Returns:
        List of dictionaries containing comment information
    """
    # ScraperAPI payload for individual Reddit post - updated based on working example
    parsed = urlparse(post_url)
    path_segments = parsed.path.strip('/').split('/')
    
    # 验证标准Reddit URL结构：/r/<subreddit>/comments/<post_id>/<post_title>/
    if len(path_segments) >= 4 and path_segments[2] == 'comments':
        post_url_token =  path_segments[3]
    else:
        return [] 
    post_url_new =f"https://www.reddit.com/svc/shreddit/comments/r/cleaningtips/t3_{post_url_token}?render-mode=partial"
    payload = {
        'api_key': SCRAPERAPI_KEY,
        'url': post_url_new, 
        'device_type': 'desktop', 
    }
    
    try:
        response = requests.get('https://api.scraperapi.com/', params=payload, timeout=30)
        response.raise_for_status()
        
        # Parse comments from markdown
        markdown_content = response.text
        comments = parse_reddit_comments_markdown_new(markdown_content)
        
        # Return only top N comments
        return comments[:MAX_COMMENTS_PER_POST]
        
    except Exception as e:
        logging.error(f"Error scraping comments for {post_url}: {e}")
        return []

def parse_reddit_comments_markdown(markdown_content: str) -> List[dict]:
    """Parse Reddit comments from markdown.
    
    Args:
        markdown_content: The markdown content from ScraperAPI
        
    Returns:
        List of dictionaries containing comment information
    """
    comments = []
    lines = markdown_content.split('\n')

    print(lines)
    
    current_comment = {}
    in_comment_section = False
    
    for line in lines:
        line = line.strip()
        
        # Detect if we're in the comments section
        if 'comments' in line.lower() and ('sort by' in line.lower() or 'best' in line.lower()):
            in_comment_section = True
            continue
        
        if not in_comment_section:
            continue
        
        # Look for comment content
        # Reddit comments in markdown often appear with username first, then the comment text
        if line.startswith('[u/') or line.startswith('u/'):
            # This is likely a username line, the next line might be the comment
            if current_comment.get('text'):
                # Save previous comment
                comments.append(current_comment.copy())
                current_comment = {}
            
            current_comment['upvotes'] = 0
            # Try to find the comment text in the next few lines
            continue
        
        # If we have a current comment being built and this line looks like content
        if current_comment and not current_comment.get('text') and line and len(line) > 5 and not line.startswith('[') and not line.startswith('*'):
            current_comment['text'] = line
        
        # Look for upvotes in comments
        elif 'upvote' in line.lower() or 'point' in line.lower() or 'vote' in line.lower():
            numbers = re.findall(r'\d+', line)
            if numbers and current_comment:
                current_comment['upvotes'] = int(numbers[0])
    
    # Don't forget the last comment
    if current_comment.get('text'):
        comments.append(current_comment)
    
    # If we couldn't parse any comments properly, create a fallback comment
    if not comments:
        comments.append({
            'text': "Unable to parse comments. Reddit's comment structure may have changed.",
            'upvotes': 0
        })
    
    return comments





def parse_reddit_comments_markdown_new(markdown_content: str) -> List[dict]:
    # markdown_content 是html,需要 提取出所有<p>元素 赋值给 lines数组
    # 1. 提取特定class的<p>标签
    # 创建BeautifulSoup对象解析HTML
    soup = BeautifulSoup(markdown_content, 'html.parser')  # [1,3,5,6](@ref)

    # 提取所有<p>元素并赋值给lines数组
    lines = soup.find_all('p')  # [1,4,5,8,9](@ref)

    # 验证提取结果
    print(f"找到 {len(lines)} 个<p>元素：")
    for i, p in enumerate(lines, 1):
        print(f"{i}. {p.text}")
 
    comments = [] 
 
     
    in_comment_section = False
    
    for line in lines:
        current_comment = {}
        line = line.text.strip()
        current_comment['upvotes'] = 1
        current_comment['text'] = line
        comments.append(current_comment )
       
    # If we couldn't parse any comments properly, create a fallback comment
    if not comments:
        comments.append({
            'text': "Unable to parse comments. Reddit's comment structure may have changed.",
            'upvotes': 0
        })
    
    return comments
