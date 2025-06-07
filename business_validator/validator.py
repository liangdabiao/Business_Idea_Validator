"""
Main business idea validation functionality.

This module provides the main entry point for validating business ideas
by scraping and analyzing data from HackerNews and Reddit.
"""

import time
import logging
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
from business_validator.models import HNPostAnalysis
from business_validator.models import CombinedAnalysis
from business_validator.utils.environment import setup_environment, save_checkpoint, load_checkpoint
from business_validator.utils.reporting import print_validation_report

from business_validator.analyzers.keyword_generator import generate_keywords
from business_validator.analyzers.hackernews_analyzer import analyze_hn_post
from business_validator.analyzers.reddit_analyzer import analyze_reddit_post
from business_validator.analyzers.combined_analyzer import (
    generate_final_analysis,
    create_fallback_analysis,
    create_minimal_analysis
)

from business_validator.scrapers.hackernews import scrape_hackernews
from business_validator.scrapers.reddit import (
    scrape_reddit_search,
    scrape_reddit_post_comments
)

def validate_business_idea(business_idea: str) -> CombinedAnalysis:
    """Main function to validate a business idea using HackerNews and Reddit.
    
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
        keywords = generate_keywords(business_idea)
        logging.info(f"Generated keywords: {keywords}")
        
        # Save keywords checkpoint
        save_checkpoint({"keywords": keywords, "business_idea": business_idea}, 
                        "01_keywords.json", data_dir)
        
        # Step 2: Scrape HackerNews
        logging.info("\n[STEP 2] Searching HackerNews...")
        hn_posts = []
        for keyword in keywords:
            logging.info(f"   Searching HN for: '{keyword}'")
            
            for page in range(MAX_PAGES_PER_KEYWORD_HN):
                logging.info(f"      Scraping page {page}...")
                results = scrape_hackernews(keyword, page)
                
                if not results['posts']:
                    logging.info(f"      No more results on page {page}")
                    break
                    
                hn_posts.extend(results['posts'])
                
                # Save checkpoint periodically
                if len(hn_posts) % CHECKPOINT_INTERVAL == 0:
                    save_checkpoint({"hn_posts": hn_posts}, 
                                    f"02_hn_posts_partial_{len(hn_posts)}.json", data_dir)
                
                time.sleep(HN_DELAY)
        
        logging.info(f"   [STATS] Total HN posts collected: {len(hn_posts)}")
        
        # Save HN posts checkpoint
        save_checkpoint({"hn_posts": hn_posts}, "02_hn_posts_complete.json", data_dir)
        
        # Step 3: Scrape Reddit
        logging.info("\n[STEP 3] Searching Reddit...")
        reddit_posts = []
        for keyword in keywords:
            logging.info(f"   Searching Reddit for: '{keyword}'")
            
            for page in range(MAX_PAGES_PER_KEYWORD_REDDIT):
                logging.info(f"      Scraping page {page}...")
                results = scrape_reddit_search(keyword, page)
                
                if not results['posts']:
                    logging.info(f"      No more results on page {page}")
                    break
                    
                reddit_posts.extend(results['posts'])
                
                # Save checkpoint periodically
                if len(reddit_posts) % CHECKPOINT_INTERVAL == 0:
                    save_checkpoint({"reddit_posts": reddit_posts}, 
                                    f"03_reddit_posts_partial_{len(reddit_posts)}.json", data_dir)
                
                time.sleep(REDDIT_DELAY)
        
        logging.info(f"   [STATS] Total Reddit posts collected: {len(reddit_posts)}")
        
        # Save Reddit posts checkpoint
        save_checkpoint({"reddit_posts": reddit_posts}, "03_reddit_posts_complete.json", data_dir)
        
        # Step 4: Scrape Reddit comments for top posts
        logging.info(f"\n[STEP 4] Scraping comments for top {MAX_POSTS_TO_ANALYZE} Reddit posts...")
        reddit_posts_with_comments = []
        
        # Sort by upvotes and take top posts
        reddit_posts.sort(key=lambda x: x.get('upvotes', 0), reverse=True)
        top_reddit_posts = reddit_posts[:MAX_POSTS_TO_ANALYZE]
        
        for i, post in enumerate(top_reddit_posts):
            logging.info(f"   Scraping comments {i+1}/{len(top_reddit_posts)}: {post['title'][:50]}...")
            comments = scrape_reddit_post_comments(post['url'])
            post['comments_data'] = comments
            reddit_posts_with_comments.append(post)
            
            # Save checkpoint periodically
            if (i+1) % CHECKPOINT_INTERVAL == 0 or i == len(top_reddit_posts) - 1:
                save_checkpoint({"reddit_posts_with_comments": reddit_posts_with_comments}, 
                                f"04_reddit_comments_partial_{i+1}.json", data_dir)
            
            time.sleep(REDDIT_DELAY)
        
        # Save Reddit posts with comments checkpoint
        save_checkpoint({"reddit_posts_with_comments": reddit_posts_with_comments}, 
                        "04_reddit_comments_complete.json", data_dir)
        
        # Step 5: Analyze HackerNews posts
        logging.info("\n[STEP 5] Analyzing HackerNews posts...")
        hn_analyses = []
        for i, post in enumerate(hn_posts):
            logging.info(f"   Analyzing HN post {i+1}/{len(hn_posts)}: {post['title'][:50]}...")
            try:
                analysis = analyze_hn_post(post, business_idea)
                if isinstance(analysis, HNPostAnalysis):
                    hn_analyses.append(analysis)
                else:
                    logging.error(f"Invalid analysis type for HN post {i+1}: {type(analysis)}")
                
                # Save checkpoint periodically
                if (i+1) % CHECKPOINT_INTERVAL == 0 or i == len(hn_posts) - 1:
                    save_checkpoint([a.dict() for a in hn_analyses], 
                                    f"05_hn_analyses_partial_{i+1}.json", data_dir)
                
            except Exception as e:
                logging.error(f"Error analyzing HN post {i+1}: {e}")
                logging.error(traceback.format_exc())
                # Continue with other posts
            
            time.sleep(0.5)
        
        # Save HN analyses checkpoint
        save_checkpoint([a.dict() for a in hn_analyses], "05_hn_analyses_complete.json", data_dir)
        
        # Step 6: Analyze Reddit posts
        logging.info("\n[STEP 6] Analyzing Reddit posts...")
        reddit_analyses = []
        for i, post in enumerate(reddit_posts_with_comments):
            logging.info(f"   Analyzing Reddit post {i+1}/{len(reddit_posts_with_comments)}: {post['title'][:50]}...")
            try:
                comments = post.get('comments_data', [])
                analysis = analyze_reddit_post(post, comments, business_idea)
                if isinstance(analysis, RedditPostAnalysis):
                    reddit_analyses.append(analysis)
                else:
                    logging.error(f"Invalid analysis type for post {i+1}: {type(analysis)}")
                
                # Save checkpoint periodically
                if (i+1) % CHECKPOINT_INTERVAL == 0 or i == len(reddit_posts_with_comments) - 1:
                    save_checkpoint([a.dict() for a in reddit_analyses], 
                                    f"06_reddit_analyses_partial_{i+1}.json", data_dir)
                
            except Exception as e:
                logging.error(f"Error analyzing Reddit post {i+1}: {e}")
                logging.error(traceback.format_exc())
                # Continue with other posts
            
            time.sleep(0.5)
        
        # Save Reddit analyses checkpoint
        save_checkpoint([a.dict() for a in reddit_analyses], "06_reddit_analyses_complete.json", data_dir)
        
        # Step 7: Generate final analysis
        logging.info("\n[STEP 7] Generating combined validation report...")
        try:
            final_analysis = generate_final_analysis(hn_analyses, reddit_analyses, business_idea, keywords)
            
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
            final_analysis = create_fallback_analysis(hn_analyses, reddit_analyses, business_idea, keywords)
            
            # Save fallback analysis
            save_checkpoint(final_analysis.dict(), "07_fallback_analysis.json", data_dir)
        
        return final_analysis
        
    except Exception as e:
        logging.error(f"Unexpected error in validation process: {e}")
        logging.error(traceback.format_exc())
        
        # Try to create a minimal analysis from whatever data we have
        try:
            return create_minimal_analysis(business_idea, data_dir)
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
