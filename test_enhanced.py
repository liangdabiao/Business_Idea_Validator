from typing import List
from pydantic import BaseModel
import requests
import time
import json
import datetime
import re
from pathlib import Path
import math
from SimplerLLM.langauge.llm import LLM, LLMProvider
from SimplerLLM.langauge.llm_addons import generate_pydantic_json_model

### 测试调试使用！！！

llm_instance = LLM.create(provider=LLMProvider.OPENAI,model_name="gpt-4o")


# ========== CONFIG ==========
SCRAPER_API_KEY = 'eaf276899b491374208456e3sb8c58'
OPENAI_API_KEY = 'fk217050-KDsz3LX9J2msZ6DATB3qMgwe'

# Scoring weights
SCORE_WEIGHTS = {
    "pain_points": 0.35,      # 35% weight for pain points
    "excitement_signals": 0.30, # 30% weight for excitement signals
    "competitors": 0.20,      # 20% weight for competitors
    "keyword_relevance": 0.15  # 15% weight for keyword relevance
}

# Minimum relevance threshold (0-10) for counting items
MIN_RELEVANCE_THRESHOLD = 5

# Validation thresholds
VALIDATION_THRESHOLDS = {
    "strongly_validated": 85,  # Was 80
    "validated": 70,           # Was 65
    "partially_validated": 55, # Was 50
    "weakly_validated": 40     # Was 35
}

NUM_PAGES = 3  # how many pages per site to fetch (was 2)
NUM_KEYWORDS = 5  # number of keywords to generate
SOURCES = {
    "Reddit": "https://www.reddit.com/search/?q={query}&page={page}",
    "ProductHunt": "https://www.producthunt.com/search?q={query}&page={page}",
    #"HackerNews": "https://hn.algolia.com/?q={query}&page={page}"
}


# Base directory for logs
LOGS_DIR = Path("logs")

# ========== KEYWORD GENERATION ==========
class KeywordModel(BaseModel):
    keywords: List[str]

def generate_keywords(business_idea, num_keywords=NUM_KEYWORDS):

    """
    Generate relevant keywords for a business idea using OpenAI
    
    Args:
        business_idea (str): The main business idea
        num_keywords (int): Number of keywords to generate
        
    Returns:
        list: List of generated keywords
    """
    print(f"Generating {num_keywords} keywords for: {business_idea}")
    
    prompt = f"""
For the business idea: "{business_idea}"

Generate {num_keywords} specific search keywords that would help validate this idea.
These should be phrases people might use when discussing pain points, needs, or solutions related to this idea.


"""
    
    try:
        response_model = generate_pydantic_json_model(model_class=KeywordModel,
                                                      llm_instance=llm_instance,
                                                      prompt=prompt)
  
      
        keywords = response_model.keywords
        
        # Always include the original business idea as a keyword
        if business_idea not in keywords:
            keywords.append(business_idea)
            
        return keywords
    except Exception as e:
        print(f"Error generating keywords 1: {e}")
        # Return the original business idea as a fallback
        return [business_idea]
    


# ========== LOGGING SETUP ==========
def setup_master_log_directory(business_idea):
    """
    Create master directory for all keyword results
    
    Args:
        business_idea (str): The main business idea
        
    Returns:
        Path: Path to the master log directory
    """
    # Sanitize business idea for use as directory name
    safe_idea = re.sub(r'[^\w\s-]', '', business_idea).strip().replace(' ', '_').lower()
    
    # Truncate long names to a reasonable length (e.g., 30 characters)
    if len(safe_idea) > 30:
        safe_idea = safe_idea[:30]
    
    # Create timestamp for this run
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create master directory
    master_dir = LOGS_DIR / safe_idea / timestamp
    master_dir.mkdir(parents=True, exist_ok=True)
    
    return master_dir

