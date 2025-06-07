"""
Main business idea validation functionality.  for china 中国市场的调研 基于小红书

This module provides the main entry point for validating business ideas
by scraping and analyzing data from 小红书.
"""

import os
import time
import logging
import sys

# Set default encoding for logging to UTF-8
logging.basicConfig(stream=sys.stdout, encoding='utf-8')
import traceback
from typing import List

from business_validator.config import (
    MAX_PAGES_PER_KEYWORD_HN,
    MAX_PAGES_PER_KEYWORD_REDDIT,
    MAX_POSTS_TO_ANALYZE,
    HN_DELAY,
    REDDIT_DELAY,
    CHECKPOINT_INTERVAL
)
from business_validator.models import XhsPostAnalysis 
from business_validator.models import CombinedAnalysis
from business_validator.utils.environment import setup_environment, save_checkpoint, load_checkpoint
from business_validator.utils.reporting import print_validation_report

from business_validator.analyzers.keyword_generator import generate_keywords_cn
from business_validator.analyzers.xhs_analyzer import analyze_xhs_post 
from business_validator.analyzers.combined_analyzer import (
    generate_final_analysis_cn,
    create_fallback_analysis_cn,
    create_minimal_analysis_cn
)

from business_validator.scrapers.xhs import (
    scrape_xhs_search,
    scrape_xhs_post_comments
)

