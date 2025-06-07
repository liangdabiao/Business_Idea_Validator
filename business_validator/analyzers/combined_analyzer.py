"""
Combined analysis functionality for generating final business validation reports.
"""

import logging
from typing import List

from SimplerLLM.langauge.llm import LLM, LLMProvider
from SimplerLLM.langauge.llm_addons import generate_pydantic_json_model

from business_validator.models import HNPostAnalysis, PlatformInsight, RedditPostAnalysis, CombinedAnalysis,XhsPostAnalysis

# Use the same LLM instance as in keyword_generator
from business_validator.analyzers.keyword_generator import llm_instance

def generate_final_analysis(
    hn_analyses: List[HNPostAnalysis], 
    reddit_analyses: List[RedditPostAnalysis], 
    business_idea: str, 
    keywords: List[str]
) -> CombinedAnalysis:
    """Generate final business validation analysis from both HN and Reddit.
    
    Args:
        hn_analyses: List of HackerNews post analyses
        reddit_analyses: List of Reddit post analyses
        business_idea: The business idea being validated
        keywords: The keywords used for searching
        
    Returns:
        CombinedAnalysis object with final analysis results
    """
    logging.info("Generating final combined analysis...")
    
    # Prepare summaries
    total_hn_posts = len(hn_analyses)
    relevant_hn_posts = [a for a in hn_analyses if a.relevant]
    total_reddit_posts = len(reddit_analyses)
    relevant_reddit_posts = [a for a in reddit_analyses if a.relevant]
    
    prompt = f"""
    Business Idea: "{business_idea}"
    Keywords Searched: {', '.join(keywords)}
    
    Analysis Summary:
    
    HackerNews:
    - Total posts analyzed: {total_hn_posts}
    - Relevant posts found: {len(relevant_hn_posts)}
    
    Reddit:
    - Total posts analyzed: {total_reddit_posts}
    - Relevant posts found: {len(relevant_reddit_posts)}
    
    HackerNews Insights:
    {chr(10).join([f"- Pain Points: {a.pain_points}, Solutions: {a.solutions_mentioned}, Sentiment: {a.sentiment}" for a in relevant_hn_posts[:5]])}
    
    Reddit Insights:
    {chr(10).join([f"- Pain Points: {a.pain_points}, Solutions: {a.solutions_mentioned}, Subreddit: {a.subreddit_context}, Sentiment: {a.sentiment}" for a in relevant_reddit_posts[:5]])}
    
    Based on this combined HackerNews and Reddit validation research, provide:
    
    1. Overall validation score (1-100) where:
       - 85+ = Strong market validation with clear demand
       - 70-84 = Good validation with some concerns
       - 50-69 = Mixed signals, needs more research
       - 30-49 = Weak validation, major concerns
       - 0-29 = Little to no validation found
    
    2. Market validation summary (2-3 sentences)
    3. Key pain points discovered across both platforms
    4. Existing solutions mentioned across both platforms
    5. Market opportunities identified
    6. Platform-specific insights as a list of objects, each with 'platform' (e.g., "HackerNews", "Reddit") and 'insights' (the specific insights for that platform)
    7. Specific recommendations for moving forward
    
    Consider that HackerNews tends to have more technical/startup audience while Reddit has more diverse consumer perspectives.
    """
    
    try:
        final_analysis = generate_pydantic_json_model(
            model_class=CombinedAnalysis,
            llm_instance=llm_instance,
            prompt=prompt
        )
        
        return final_analysis
    except Exception as e:
        logging.error(f"Error generating final analysis: {e}")
        # Create a fallback analysis
        return create_fallback_analysis(hn_analyses, reddit_analyses, business_idea, keywords)