def setup_keyword_log_directories(keyword, master_log_dir):
    """
    Set up log directories for a specific keyword
    
    Args:
        keyword (str): The keyword
        master_log_dir (Path): Path to the master log directory
        
    Returns:
        dict: Dictionary containing paths to different log directories
    """
    # Sanitize keyword for use as directory name
    safe_keyword = re.sub(r'[^\w\s-]', '', keyword).strip().replace(' ', '_').lower()
    
    # Truncate long keywords to a reasonable length
    if len(safe_keyword) > 30:
        safe_keyword = safe_keyword[:30]
    
    # Create keyword directory
    keyword_dir = master_log_dir / "keywords" / safe_keyword
    
    # Create subdirectories
    raw_dir = keyword_dir / "raw"
    analyzed_dir = keyword_dir / "analyzed"
    reports_dir = keyword_dir / "reports"
    
    # Create all directories
    for directory in [raw_dir, analyzed_dir, reports_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    
    return {
        "keyword_dir": keyword_dir,
        "raw_dir": raw_dir,
        "analyzed_dir": analyzed_dir,
        "reports_dir": reports_dir
    }

def save_to_file(content, file_path, is_json=False):
    """
    Save content to a file
    
    Args:
        content: The content to save
        file_path (Path): The path to save the file to
        is_json (bool): Whether the content is JSON and should be formatted
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            if is_json:
                json.dump(content, f, indent=2, ensure_ascii=False)
            else:
                f.write(content)
        print(f"Saved: {file_path}")
    except Exception as e:
        print(f"Error saving to {file_path}: {e}")

# ========== FETCHER ==========
def fetch_page(url, log_dirs=None, source_name=None, page_num=None):
    """
    Fetch a page from a URL and optionally log the raw content
    
    Args:
        url (str): The URL to fetch
        log_dirs (dict, optional): Log directory paths
        source_name (str, optional): Name of the source being fetched
        page_num (int, optional): Page number being fetched
        
    Returns:
        str: The page content or None if there was an error
    """
    params = {
        'api_key': SCRAPER_API_KEY,
        'url': url,
        'output_format': 'text'
    }
    
    try:
        response = requests.get('https://api.scraperapi.com/', params=params, timeout=20)
        
        if response.status_code == 200:
            content = response.text
            
            # Log raw content if logging is enabled
            if log_dirs and source_name and page_num is not None:
                file_name = f"{source_name}_page{page_num}.txt"
                file_path = log_dirs["raw_dir"] / file_name
                save_to_file(content, file_path)
                
            return content
        else:
            print(f"Error fetching {url}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception while fetching {url}: {e}")
        return None

# ========== ANALYZER ==========
class TextWithRelevance(BaseModel):
    text: str
    relevance: int

class BusinessIdeaAnalysis(BaseModel):
    pain_points: List[TextWithRelevance]
    excitement_signals: List[TextWithRelevance]
    mentions_of_competitors: List[str]
    notable_quotes: List[str]
    red_flags: List[str]
    coherence_score: int

def analyze_text_with_openai(text, keyword, log_dirs=None, source_name=None, page_num=None):
    print(f"analyze_text_with_openai for page_num: {page_num}")
    #print(text)
    print(keyword)
    """
    Analyze text using OpenAI and optionally log the results
    
    Args:
        text (str): The text to analyze
        keyword (str): The keyword being researched
        log_dirs (dict, optional): Log directory paths
        source_name (str, optional): Name of the source being analyzed
        page_num (int, optional): Page number being analyzed
        
    Returns:
        dict: The analysis results
    """
    prompt = f"""
You are a business idea validator.  
Analyze the following text in the context of the keyword: "{keyword}"

Find:
1. Pain points people mention
2. Excitement signals (desires, positive needs)
3. Competitors mentioned
4. Notable quotes (max 2 short quotes)

For each pain point and excitement signal, rate its relevance to the business idea on a scale of 0-10, 
where 0 means completely irrelevant and 10 means highly relevant and specific to the business idea.

Also identify any contradictions or red flags in the data that might indicate the business idea is not viable.


The coherence_score (0-10) represents how consistent and coherent the findings are, with 10 being highly coherent 
and 0 indicating contradictory or nonsensical findings.

Text to analyze:
{text}
"""

    try:
        response_model = generate_pydantic_json_model(model_class=BusinessIdeaAnalysis,
                                                      llm_instance=llm_instance,
                                                      prompt=prompt)
        print("20")
        # 确保返回的是模型实例而非字典
        if not isinstance(response_model, (BusinessIdeaAnalysis, dict)):
            print(f"Unexpected response  : {response_model}")
            raise ValueError(f"Unexpected response type: {type(response_model)}")
        print("21")
        if isinstance(response_model, dict):
            response_model = BusinessIdeaAnalysis(**response_model)
        print("22")  
        # Log analyzed results if logging is enabled
        if log_dirs and source_name and page_num is not None:
            file_name = f"{source_name}_page{page_num}.json"
            file_path = log_dirs["analyzed_dir"] / file_name
            print("23")
            # Add metadata to the logged result
            log_result = {
                "metadata": {
                    "source": source_name,
                    "page": page_num,
                    "keyword": keyword,
                    "timestamp": datetime.datetime.now().isoformat()
                },
                "analysis": response_model.model_dump() if hasattr(response_model, 'model_dump') else response_model
            }
            print("24")
            save_to_file(log_result, file_path, is_json=True)
        print("23")    
        return response_model.model_dump()
    except Exception as e:
        print(f"Error during OpenAI analysis: {e}")
        return {
            "pain_points": [],
            "excitement_signals": [],
            "mentions_of_competitors": [],
            "notable_quotes": []
        }

# ========== MERGER ==========
def merge_results(all_results):
    """
    Merge multiple analysis results into a single report
    
    Args:
        all_results (list): List of analysis results to merge
        
    Returns:
        dict: The merged results
    """
    final = {
        "pain_points": [],
        "excitement_signals": [],
        "mentions_of_competitors": [],
        "notable_quotes": [],
        "red_flags": [],
        "coherence_scores": []
    }
    
    for res in all_results:
        # Handle pain points and excitement signals with relevance scores
        if "pain_points" in res:
            final["pain_points"].extend(res["pain_points"])
        
        if "excitement_signals" in res:
            final["excitement_signals"].extend(res["excitement_signals"])
        
        # Handle simple list fields
        if "mentions_of_competitors" in res:
            final["mentions_of_competitors"].extend(res.get("mentions_of_competitors", []))
        
        if "notable_quotes" in res:
            final["notable_quotes"].extend(res.get("notable_quotes", []))
        
        # Handle red flags
        if "red_flags" in res:
            final["red_flags"].extend(res.get("red_flags", []))
        
        # Track coherence scores
        if "coherence_score" in res:
            final["coherence_scores"].append(res.get("coherence_score", 5))
    
    # Deduplicate simple lists (competitors and red flags)
    final["mentions_of_competitors"] = list(set(final["mentions_of_competitors"]))
    final["red_flags"] = list(set(final["red_flags"]))
    
    # Deduplicate notable quotes (similar to pain points and excitement signals)
    deduplicated_quotes = {}
    for item in final["notable_quotes"]:
        if isinstance(item, dict) and "text" in item:
            text = item["text"]
            if text not in deduplicated_quotes:
                deduplicated_quotes[text] = item
        elif isinstance(item, str):  # Handle old format for backward compatibility
            if item not in deduplicated_quotes:
                deduplicated_quotes[item] = {"text": item}
    
    # Convert back to list
    final["notable_quotes"] = list(deduplicated_quotes.values())
    
    # For pain points and excitement signals, we need to deduplicate based on text content
    # while preserving the relevance scores
    deduplicated_pain_points = {}
    for item in final["pain_points"]:
        if isinstance(item, dict) and "text" in item and "relevance" in item:
            text = item["text"]
            relevance = item["relevance"]
            
            if text not in deduplicated_pain_points or relevance > deduplicated_pain_points[text]["relevance"]:
                deduplicated_pain_points[text] = item
        elif isinstance(item, str):  # Handle old format for backward compatibility
            if item not in deduplicated_pain_points:
                deduplicated_pain_points[item] = {"text": item, "relevance": 5}  # Default relevance
    
    deduplicated_excitement = {}
    for item in final["excitement_signals"]:
        if isinstance(item, dict) and "text" in item and "relevance" in item:
            text = item["text"]
            relevance = item["relevance"]
            
            if text not in deduplicated_excitement or relevance > deduplicated_excitement[text]["relevance"]:
                deduplicated_excitement[text] = item
        elif isinstance(item, str):  # Handle old format for backward compatibility
            if item not in deduplicated_excitement:
                deduplicated_excitement[item] = {"text": item, "relevance": 5}  # Default relevance
    
    # Convert back to lists
    final["pain_points"] = list(deduplicated_pain_points.values())
    final["excitement_signals"] = list(deduplicated_excitement.values())
    
    # Calculate average coherence score
    if final["coherence_scores"]:
        final["coherence_score"] = sum(final["coherence_scores"]) / len(final["coherence_scores"])
    else:
        final["coherence_score"] = 5  # Default middle value
    
    # Remove the list of scores
    del final["coherence_scores"]
    
    return final

def process_keyword(keyword, master_log_dir):
    """
    Process a single keyword through the scraping and analysis pipeline
    
    Args:
        keyword (str): The keyword to process
        master_log_dir (Path): Path to the master log directory
        
    Returns:
        dict: The keyword results
    """
    print(f"\n{'='*50}")
    print(f"Processing keyword: {keyword}")
    print(f"{'='*50}")
    
    # Set up logging directories for this keyword
    log_dirs = setup_keyword_log_directories(keyword, master_log_dir)
    
    # Save keyword metadata
    keyword_metadata = {
        "keyword": keyword,
        "timestamp": datetime.datetime.now().isoformat(),
        "sources": list(SOURCES.keys()),
        "pages_per_source": NUM_PAGES
    }
    metadata_path = log_dirs["keyword_dir"] / "keyword_metadata.json"
    save_to_file(keyword_metadata, metadata_path, is_json=True)
    
    all_page_results = []
    source_results = {}  # To track results by source

    for source_name, url_template in SOURCES.items():
        print(f"\nScraping {source_name} for '{keyword}'...")
        source_results[source_name] = []
        
        for page in range(1, NUM_PAGES + 1):
            url = url_template.format(query=keyword.replace(' ', '+'), page=page)
            page_text = fetch_page(url, log_dirs, source_name, page)
            
            if page_text:
                print(f"Analyzing {source_name} page {page} for '{keyword}'...")
                page_result = analyze_text_with_openai(page_text, keyword, log_dirs, source_name, page)
                all_page_results.append(page_result)
                source_results[source_name].append(page_result)
                time.sleep(1)  # be nice, avoid overloading OpenAI or ScraperAPI

    # Merge results for this keyword
    keyword_report = merge_results(all_page_results)
    
    # Save keyword report
    keyword_report_with_metadata = {
        "metadata": {
            "keyword": keyword,
            "timestamp": datetime.datetime.now().isoformat(),
            "sources": list(SOURCES.keys()),
            "pages_per_source": NUM_PAGES
        },
        "results": keyword_report,
        "source_results": source_results
    }
    
    report_path = log_dirs["reports_dir"] / "keyword_report.json"
    save_to_file(keyword_report_with_metadata, report_path, is_json=True)
    
    return keyword_report

def generate_aggregated_report(business_idea, keywords, all_keyword_results, master_log_dir):
    """
    Generate an aggregated report across all keywords
    
    Args:
        business_idea (str): The main business idea
        keywords (list): List of keywords used
        all_keyword_results (dict): Dictionary of results for each keyword
        master_log_dir (Path): Path to the master log directory
        
    Returns:
        dict: The aggregated report
    """
    print("\nGenerating aggregated report...")
    
    # Merge all keyword results
    aggregated_results = {
        "pain_points": [],
        "excitement_signals": [],
        "mentions_of_competitors": [],
        "notable_quotes": [],
        "red_flags": [],
        "coherence_scores": []
    }
    
    for keyword, results in all_keyword_results.items():
        # Handle pain points and excitement signals with relevance scores
        if "pain_points" in results:
            aggregated_results["pain_points"].extend(results["pain_points"])
        
        if "excitement_signals" in results:
            aggregated_results["excitement_signals"].extend(results["excitement_signals"])
        
        # Handle simple list fields
        if "mentions_of_competitors" in results:
            aggregated_results["mentions_of_competitors"].extend(results.get("mentions_of_competitors", []))
        
        if "notable_quotes" in results:
            aggregated_results["notable_quotes"].extend(results.get("notable_quotes", []))
        
        # Handle red flags
        if "red_flags" in results:
            aggregated_results["red_flags"].extend(results.get("red_flags", []))
        
        # Track coherence scores
        if "coherence_score" in results:
            aggregated_results["coherence_scores"].append(results.get("coherence_score", 5))
    
    # Deduplicate simple lists (competitors and red flags)
    aggregated_results["mentions_of_competitors"] = list(set(aggregated_results["mentions_of_competitors"]))
    aggregated_results["red_flags"] = list(set(aggregated_results["red_flags"]))
    
    # Deduplicate notable quotes (similar to pain points and excitement signals)
    deduplicated_quotes = {}
    for item in aggregated_results["notable_quotes"]:
        if isinstance(item, dict) and "text" in item:
            text = item["text"]
            if text not in deduplicated_quotes:
                deduplicated_quotes[text] = item
        elif isinstance(item, str):  # Handle old format for backward compatibility
            if item not in deduplicated_quotes:
                deduplicated_quotes[item] = {"text": item}
    
    # Convert back to list
    aggregated_results["notable_quotes"] = list(deduplicated_quotes.values())
    
    # For pain points and excitement signals, we need to deduplicate based on text content
    # while preserving the relevance scores
    deduplicated_pain_points = {}
    for item in aggregated_results["pain_points"]:
        if isinstance(item, dict) and "text" in item and "relevance" in item:
            text = item["text"]
            relevance = item["relevance"]
            
            if text not in deduplicated_pain_points or relevance > deduplicated_pain_points[text]["relevance"]:
                deduplicated_pain_points[text] = item
        elif isinstance(item, str):  # Handle old format for backward compatibility
            if item not in deduplicated_pain_points:
                deduplicated_pain_points[item] = {"text": item, "relevance": 5}  # Default relevance
    
    deduplicated_excitement = {}
    for item in aggregated_results["excitement_signals"]:
        if isinstance(item, dict) and "text" in item and "relevance" in item:
            text = item["text"]
            relevance = item["relevance"]
            
            if text not in deduplicated_excitement or relevance > deduplicated_excitement[text]["relevance"]:
                deduplicated_excitement[text] = item
        elif isinstance(item, str):  # Handle old format for backward compatibility
            if item not in deduplicated_excitement:
                deduplicated_excitement[item] = {"text": item, "relevance": 5}  # Default relevance
    
    # Convert back to lists
    aggregated_results["pain_points"] = list(deduplicated_pain_points.values())
    aggregated_results["excitement_signals"] = list(deduplicated_excitement.values())
    
    # Calculate average coherence score
    if aggregated_results["coherence_scores"]:
        aggregated_results["coherence_score"] = sum(aggregated_results["coherence_scores"]) / len(aggregated_results["coherence_scores"])
    else:
        aggregated_results["coherence_score"] = 5  # Default middle value
    
    # Remove the list of scores
    del aggregated_results["coherence_scores"]
    
    # Create final report
    final_report = {
        "metadata": {
            "business_idea": business_idea,
            "timestamp": datetime.datetime.now().isoformat(),
            "keywords": keywords,
            "sources": list(SOURCES.keys()),
            "pages_per_source": NUM_PAGES
        },
        "aggregated_results": aggregated_results,
        "keyword_results": all_keyword_results
    }
    
    # Save final report
    final_report_path = master_log_dir / "final_report.json"
    save_to_file(final_report, final_report_path, is_json=True)
    
    return final_report

# ========== SCORING AND SUMMARY ==========
def calculate_business_idea_scores(final_report):
    """
    Calculate scores for the business idea based on the validation results
    
    Args:
        final_report (dict): The final aggregated report
        
    Returns:
        dict: Dictionary containing various scores
    """
    print("\nCalculating business idea scores...")
    
    aggregated = final_report["aggregated_results"]
    keyword_results = final_report["keyword_results"]
    keywords = final_report["metadata"]["keywords"]
    
    # Filter items by relevance threshold
    relevant_pain_points = []
    for item in aggregated.get("pain_points", []):
        if isinstance(item, dict) and "relevance" in item and item["relevance"] >= MIN_RELEVANCE_THRESHOLD:
            relevant_pain_points.append(item)
        elif isinstance(item, str):  # Handle old format
            relevant_pain_points.append({"text": item, "relevance": 5})
    
    relevant_excitement = []
    for item in aggregated.get("excitement_signals", []):
        if isinstance(item, dict) and "relevance" in item and item["relevance"] >= MIN_RELEVANCE_THRESHOLD:
            relevant_excitement.append(item)
        elif isinstance(item, str):  # Handle old format
            relevant_excitement.append({"text": item, "relevance": 5})
    
    # Count items in each category
    num_pain_points = len(relevant_pain_points)
    num_excitement = len(relevant_excitement)
    num_competitors = len(aggregated.get("mentions_of_competitors", []))
    num_red_flags = len(aggregated.get("red_flags", []))
    
    # Calculate average relevance scores
    avg_pain_relevance = 0
    if relevant_pain_points:
        avg_pain_relevance = sum(item["relevance"] for item in relevant_pain_points) / len(relevant_pain_points)
    
    avg_excitement_relevance = 0
    if relevant_excitement:
        avg_excitement_relevance = sum(item["relevance"] for item in relevant_excitement) / len(relevant_excitement)
    
    # Get coherence score
    coherence_score = aggregated.get("coherence_score", 5)
    
    # Calculate keyword relevance score
    keyword_relevance = 0
    for keyword in keywords:
        # Calculate how many results each keyword found
        results = keyword_results.get(keyword, {})
        
        # Count relevant pain points and excitement signals
        keyword_pain = 0
        for item in results.get("pain_points", []):
            if isinstance(item, dict) and "relevance" in item and item["relevance"] >= MIN_RELEVANCE_THRESHOLD:
                keyword_pain += 1
            elif isinstance(item, str):  # Handle old format
                keyword_pain += 1
        
        keyword_excitement = 0
        for item in results.get("excitement_signals", []):
            if isinstance(item, dict) and "relevance" in item and item["relevance"] >= MIN_RELEVANCE_THRESHOLD:
                keyword_excitement += 1
            elif isinstance(item, str):  # Handle old format
                keyword_excitement += 1
        
        keyword_competitors = len(results.get("mentions_of_competitors", []))
        
        # A keyword is more relevant if it found more insights
        keyword_score = keyword_pain + keyword_excitement + keyword_competitors
        keyword_relevance += keyword_score
    
    # Normalize keyword relevance by the number of keywords
    if keywords:
        keyword_relevance = keyword_relevance / len(keywords)
    
    # Calculate individual scores (0-10 scale)
    # Pain points score - use a more linear approach and factor in relevance
    pain_factor = num_pain_points * (avg_pain_relevance / 10)  # Scale by average relevance
    pain_score = min(10, pain_factor * 1.5)  # More linear scaling
    
    # Excitement signals score - use a more linear approach and factor in relevance
    excitement_factor = num_excitement * (avg_excitement_relevance / 10)  # Scale by average relevance
    excitement_score = min(10, excitement_factor * 1.5)  # More linear scaling
    
    # Competition score (moderate competition is ideal)
    if num_competitors == 0:
        competition_score = 1  # No competitors is worse (was 3)
    elif num_competitors <= 3:
        competition_score = 6  # Few competitors is good (was 7)
    elif num_competitors <= 7:
        competition_score = 10  # Moderate competition is ideal
    elif num_competitors <= 15:
        competition_score = 8  # More competition means established market
    else:
        competition_score = 5  # Too much competition is challenging (was 6)
    
    # Keyword relevance score (0-10)
    keyword_relevance_score = min(10, keyword_relevance)
    
    # Coherence penalty - reduce scores if coherence is low
    coherence_factor = coherence_score / 10  # 0.0 to 1.0
    
    # Red flag penalty - reduce scores based on number of red flags
    red_flag_penalty = min(0.5, num_red_flags * 0.1)  # Up to 50% reduction for 5+ red flags
    
    # Apply coherence factor and red flag penalty
    pain_score = pain_score * coherence_factor * (1 - red_flag_penalty)
    excitement_score = excitement_score * coherence_factor * (1 - red_flag_penalty)
    
    # Calculate overall viability score (0-100)
    overall_score = (
        pain_score * SCORE_WEIGHTS["pain_points"] * 10 +
        excitement_score * SCORE_WEIGHTS["excitement_signals"] * 10 +
        competition_score * SCORE_WEIGHTS["competitors"] * 10 +
        keyword_relevance_score * SCORE_WEIGHTS["keyword_relevance"] * 10
    )
    
    # Round scores to 1 decimal place
    pain_score = round(pain_score, 1)
    excitement_score = round(excitement_score, 1)
    competition_score = round(competition_score, 1)
    keyword_relevance_score = round(keyword_relevance_score, 1)
    coherence_score = round(coherence_score, 1)
    overall_score = round(overall_score, 1)
    
    # Generate explanations for each score
    score_explanations = {
        "market_pain_score": f"Based on {num_pain_points} pain points with average relevance of {round(avg_pain_relevance, 1)}/10. " +
                            (f"Score reduced by coherence factor ({coherence_score}/10)" if coherence_score < 9 else "") +
                            (f" and red flag penalty ({num_red_flags} red flags)" if num_red_flags > 0 else ""),
        
        "market_interest_score": f"Based on {num_excitement} excitement signals with average relevance of {round(avg_excitement_relevance, 1)}/10. " +
                                (f"Score reduced by coherence factor ({coherence_score}/10)" if coherence_score < 9 else "") +
                                (f" and red flag penalty ({num_red_flags} red flags)" if num_red_flags > 0 else ""),
        
        "competition_score": (f"No competitors found, which might indicate no market exists." if num_competitors == 0 else
                            f"Based on {num_competitors} competitors mentioned. " +
                            ("Few competitors indicates potential opportunity." if num_competitors <= 3 else
                             "Moderate competition indicates a validated market." if num_competitors <= 7 else
                             "Established market with significant competition." if num_competitors <= 15 else
                             "Highly competitive market may be challenging to enter.")),
        
        "keyword_relevance_score": f"Based on average of {round(keyword_relevance, 1)} findings per keyword across {len(keywords)} keywords.",
        
        "coherence_score": f"Measures consistency and coherence of findings. " +
                          ("Low score indicates contradictory or inconsistent data." if coherence_score < 5 else
                           "Moderate score indicates some inconsistencies in data." if coherence_score < 8 else
                           "High score indicates consistent and coherent findings."),
        
        "overall_viability_score": f"Calculated from weighted component scores: " +
                                  f"Pain Points ({SCORE_WEIGHTS['pain_points']*100}%), " +
                                  f"Excitement ({SCORE_WEIGHTS['excitement_signals']*100}%), " +
                                  f"Competition ({SCORE_WEIGHTS['competitors']*100}%), " +
                                  f"Keyword Relevance ({SCORE_WEIGHTS['keyword_relevance']*100}%)." +
                                  (f" Reduced by coherence factor and red flag penalty." if coherence_score < 9 or num_red_flags > 0 else "")
    }
    
    return {
        "market_pain_score": pain_score,
        "market_interest_score": excitement_score,
        "competition_score": competition_score,
        "keyword_relevance_score": keyword_relevance_score,
        "coherence_score": coherence_score,
        "overall_viability_score": overall_score,
        "raw_counts": {
            "pain_points": num_pain_points,
            "excitement_signals": num_excitement,
            "competitors": num_competitors,
            "red_flags": num_red_flags
        },
        "avg_relevance": {
            "pain_points": round(avg_pain_relevance, 1),
            "excitement_signals": round(avg_excitement_relevance, 1)
        },
        "score_explanations": score_explanations
    }

def generate_executive_summary(final_report, scores):
    """
    Generate a concise executive summary of the business idea validation results
    
    Args:
        final_report (dict): The final aggregated report
        scores (dict): The calculated scores
        
    Returns:
        dict: The executive summary
    """
    print("\nGenerating executive summary...")
    
    business_idea = final_report["metadata"]["business_idea"]
    aggregated = final_report["aggregated_results"]
    
    # Filter items by relevance threshold
    relevant_pain_points = []
    for item in aggregated.get("pain_points", []):
        if isinstance(item, dict) and "relevance" in item and item["relevance"] >= MIN_RELEVANCE_THRESHOLD:
            relevant_pain_points.append(item)
        elif isinstance(item, str):  # Handle old format
            relevant_pain_points.append({"text": item, "relevance": 5})
    
    relevant_excitement = []
    for item in aggregated.get("excitement_signals", []):
        if isinstance(item, dict) and "relevance" in item and item["relevance"] >= MIN_RELEVANCE_THRESHOLD:
            relevant_excitement.append(item)
        elif isinstance(item, str):  # Handle old format
            relevant_excitement.append({"text": item, "relevance": 5})
    
    # Sort by relevance (highest first)
    relevant_pain_points.sort(key=lambda x: x.get("relevance", 0), reverse=True)
    relevant_excitement.sort(key=lambda x: x.get("relevance", 0), reverse=True)
    
    # Get top pain points (up to 5)
    top_pain_points = relevant_pain_points[:min(5, len(relevant_pain_points))]
    
    # Get top excitement signals (up to 5)
    top_excitement = relevant_excitement[:min(5, len(relevant_excitement))]
    
    # Get top competitors (up to 5)
    top_competitors = aggregated["mentions_of_competitors"][:min(5, len(aggregated["mentions_of_competitors"]))]
    
    # Get top red flags (up to 3)
    top_red_flags = aggregated.get("red_flags", [])[:min(3, len(aggregated.get("red_flags", [])))]
    
    # Determine market validation status based on overall score using the new thresholds
    overall_score = scores["overall_viability_score"]
    if overall_score >= VALIDATION_THRESHOLDS["strongly_validated"]:
        validation_status = "Strongly Validated"
        recommendation = "This business idea shows strong market validation. Consider proceeding with development and creating an MVP."
    elif overall_score >= VALIDATION_THRESHOLDS["validated"]:
        validation_status = "Validated"
        recommendation = "This business idea shows good market validation. Consider proceeding with caution, focusing on the identified pain points."
    elif overall_score >= VALIDATION_THRESHOLDS["partially_validated"]:
        validation_status = "Partially Validated"
        recommendation = "This business idea shows moderate market validation. Consider refining the concept based on the identified pain points and excitement signals."
    elif overall_score >= VALIDATION_THRESHOLDS["weakly_validated"]:
        validation_status = "Weakly Validated"
        recommendation = "This business idea shows weak market validation. Consider pivoting or significantly refining the concept before proceeding."
    else:
        validation_status = "Not Validated"
        recommendation = "This business idea lacks sufficient market validation. Consider exploring alternative ideas or completely rethinking the approach."
    
    # Generate insights based on scores
    insights = []
    
    if scores["market_pain_score"] >= 7:
        insights.append("Strong pain points identified, indicating a clear market need.")
    elif scores["market_pain_score"] <= 3:
        insights.append("Few significant pain points identified, suggesting limited market need.")
    
    if scores["market_interest_score"] >= 7:
        insights.append("High market interest detected, indicating potential demand.")
    elif scores["market_interest_score"] <= 3:
        insights.append("Low market interest detected, suggesting limited demand.")
    
    if scores["competition_score"] >= 7:
        insights.append("Healthy competitive landscape, indicating a validated market.")
    elif scores["competition_score"] <= 3:
        insights.append("Limited competition may indicate an untapped market or lack of market viability.")
    
    if scores["keyword_relevance_score"] >= 7:
        insights.append("Keywords were highly relevant, providing good market insights.")
    elif scores["keyword_relevance_score"] <= 3:
        insights.append("Keywords had limited relevance, suggesting the need for refined market research.")
    
    # Create the executive summary
    summary = {
        "business_idea": business_idea,
        "validation_status": validation_status,
        "overall_score": overall_score,
        "top_pain_points": top_pain_points,
        "top_excitement_signals": top_excitement,
        "top_competitors": top_competitors,
        "key_insights": insights,
        "recommendation": recommendation,
        "score_explanations": scores.get("score_explanations", {})
    }
    
    return summary

def display_results(final_report, master_log_dir):
    """
    Display the final results in the console
    
    Args:
        final_report (dict): The final aggregated report
        master_log_dir (Path): Path to the master log directory
    """
    print("\n" + "="*60)
    print("=== Enhanced Business Idea Validation Report ===")
    print("="*60)
    
    print(f"\nBusiness Idea: {final_report['metadata']['business_idea']}")
    print(f"Keywords Used: {', '.join(final_report['metadata']['keywords'])}")
    
    aggregated = final_report["aggregated_results"]
    
    print("\n--- Aggregated Results ---\n")
    
    # Display pain points with relevance scores
    if aggregated["pain_points"]:
        print("Pain Points:")
        for item in aggregated["pain_points"]:
            if isinstance(item, dict) and "text" in item and "relevance" in item:
                print(f" - {item['text']} (Relevance: {item['relevance']}/10)")
            elif isinstance(item, str):
                print(f" - {item}")
    else:
        print("Pain Points: None found")
    
    # Display excitement signals with relevance scores
    if aggregated["excitement_signals"]:
        print("\nExcitement Signals:")
        for item in aggregated["excitement_signals"]:
            if isinstance(item, dict) and "text" in item and "relevance" in item:
                print(f" - {item['text']} (Relevance: {item['relevance']}/10)")
            elif isinstance(item, str):
                print(f" - {item}")
    else:
        print("\nExcitement Signals: None found")
    
    # Display competitors
    if aggregated["mentions_of_competitors"]:
        print(f"\nMentions of Competitors:\n - " + "\n - ".join(aggregated["mentions_of_competitors"]))
    else:
        print("\nMentions of Competitors: None found")
    
    # Display notable quotes
    if aggregated["notable_quotes"]:
        print("\nNotable Quotes:")
        for item in aggregated["notable_quotes"]:
            if isinstance(item, dict) and "text" in item:
                print(f" - {item['text']}")
            elif isinstance(item, str):
                print(f" - {item}")
    else:
        print("\nNotable Quotes: None found")
    
    # Display red flags if any
    if "red_flags" in aggregated and aggregated["red_flags"]:
        print(f"\nRed Flags:\n - " + "\n - ".join(aggregated["red_flags"]))
    
    # Display coherence score if available
    if "coherence_score" in aggregated:
        print(f"\nCoherence Score: {aggregated['coherence_score']}/10")
    
    print("\n--- Results by Keyword ---")
    for keyword, results in final_report["keyword_results"].items():
        print(f"\n  {keyword}:")
        for key, items in results.items():
            if items and key not in ["coherence_score"]:
                print(f"    {key.replace('_', ' ').title()}: {len(items)} items")
            elif key == "coherence_score":
                print(f"    {key.replace('_', ' ').title()}: {items}/10")
            elif items == 0:
                print(f"    {key.replace('_', ' ').title()}: None found")
    
    # Calculate scores
    scores = calculate_business_idea_scores(final_report)
    
    # Generate executive summary
    summary = generate_executive_summary(final_report, scores)
    
    # Display scores with explanations
    print("\n" + "="*60)
    print("=== BUSINESS IDEA SCORECARD ===")
    print("="*60)
    
    print(f"\nMarket Pain Score: {scores['market_pain_score']}/10")
    print(f"  Why: {scores['score_explanations']['market_pain_score']}")
    
    print(f"\nMarket Interest Score: {scores['market_interest_score']}/10")
    print(f"  Why: {scores['score_explanations']['market_interest_score']}")
    
    print(f"\nCompetition Score: {scores['competition_score']}/10")
    print(f"  Why: {scores['score_explanations']['competition_score']}")
    
    print(f"\nKeyword Relevance Score: {scores['keyword_relevance_score']}/10")
    print(f"  Why: {scores['score_explanations']['keyword_relevance_score']}")
    
    print(f"\nCoherence Score: {scores['coherence_score']}/10")
    print(f"  Why: {scores['score_explanations']['coherence_score']}")
    
    print(f"\nOVERALL VIABILITY SCORE: {scores['overall_viability_score']}/100")
    print(f"  Why: {scores['score_explanations']['overall_viability_score']}")
    
    # Display executive summary
    print("\n" + "="*60)
    print("=== EXECUTIVE SUMMARY ===")
    print("="*60)
    
    print(f"\nValidation Status: {summary['validation_status']} ({summary['overall_score']}/100)")
    
    print("\nTop Pain Points:")
    for point in summary["top_pain_points"]:
        if isinstance(point, dict) and "text" in point and "relevance" in point:
            print(f" - {point['text']} (Relevance: {point['relevance']}/10)")
        elif isinstance(point, str):
            print(f" - {point}")
    
    print("\nTop Excitement Signals:")
    for signal in summary["top_excitement_signals"]:
        if isinstance(signal, dict) and "text" in signal and "relevance" in signal:
            print(f" - {signal['text']} (Relevance: {signal['relevance']}/10)")
        elif isinstance(signal, str):
            print(f" - {signal}")
    
    # Display red flags if any
    if "red_flags" in aggregated and aggregated["red_flags"]:
        print("\nRed Flags:")
        for flag in aggregated["red_flags"][:min(3, len(aggregated["red_flags"]))]:
            print(f" - {flag}")
    
    print("\nKey Competitors:")
    for competitor in summary["top_competitors"]:
        print(f" - {competitor}")
    
    print("\nKey Insights:")
    for insight in summary["key_insights"]:
        print(f" - {insight}")
    
    print(f"\nRecommendation: {summary['recommendation']}")
    
    # Save summary and scores to file
    summary_with_scores = {
        "scores": scores,
        "executive_summary": summary
    }
    summary_path = master_log_dir / "executive_summary.json"
    save_to_file(summary_with_scores, summary_path, is_json=True)
    
    print(f"\nFull JSON report saved to: {master_log_dir / 'final_report.json'}")
    print(f"Executive summary saved to: {summary_path}")




# ========== MAIN ==========
def main():

    

    """Main function to run the enhanced business idea validator"""
    business_idea = input("Enter your business idea: ")
    
    # Set up master logging directory
    master_log_dir = setup_master_log_directory(business_idea)
    print(f"Logs will be saved to: {master_log_dir}")
    
    # Generate keywords
    keywords = generate_keywords(business_idea)
    print(f"Generated keywords: {keywords}")
    
    # Save keywords metadata
    keywords_metadata = {
        "business_idea": business_idea,
        "timestamp": datetime.datetime.now().isoformat(),
        "keywords": keywords
    }
    metadata_path = master_log_dir / "keywords_metadata.json"
    save_to_file(keywords_metadata, metadata_path, is_json=True)
    
    # Process each keyword
    all_keyword_results = {}
    for keyword in keywords:
        keyword_results = process_keyword(keyword, master_log_dir)
        all_keyword_results[keyword] = keyword_results
    
    # Generate aggregated report
    final_report = generate_aggregated_report(business_idea, keywords, all_keyword_results, master_log_dir)
    
    # Display results with scores and executive summary
    display_results(final_report, master_log_dir)


 

if __name__ == "__main__":

    

    from business_validator.scrapers.xhs import   scrape_xhs_post_comments
    #aa = scrape_xhs("insta360出租")
    aa = scrape_xhs_post_comments('6813c009000000002300c965')
    print(aa)
    

    # main()
