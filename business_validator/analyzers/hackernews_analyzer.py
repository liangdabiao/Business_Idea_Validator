"""
HackerNews post analysis functionality.
"""

import logging
from typing import Dict

from SimplerLLM.langauge.llm import LLM, LLMProvider
from SimplerLLM.langauge.llm_addons import generate_pydantic_json_model

from business_validator.models import HNPostAnalysis

# Use the same LLM instance as in keyword_generator
from business_validator.analyzers.keyword_generator import llm_instance

def analyze_hn_post(post: dict, business_idea: str) -> HNPostAnalysis:
    """Analyze a single HackerNews post for business validation.
    
    Args:
        post: Dictionary containing post information
        business_idea: The business idea being validated
        
    Returns:
        HNPostAnalysis object with analysis results
    """
    logging.info(f"Analyzing HN post: {post['title'][:50]}...")
    
    prompt = f"""
    Business Idea: "{business_idea}"
    
    HackerNews Post:
    Title: {post['title']}
    Points: {post['points']}
    Comments: {post['comments']}
    URL: {post['url']}
    
    Analyze this post for business validation signals:
    
    1. Is this post relevant to validating the business idea? (true/false)
    2. What pain points are mentioned or implied?
    3. What solutions are discussed or mentioned?
    4. What market signals does this show? (demand, competition, trends, etc.)
    5. What's the overall sentiment? (positive/negative/neutral)
    6. Rate the engagement score 1-10 based on points and comments relative to typical HN posts
    
    Focus on extracting actionable insights for business validation.
    """
    
    try:
        analysis = generate_pydantic_json_model(
            model_class=HNPostAnalysis,
            llm_instance=llm_instance,
            prompt=prompt
        )
        
        return analysis
    except Exception as e:
        logging.error(f"Error analyzing HN post: {e}")
        # Return a default analysis if generation fails
        return HNPostAnalysis(
            relevant=False,
            pain_points=["Analysis failed"],
            solutions_mentioned=["Analysis failed"],
            market_signals=["Analysis failed"],
            sentiment="neutral",
            engagement_score=0
        )