def create_fallback_analysis(
    hn_analyses: List[HNPostAnalysis], 
    reddit_analyses: List[RedditPostAnalysis], 
    business_idea: str, 
    keywords: List[str]
) -> CombinedAnalysis:
    """Create a simplified analysis when the full analysis generation fails.
    
    Args:
        hn_analyses: List of HackerNews post analyses
        reddit_analyses: List of Reddit post analyses
        business_idea: The business idea being validated
        keywords: The keywords used for searching
        
    Returns:
        CombinedAnalysis object with simplified analysis results
    """
    logging.info("Creating fallback analysis...")
    
    # Count relevant posts
    relevant_hn_posts = [a for a in hn_analyses if a.relevant]
    relevant_reddit_posts = [a for a in reddit_analyses if a.relevant]
    
    # Collect pain points and solutions
    all_pain_points = []
    all_solutions = []
    
    for analysis in relevant_hn_posts:
        all_pain_points.extend(analysis.pain_points)
        all_solutions.extend(analysis.solutions_mentioned)
    
    for analysis in relevant_reddit_posts:
        all_pain_points.extend(analysis.pain_points)
        all_solutions.extend(analysis.solutions_mentioned)
    
    # Remove duplicates and limit length
    unique_pain_points = list(set(all_pain_points))[:10]
    unique_solutions = list(set(all_solutions))[:10]
    
    # Calculate a basic score
    relevance_ratio = (len(relevant_hn_posts) + len(relevant_reddit_posts)) / max(1, len(hn_analyses) + len(reddit_analyses))
    basic_score = min(100, int(relevance_ratio * 100))
    
    # Create platform insights
    platform_insights = [
        PlatformInsight(
            platform="HackerNews",
            insights=f"Found {len(relevant_hn_posts)} relevant posts out of {len(hn_analyses)} total"
        ),
        PlatformInsight(
            platform="Reddit",
            insights=f"Found {len(relevant_reddit_posts)} relevant posts out of {len(reddit_analyses)} total"
        )
    ]
    
    # Create a basic summary
    summary = f"Analysis found {len(relevant_hn_posts) + len(relevant_reddit_posts)} relevant posts across HackerNews and Reddit. "
    summary += f"The idea shows {basic_score}% relevance based on available data. "
    summary += "Note: This is a fallback analysis due to an error in the full analysis generation."
    
    return CombinedAnalysis(
        overall_score=basic_score,
        market_validation_summary=summary,
        key_pain_points=unique_pain_points if unique_pain_points else ["No clear pain points identified"],
        existing_solutions=unique_solutions if unique_solutions else ["No clear solutions identified"],
        market_opportunities=["Review the collected data for opportunities"],
        platform_insights=platform_insights,
        recommendations=[
            "Review the individual post analyses for more detailed insights",
            "Consider refining the business idea based on the pain points identified",
            "Try running the analysis again with more focused keywords"
        ]
    )

def create_minimal_analysis(business_idea: str, data_dir: str) -> CombinedAnalysis:
    """Create a minimal analysis from whatever checkpoint data is available.
    
    Args:
        business_idea: The business idea being validated
        data_dir: The directory containing checkpoint data
        
    Returns:
        CombinedAnalysis object with minimal analysis results
    """
    logging.info("Creating minimal analysis from available checkpoint data...")
    
    # Create a minimal analysis when all else fails
    return CombinedAnalysis(
        overall_score=10,  # Very low score since analysis is incomplete
        market_validation_summary=f"Analysis for '{business_idea}' was interrupted. This is a minimal report based on limited data.",
        key_pain_points=["Analysis incomplete - review collected data"],
        existing_solutions=["Analysis incomplete - review collected data"],
        market_opportunities=["Analysis incomplete - review collected data"],
        platform_insights=[PlatformInsight(platform="Error", insights="Analysis was interrupted")],
        recommendations=[
            f"Review the data in {data_dir} for partial insights",
            "Try running the analysis again with fewer keywords",
            "Consider breaking the analysis into smaller parts"
        ]
    )











def generate_final_analysis_cn(
    hn_analyses: List[HNPostAnalysis], 
    xhs_analyses: List[XhsPostAnalysis], 
    business_idea: str, 
    keywords: List[str]
) -> CombinedAnalysis:
    """Generate final business validation analysis from XHS
    
    Args:
        hn_analyses: List of HackerNews post analyses
        XHS_analyses: List of Reddit post analyses
        business_idea: The business idea being validated
        keywords: The keywords used for searching
        
    Returns:
        CombinedAnalysis object with final analysis results
    """
    logging.info("Generating final combined analysis...")
    
    # Prepare summaries
    total_hn_posts = len(hn_analyses)
    relevant_hn_posts = [a for a in hn_analyses if a.relevant]
    total_xhs_posts = len(xhs_analyses)
    relevant_xhs_posts = [a for a in xhs_analyses if a.relevant]
    
    prompt = f"""
    Business Idea: "{business_idea}"
    Keywords Searched: {', '.join(keywords)}
    
    Analysis Summary:

    XHS(小红书):
    - Total posts analyzed: {total_xhs_posts}
    - Relevant posts found: {len(relevant_xhs_posts)}
    
    XHS Insights:
    {chr(10).join([f"- Pain Points: {a.pain_points}, Solutions: {a.solutions_mentioned},  Sentiment: {a.sentiment}" for a in relevant_xhs_posts[:5]])}
    
    Based on this XHS(小红书) validation research, provide:
    
    1. Overall validation score (1-100) where:
       - 85+ = Strong market validation with clear demand
       - 70-84 = Good validation with some concerns
       - 50-69 = Mixed signals, needs more research
       - 30-49 = Weak validation, major concerns
       - 0-29 = Little to no validation found
    
    2. Market validation summary (2-3 sentences)
    3. Key pain points discovered across both platforms
    4. Existing solutions mentioned across both platforms
    5. Market opportunities identified
    6. Platform-specific insights as a list of objects, each with 'platform' (e.g., "xhs" ) and 'insights' (the specific insights for that platform)
    7. Specific recommendations for moving forward
    
    note:return chinese language.
    """
    
    try:
        final_analysis = generate_pydantic_json_model(
            model_class=CombinedAnalysis,
            llm_instance=llm_instance,
            prompt=prompt
        )
        
        return final_analysis
    except Exception as e:
        logging.error(f"Error generating final analysis: {e}")
        # Create a fallback analysis
        return create_fallback_analysis_cn(hn_analyses, xhs_analyses, business_idea, keywords)

