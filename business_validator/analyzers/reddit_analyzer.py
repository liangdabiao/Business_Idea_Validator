"""
Reddit post analysis functionality.
"""

import logging
from typing import Dict, List

from SimplerLLM.langauge.llm import LLM, LLMProvider
from SimplerLLM.langauge.llm_addons import generate_pydantic_json_model

from business_validator.models import RedditPostAnalysis

# Use the same LLM instance as in keyword_generator
from business_validator.analyzers.keyword_generator import llm_instance

def analyze_reddit_post(post: dict, comments: List[dict], business_idea: str) -> RedditPostAnalysis:
    """Analyze a Reddit post and its comments for business validation.
    
    Args:
        post: Dictionary containing post information
        comments: List of dictionaries containing comment information
        business_idea: The business idea being validated
        
    Returns:
        RedditPostAnalysis object with analysis results
    """
    logging.info(f"Analyzing Reddit post: {post.get('title', '')[:50]}...")
    
    # Format comments for the prompt
    comments_text = "\n".join([
        f"- {c.get('text', '')} (upvotes: {c.get('upvotes', 0)})" 
        for c in comments[:5]
    ])
    
    prompt = f"""
    Business Idea: "{business_idea}"
    
    Reddit Post:
    Subreddit: {post.get('subreddit', 'Unknown')}
    Title: {post.get('title', '')}
    Upvotes: {post.get('upvotes', 0)}
    Comments: {post.get('comments', 0)}
    URL: {post.get('url', '')}
    
    Top Comments:
    {comments_text}
    
    Analyze this Reddit post and comments for business validation:
    
    1. Is this relevant to validating the business idea? (true/false)
    2. What pain points are mentioned in the post or comments?
    3. What solutions are discussed or mentioned?
    4. What market signals does this show? (demand, competition, user behavior, etc.)
    5. What's the overall sentiment? (positive/negative/neutral)
    6. Rate the engagement score 1-10 based on upvotes and comment quality
    7. What does the subreddit context tell us about the audience?
    
    Reddit often has more detailed discussions than other platforms - look for nuanced insights.
    """
    
    try:
        analysis = generate_pydantic_json_model(
            model_class=RedditPostAnalysis,
            llm_instance=llm_instance,
            prompt=prompt
        )
        
        return analysis
    except Exception as e:
        logging.error(f"Error analyzing Reddit post: {e}")
        # Return a default analysis if generation fails
        return RedditPostAnalysis(
            relevant=False,
            pain_points=["Analysis failed"],
            solutions_mentioned=["Analysis failed"],
            market_signals=["Analysis failed"],
            sentiment="neutral",
            engagement_score=0,
            subreddit_context="Analysis failed"
        )
