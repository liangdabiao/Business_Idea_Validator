from typing import List
from pydantic import BaseModel
import requests
import time
import csv
import json
import datetime
import re
from pathlib import Path
import math
from SimplerLLM.langauge.llm import LLM, LLMProvider
from SimplerLLM.langauge.llm_addons import generate_pydantic_json_model
import hashlib


llm_instance = LLM.create(provider=LLMProvider.OPENAI,model_name="gpt-4o")

 

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
 


# Base directory for logs
LOGS_DIR = Path("logs")

# ========== KEYWORD GENERATION ==========
class KeywordModel(BaseModel):
    keywords: List[str]
 


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


# 增加内容写入文件的函数
def append_to_file(content, file_path, is_json=False):
    """
    Save content to a file
    
    Args:
        content: The content to save
        file_path (Path): The path to save the file to
        is_json (bool): Whether the content is JSON and should be formatted
    """
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            if is_json:
                f.write(json.dumps(content, ensure_ascii=False) + '\n')
            else:
                f.write(content)
        print(f"Saved: {file_path}")
    except Exception as e:
        print(f"Error saving to {file_path}: {e}")


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

class TagAnalysis(BaseModel):
    tag: str
    count:int
    sentiment: str  # positive, negative, neutral
    keywords: List[str]

class TagListAnalysis(BaseModel):
    taglist: List[TagAnalysis] 

def analyze_text_with_openai(business_idea, master_log_dir, topic,topic_description, review  ):
    print(f"analyze_text_with_openai for topic: {topic}")  
    """
    Analyze text using OpenAI and optionally log the results
    
    Args:
        business_idea (str): The text to analyze
        topic (str): The topic keyword being researched
        master_log_dir (dict, optional): Log directory paths
        review (str): review being analyzed 
        
    Returns:
        dict: The analysis results
    """
    prompt = f"""
You are a business idea validator.  
Analyze the following text in the context of the topic: # "{topic}" # ,topic description: # "{topic_description}" #

Find:
1. Pain points people mention
2. Excitement signals (desires, positive needs)
3. Competitors mentioned
4. Notable quotes (max 2 short quotes)
5. Red flags (anything that might indicate the business idea is not viable)

For each pain point and excitement signal, rate its relevance to the business idea on a scale of 0-10, 
where 0 means completely irrelevant and 10 means highly relevant and specific to the business idea.

Also identify any contradictions or red flags in the data that might indicate the business idea is not viable.


The coherence_score (0-10) represents how consistent and coherent the findings are, with 10 being highly coherent 
and 0 indicating contradictory or nonsensical findings.

AND note: return in chinese language.

Review Text to analyze: ###
{review}
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
        if master_log_dir and topic and topic is not None:
            file_name = f"{business_idea}.jsonl"
            file_path = Path(master_log_dir) / file_name
            print("23")
            # Add metadata to the logged result
            log_result = {
                "metadata": {
                    "topic": topic, 
                    "business_idea": business_idea,
                    "timestamp": datetime.datetime.now().isoformat()
                },
                "analysis": response_model.model_dump() if hasattr(response_model, 'model_dump') else response_model
            }
            print("24")
            append_to_file(log_result, file_path, is_json=True)
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


def generate_aggregated_report(business_idea,   all_keyword_results, master_log_dir):
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
    
    # 初始化模板确保所有键存在
    initial_aggregated_results = {
        "pain_points": [],
        "excitement_signals": [],
        "mentions_of_competitors": [],
        "notable_quotes": [],
        "red_flags": [],
        "coherence_scores": []
    }
    aggregated_results = initial_aggregated_results.copy()
    aggregated_results.update(all_keyword_results)
   
    
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
        aggregated_results["coherence_score"] = aggregated_results["coherence_score"]  # Default middle value
    
    # Remove the list of scores
    del aggregated_results["coherence_scores"]
    
    # Create final report
    final_report = {
        "metadata": {
            "business_idea": business_idea,
            "timestamp": datetime.datetime.now().isoformat(), 
        },
        "aggregated_results": aggregated_results
    }
    
    # Save final report
    final_report_path = Path(master_log_dir) / f"final_{business_idea}_report.json"
    print(final_report_path)
    save_to_file(final_report, final_report_path, is_json=True)
    
    return final_report

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
    
    




def analyze_word_frequency(final_report):
    print(f"analyze_word_frequency :")  
   
    prompt = f"""您是一位经验丰富的产品分析专家和自然语言处理专家。您的任务是基于我提供的一批用户评论
