"""
Configuration settings for the business validator package.
"""

import os

# API Keys
SCRAPERAPI_KEY = "eaf276899b491e64s3742se3ssb8c58"  # Replace with your ScraperAPI key
GZH_AUTH_TOKEN = "xq5oa0Zj+GMAjRQnzU2evyUdwCoyuYHj7spyyD7s3Q4RZMxqmA+1Uw==" # from https://api.tikhub.io
XHZ_AUTH_TOKEN = "xq5oa0Zj+GMAjRQnzU2evyUdwCoyuYHj7spyyDsga3Q4RZMxqmA+1Uw==" # from https://api.tikhub.io
# HackerNews Configuration
MAX_PAGES_PER_KEYWORD_HN = 3  # Number of pages to scrape per keyword on HN
HN_DELAY = 1  # Seconds to wait between HN requests

# Reddit Configuration  
MAX_PAGES_PER_KEYWORD_REDDIT = 3  # Number of pages to scrape per keyword on Reddit
MAX_POSTS_TO_ANALYZE = 20  # Maximum posts to scrape comments for per keyword
MAX_COMMENTS_PER_POST = 10  # Maximum top comments to analyze per post
REDDIT_DELAY = 2  # Seconds to wait between Reddit requests (longer due to more complexity)

# Logging and Checkpoint Configuration
DATA_DIR = "validation_data"
LOG_DIR = "logs"
CHECKPOINT_INTERVAL = 5  # Save checkpoints every N items when processing lists
