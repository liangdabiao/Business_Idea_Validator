"""
Pydantic models for the business validator package.
"""

from typing import List, Dict, Any
from pydantic import BaseModel

class KeywordModel(BaseModel):
    """Model for keyword generation results."""
    keywords: List[str]

class HNPostAnalysis(BaseModel):
    """Model for HackerNews post analysis results."""
    relevant: bool
    pain_points: List[str]
    solutions_mentioned: List[str]
    market_signals: List[str]
    sentiment: str  # positive, negative, neutral
    engagement_score: int  # 1-10 based on points and comments

class RedditPostAnalysis(BaseModel):
    """Model for Reddit post analysis results."""
    relevant: bool
    pain_points: List[str]
    solutions_mentioned: List[str]
    market_signals: List[str]
    sentiment: str  # positive, negative, neutral
    engagement_score: int  # 1-10 based on upvotes and comments
    subreddit_context: str  # What the subreddit tells us about the audience


class XhsPostAnalysis(BaseModel):
    """Model for xhs post analysis results."""
    relevant: bool
    pain_points: List[str]
    solutions_mentioned: List[str]
    market_signals: List[str]
    sentiment: str  # positive, negative, neutral
    engagement_score: int  # 1-10 based on upvotes and comments 

class PlatformInsight(BaseModel):
    """Model for platform-specific insights."""
    platform: str  # Name of the platform (e.g., "HackerNews", "Reddit")
    insights: str  # Insights specific to this platform

class CombinedAnalysis(BaseModel):
    """Model for the final combined analysis results."""
    overall_score: int  # 1-100
    market_validation_summary: str
    key_pain_points: List[str]
    existing_solutions: List[str]
    market_opportunities: List[str]
    platform_insights: List[PlatformInsight]  # Separate insights from HN vs Reddit
    recommendations: List[str]