然后为该产品构建一个基于数据的分析标签 ，以便深入洞察用户需求和反馈。

标签设计原则：
    *   覆盖性： 能够尽可能全面地覆盖评论中用户提及的主要议题。
    *   互斥性（理想状态）： 同一级下的标签应尽可能互斥，避免语义重叠过多。
    *   简洁性： 每个标签的名称应简洁明了，尽量不超过5个汉字。

用户评论是以下数据： ####
{final_report}

####, 注意： Directly return the json, do not include any other text.  标签需要统计对应评论数量：标签:数量，
返回json格式参考如下：###
 [
    {{"tag":"口味偏好","count":3,"sentiment":"negative","keywords":["口味难吃","偏好差"]}},
    {{"tag":"产品外观","count":2,"sentiment":"positive"}},
    {{"tag":"影响睡眠","count":1,"sentiment":"mixed"}},
    {{"tag":"设计差","count":1,"sentiment":"positive"}},
....
 ]
"""
 

    try:
        response_model = generate_pydantic_json_model(model_class=TagListAnalysis,
                                                      llm_instance=llm_instance,
                                                      prompt=prompt)
        
        # 确保返回的是模型实例而非字典
        if not isinstance(response_model, (TagListAnalysis, dict)):
            print(f"Unexpected response  : {response_model}")
            raise ValueError(f"Unexpected response type: {type(response_model)}")
        print("response_model：")
        if isinstance(response_model, dict):
            response_model = TagListAnalysis(**response_model)
        #print(response_model)  
         
        return response_model.model_dump()
    except Exception as e:
        print(f"Error during TagListAnalysis analysis: {e}")
        return []

# ========== MAIN ==========
# 项目流程： 提出business_idea 商业问题，提取csv评论内容all_reviews ， 对每一个评论进行分析， 合并分析结果， 生成最终报告， 显示结果， 生成总结， 保存结果。
def csv_analysis(csv_file):
    #  提出business_idea 商业问题
    #business_idea = '用户的评价哪些方面？'
    business_idea = hashlib.md5(csv_file.encode('utf-8')).hexdigest()
    # 日志存放地方
    master_log_dir =  'jsons/'
    #  提取csv评论内容all_reviews  
    # 提取csv评论内容all_reviews
    reviews_csv = csv_file #'xiaohongshu.csv'
    all_reviews = []
    
    # 读取CSV文件内容
    with open(reviews_csv, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # 跳过标题行
        for row in reader:
            all_reviews.append(row)  # 假设评论内容在第一列

    reviews_with_analysis = []
    for review in all_reviews:
        #print(review)
        topic = review[2]
        topic_description = review[6]
        print('topic:')
        print(topic)
        text = review[7]
        #print('text:')
        #print(text)
        result = analyze_text_with_openai(business_idea, master_log_dir, topic,topic_description, text )
        print(result)
        if(result):
            reviews_with_analysis.append(result)
    
    print(reviews_with_analysis)
    #， 合并分析结果
    merge_results_txt = merge_results(reviews_with_analysis)
    print('merge_results_txt:')
    print(merge_results_txt)
    all_keyword_results = merge_results_txt
    
    # Generate aggregated report
    final_report = generate_aggregated_report(business_idea,  all_keyword_results, master_log_dir)
    
    # Display results with scores and executive summary
    display_results(final_report, master_log_dir)

    pain_points_word_frequency = analyze_word_frequency(final_report["aggregated_results"]["pain_points"])
    print("pain_points_word_frequency:")
    print(pain_points_word_frequency)

    excitement_signals_word_frequency = analyze_word_frequency(final_report["aggregated_results"]["excitement_signals"])
    print("excitement_signals_word_frequency:")
    print(excitement_signals_word_frequency)

    notable_quotes_word_frequency = analyze_word_frequency(final_report["aggregated_results"]["notable_quotes"])
    print("notable_quotes_word_frequency:")
    print(notable_quotes_word_frequency)

    red_flags_word_frequency = analyze_word_frequency(final_report["aggregated_results"]["red_flags"])
    print("red_flags_word_frequency:")
    print(red_flags_word_frequency)

    return final_report, pain_points_word_frequency,excitement_signals_word_frequency,notable_quotes_word_frequency,red_flags_word_frequency



 

if __name__ == "__main__":
    main()
