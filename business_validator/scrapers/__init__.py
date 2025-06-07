"""
Scraper modules for fetching data from various platforms.
"""

from business_validator.scrapers.hackernews import scrape_hackernews, parse_hn_markdown
from business_validator.scrapers.reddit import (
    scrape_reddit_search, 
    parse_reddit_search_markdown,
    scrape_reddit_post_comments,
    parse_reddit_comments_markdown,
    parse_reddit_comments_markdown_new
)
from business_validator.scrapers.gzh import  scrape_gzh
from business_validator.scrapers.xhs import   scrape_xhs_post_comments,scrape_xhs_search

__all__ = [
    'scrape_gzh', 
    'scrape_hackernews',
    'parse_hn_markdown',
    'scrape_reddit_search',
    'parse_reddit_search_markdown',
    'scrape_reddit_post_comments',
    'parse_reddit_comments_markdown',
    'parse_reddit_comments_markdown_new',
    'scrape_xhs_search',
    'scrape_xhs_post_comments'
]
