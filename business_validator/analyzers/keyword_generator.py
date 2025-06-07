"""
Keyword generation functionality for business idea validation.
"""

import logging
from typing import List

from SimplerLLM.langauge.llm import LLM, LLMProvider
from SimplerLLM.langauge.llm_addons import generate_basic_pydantic_json_model

from business_validator.models import KeywordModel

# Initialize LLM
llm_instance = LLM.create(provider=LLMProvider.OPENAI, model_name="gpt-4o")

def generate_keywords(business_idea: str, num_keywords: int = 3) -> List[str]:
    """Generate search keywords for the business idea.
    
    Args:
        business_idea: The business idea to generate keywords for
        num_keywords: The number of keywords to generate
        
    Returns:
        List of generated keywords
    """
    logging.info(f"Generating keywords for business idea: {business_idea}")
    
    prompt = f"""
    For the business idea: "{business_idea}"
    
    Generate {num_keywords} specific search keywords that would help validate this idea.
    These should be phrases people might use when discussing pain points, needs, or solutions related to this idea.
    
    Keep keywords concise (2-4 words) and focused on the core problem/solution.
    """
    
    try:
        response_model = generate_basic_pydantic_json_model(
            model_class=KeywordModel,
            prompt=prompt,
            llm_instance=llm_instance
        )
        
        logging.info(f"Generated keywords: {response_model.keywords}")
        return response_model.keywords
    except Exception as e:
        logging.error(f"Error generating keywords 2: {e}")
        # Fallback to basic keywords if generation fails
        fallback_keywords = [business_idea.split()[:2]]
        return fallback_keywords





def generate_keywords_cn(business_idea: str, num_keywords: int = 3) -> List[str]:
    """Generate search keywords for the business idea. return chinese language.
    
    Args:
        business_idea: The business idea to generate keywords for
        num_keywords: The number of keywords to generate
        
    Returns:
        List of generated keywords
    """
    logging.info(f"Generating keywords for business idea: {business_idea}")
    
    prompt = f"""
    For the business idea: "{business_idea}"
    
    Generate {num_keywords} specific search keywords that would help validate this idea.
    These should be phrases people might use when discussing pain points, needs, or solutions related to this idea.
    
    Keep keywords concise (3-6 words) and focused on the core problem/solution. return chinese language.
    """
    
    try:
        response_model = generate_basic_pydantic_json_model(
            model_class=KeywordModel,
            prompt=prompt,
            llm_instance=llm_instance
        )
        
        logging.info(f"Generated keywords: {response_model.keywords}")
        return response_model.keywords
    except Exception as e:
        logging.error(f"Error generating keywords 2: {e}")
        # Fallback to basic keywords if generation fails
        fallback_keywords = [business_idea.split()[:2]]
        return fallback_keywords