def create_fallback_analysis_cn(
    hn_analyses: List[HNPostAnalysis], 
    xhs_analyses: List[RedditPostAnalysis], 
    business_idea: str, 
    keywords: List[str]
) -> CombinedAnalysis:
    """Create a simplified analysis when the full analysis generation fails.
    
    Args:
        xhs_analyses: List of XHS(小红书) post analyses
        business_idea: The business idea being validated
        keywords: The keywords used for searching
        
    Returns:
        CombinedAnalysis object with simplified analysis results
    """
    logging.info("Creating fallback analysis...")
    
    # Count relevant posts 
    relevant_xhs_posts = [a for a in xhs_analyses if a.relevant]
    
    # Collect pain points and solutions
    all_pain_points = []
    all_solutions = []
    
    
    for analysis in relevant_xhs_posts:
        all_pain_points.extend(analysis.pain_points)
        all_solutions.extend(analysis.solutions_mentioned)
    
    # Remove duplicates and limit length
    unique_pain_points = list(set(all_pain_points))[:10]
    unique_solutions = list(set(all_solutions))[:10]
    
    # Calculate a basic score
    relevance_ratio = (len(relevant_xhs_posts)) / max(1, len(hn_analyses) + len(xhs_analyses))
    basic_score = min(100, int(relevance_ratio * 100))
    
    # Create platform insights
    platform_insights = [
      
        PlatformInsight(
            platform="xhs",
            insights=f"Found {len(relevant_xhs_posts)} relevant posts out of {len(xhs_analyses)} total"
        )
    ]
    
    # Create a basic summary
    summary = f"Analysis found {len(relevant_xhs_posts)} relevant posts across xhs. "
    summary += f"The idea shows {basic_score}% relevance based on available data. "
    summary += "Note: This is a fallback analysis due to an error in the full analysis generation.note:return chinese language."
    
    return CombinedAnalysis(
        overall_score=basic_score,
        market_validation_summary=summary,
        key_pain_points=unique_pain_points if unique_pain_points else ["No clear pain points identified"],
        existing_solutions=unique_solutions if unique_solutions else ["No clear solutions identified"],
        market_opportunities=["Review the collected data for opportunities"],
        platform_insights=platform_insights,
        recommendations=[
            "Review the individual post analyses for more detailed insights",
            "Consider refining the business idea based on the pain points identified",
            "Try running the analysis again with more focused keywords"
        ]
    )

def create_minimal_analysis_cn(business_idea: str, data_dir: str) -> CombinedAnalysis:
    """Create a minimal analysis from whatever checkpoint data is available.
    
    Args:
        business_idea: The business idea being validated
        data_dir: The directory containing checkpoint data
        
    Returns:
        CombinedAnalysis object with minimal analysis results
    """
    logging.info("Creating minimal analysis from available checkpoint data...")
    
    # Create a minimal analysis when all else fails
    return CombinedAnalysis(
        overall_score=10,  # Very low score since analysis is incomplete
        market_validation_summary=f"Analysis for '{business_idea}' was interrupted. This is a minimal report based on limited data.",
        key_pain_points=["Analysis incomplete - review collected data"],
        existing_solutions=["Analysis incomplete - review collected data"],
        market_opportunities=["Analysis incomplete - review collected data"],
        platform_insights=[PlatformInsight(platform="Error", insights="Analysis was interrupted")],
        recommendations=[
            f"Review the data in {data_dir} for partial insights",
            "Try running the analysis again with fewer keywords",
            "Consider breaking the analysis into smaller parts"
        ]
    )
