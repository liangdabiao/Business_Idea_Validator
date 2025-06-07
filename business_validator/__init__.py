"""
Business Idea Validator Package

This package provides tools to validate business ideas by scraping and analyzing
data from HackerNews and Reddit.
"""

from business_validator.validator import validate_business_idea, print_validation_report
from business_validator.validator_cn import  validate_business_idea_cn

__all__ = ['validate_business_idea', 'print_validation_report','validate_business_idea_cn']