def validate_business_idea_cn(business_idea: str) -> CombinedAnalysis:
    """Main function to validate a business idea using xhs
    
    Args:
        business_idea: The business idea to validate
        
    Returns:
        CombinedAnalysis object with validation results
    """
    # Setup environment for this run
    env = setup_environment(business_idea)
    run_id = env["run_id"]
    data_dir = env["data_dir"]
    
    logging.info(f"[STARTING] Validating business idea: {business_idea}")
    
    try:
        # Step 1: Generate keywords
        logging.info("\n[STEP 1] Generating search keywords...")
        keywords = generate_keywords_cn(business_idea)
        logging.info(f"Generated keywords: {keywords}")
        
        # Save keywords checkpoint
        save_checkpoint({"keywords": keywords, "business_idea": business_idea}, 
                        "01_keywords.json", data_dir)
        # TODO 这里在用户界面展示 keywords ，在validator_cn.py 中增加回调函数参数来传递关键词数据。
         
        
        # Step 3: Scrape xhs
        logging.info("\n[STEP 3] Searching XHS...")
        xhs_posts = []
        for keyword in keywords:
            logging.info(f"   Searching XHS for: '{keyword}'")
            
            for page in range(2):
                page =page +1
                logging.info(f"      Scraping page {page}...")
                results = scrape_xhs_search(keyword, page)
                
                if not results['posts']:
                    logging.info(f"      No more results on page {page}")
                    break
                    
                xhs_posts.extend([post for post in results['posts'] if post not in xhs_posts])
                
                # Save checkpoint periodically
                if len(xhs_posts) % CHECKPOINT_INTERVAL == 0:
                    save_checkpoint({"xhs_posts": xhs_posts}, 
                                    f"03_xhs_posts_partial_{len(xhs_posts)}.json", data_dir)
                
                time.sleep(REDDIT_DELAY)
        
        logging.info(f"   [STATS] Total xhs  posts collected: {len(xhs_posts)}")
        
        # Save xhs posts checkpoint
        save_checkpoint({"xhs_posts": xhs_posts}, "03_xhs_posts_complete.json", data_dir)
        
        # Step 4: Scrape xhs comments for top posts
        logging.info(f"\n[STEP 4] Scraping comments for top {MAX_POSTS_TO_ANALYZE} xhs posts...")
        xhs_posts_with_comments = []
        
        # Sort by liked_count and take top posts
        # xhs_posts.sort(key=lambda x: x.get('liked_count', 0), reverse=True) # 按点赞数排序，先不要，默认是更相关性
        top_xhs_posts = xhs_posts[:MAX_POSTS_TO_ANALYZE]
        
        for i, post in enumerate(top_xhs_posts):
            if post and 'title' in post:
                try:
                    msg = f"   Scraping comments {i+1}/{len(top_xhs_posts)}: {post['title'][:50]}..."
                    logging.info(msg)
                except Exception:
                    logging.info(f"   Scraping comments {i+1}/{len(top_xhs_posts)}")
            else:
                try:
                    msg = f"   Skipping invalid post at index {i}"
                    logging.warning(msg)
                except Exception:
                    logging.warning(f"   Skipping invalid post at index {i}")
                continue
            comments = scrape_xhs_post_comments(post['note_id'])
            post['comments_data'] = comments
            xhs_posts_with_comments.append(post)
            
            # Save checkpoint periodically
            if (i+1) % CHECKPOINT_INTERVAL == 0 or i == len(top_xhs_posts) - 1:
                save_checkpoint({"xhs_posts_with_comments": xhs_posts_with_comments}, 
                                f"04_xhs_comments_partial_{i+1}.json", data_dir)
            
            time.sleep(REDDIT_DELAY)
        
        # Save xhs posts with comments checkpoint
        save_checkpoint({"xhs_posts_with_comments": xhs_posts_with_comments}, 
                        "04_xhs_comments_complete.json", data_dir)
        
      
        # Step 6: Analyze xhs posts
        logging.info("\n[STEP 6] Analyzing xhs posts...")
        xhs_analyses = []
        for i, post in enumerate(xhs_posts_with_comments):
            if post is None:
                logging.warning(f"Skipping None post at index {i}")
                continue
            
            # Safely get title with fallback
            title = post.get('title', 'No Title')
            if title is None:
                title = 'No Title'
            safe_title = title[:50] if title else 'No Title'
            logging.info(f"   Analyzing xhs post {i+1}/{len(xhs_posts_with_comments)}: {safe_title.encode('unicode-escape').decode('ascii')}...")
            try:
                comments = post.get('comments_data', [])
                analysis = analyze_xhs_post(post, comments, business_idea)
                if isinstance(analysis, XhsPostAnalysis):
                    xhs_analyses.append(analysis)
                else:
                    logging.error(f"Invalid analysis type for post {i+1}: {type(analysis)}")
                
                # Save checkpoint periodically
                if (i+1) % CHECKPOINT_INTERVAL == 0 or i == len(xhs_posts_with_comments) - 1:
                    save_checkpoint([a.dict() for a in xhs_analyses], 
                                    f"06_xhs_analyses_partial_{i+1}.json", data_dir)
                
            except Exception as e:
                logging.error(f"Error analyzing xhs post {i+1}: {e}")
                logging.error(traceback.format_exc())
                # Continue with other posts
            
            time.sleep(0.5)
        
        # Save xhs analyses checkpoint
        save_checkpoint([a.dict() for a in xhs_analyses], "06_xhs_analyses_complete.json", data_dir)
        
        # Step 7: Generate final analysis
        logging.info("\n[STEP 7] Generating combined validation report...")
        try:
            final_analysis = generate_final_analysis_cn([], xhs_analyses, business_idea, keywords)
            
            # Save final analysis
            if hasattr(final_analysis, 'dict'):
                save_checkpoint(final_analysis.dict(), "07_final_analysis.json", data_dir)
            else:
                logging.warning("Final analysis is not a CombinedAnalysis object, saving as string")
                save_checkpoint({"analysis": str(final_analysis)}, "07_final_analysis.json", data_dir)
            
        except Exception as e:
            logging.error(f"Error generating final analysis: {e}")
            logging.error(traceback.format_exc())
            
            # Create a simplified fallback analysis
            logging.info("Creating fallback analysis from collected data...")
            final_analysis = create_fallback_analysis_cn([], xhs_analyses, business_idea, keywords)
            
            # Save fallback analysis
            save_checkpoint(final_analysis.dict(), "07_fallback_analysis.json", data_dir)
        
        return final_analysis
        
    except Exception as e:
        logging.error(f"Unexpected error in validation process: {e}")
        logging.error(traceback.format_exc())
        
        # Try to create a minimal analysis from whatever data we have
        try:
            return create_minimal_analysis_cn(business_idea, data_dir)
        except:
            # If all else fails, return an empty analysis
            return CombinedAnalysis(
                overall_score=0,
                market_validation_summary="Analysis failed due to an error. Please check the logs.",
                key_pain_points=["Analysis incomplete"],
                existing_solutions=["Analysis incomplete"],
                market_opportunities=["Analysis incomplete"],
                platform_insights={"error": "Analysis failed"},
                recommendations=["Review collected data manually", "Try again with fewer keywords"]
            )

if __name__ == "__main__":
    # Example usage
    business_idea = input("Enter your business idea: ")
    
    # Validate the idea
    analysis = validate_business_idea(business_idea)
    
    # Print the report
    print_validation_report(analysis, business_idea)
    
    # Show where the data is saved
    data_dir = os.path.join("validation_data", f"{business_idea}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    print(f"\nAll collected data and analysis results have been saved to the '{data_dir}' directory.")
    print("You can review these files even if the analysis was incomplete.")
