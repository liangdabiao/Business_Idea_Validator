"""
Xhs post analysis functionality.
"""

import logging
from typing import Dict, List

from SimplerLLM.langauge.llm import LLM, LLMProvider
from SimplerLLM.langauge.llm_addons import generate_pydantic_json_model

from business_validator.models import XhsPostAnalysis

# Use the same LLM instance as in keyword_generator
from business_validator.analyzers.keyword_generator import llm_instance

def analyze_xhs_post(post: dict, comments: List[dict], business_idea: str) -> XhsPostAnalysis:
    """Analyze a Xhs(小红书) post and its comments for business validation.
    
    Args:
        post: Dictionary containing post information
        comments: List of dictionaries containing comment information
        business_idea: The business idea being validated
        
    Returns:
        XhsPostAnalysis object with analysis results
    """
    try:
        msg = f"Analyzing Xhs post: {post.get('title', '')[:50]}..."
        logging.info(msg.encode('utf-8', errors='replace').decode('utf-8'))
    except Exception:
        logging.info("Analyzing Xhs post")
    
    # Format comments for the prompt
    comments_text = "\n".join([
        f"- {c.get('content', '')} (user: {c.get('user', '')})" 
        for c in comments[:15]
    ])
    
    prompt = f"""
    Business Idea: "{business_idea}"
    
    Xhs Post:
    Title: {post.get('title', '')}
    desc: {post.get('desc', 0)}
    liked_count: {post.get('liked_count', 0)}
    collected_count: {post.get('collected_count', '')}
    shared_count: {post.get('shared_count', '')}
    comments_count: {post.get('comments_count', '')}
    
    Top Comments:
    {comments_text}
    
    Analyze this Xhs(小红书) post and comments for business validation:
    
    1. Is this relevant to validating the business idea? Note:Pay attention to the (location/city/brand...) information; if it does not match, then determine it as false. (true/false)
    2. What pain points are mentioned in the post or comments?
    3. What solutions are discussed or mentioned?
    4. What market signals does this show? (demand, competition, user behavior, etc.)
    5. What's the overall sentiment? (positive/negative/neutral)
    6. Rate the engagement score 1-10 based on upvotes and comment quality
    
    Xhs(小红书) often has more detailed discussions than other platforms - look for nuanced insights. 
    Note: return in chinese language.
    """
    
    try:
        analysis = generate_pydantic_json_model(
            model_class=XhsPostAnalysis,
            llm_instance=llm_instance,
            prompt=prompt
        )
        
        return analysis
    except Exception as e:
        logging.error(f"Error analyzing Xhs post: {e}")
        # Return a default analysis if generation fails
        return XhsPostAnalysis(
            relevant=False,
            pain_points=["Analysis failed"],
            solutions_mentioned=["Analysis failed"],
            market_signals=["Analysis failed"],
            sentiment="neutral",
            engagement_score=0,
        )
