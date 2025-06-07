"""
Reporting utilities for displaying validation results.
"""

from business_validator.models import CombinedAnalysis

def print_validation_report(analysis: CombinedAnalysis, business_idea: str):
    """Print a nicely formatted validation report.
    
    Args:
        analysis: The combined analysis results
        business_idea: The business idea that was validated
    """
    print("\n" + "="*60)
    print("BUSINESS IDEA VALIDATION REPORT")
    print("="*60)
    print(f"Idea: {business_idea}")
    print(f"Overall Score: {analysis.overall_score}/100")
    print("\nSummary:")
    print(analysis.market_validation_summary)
    
    print("\nKey Pain Points Discovered:")
    for pain_point in analysis.key_pain_points:
        print(f"  • {pain_point}")
    
    print("\nExisting Solutions Found:")
    for solution in analysis.existing_solutions:
        print(f"  • {solution}")
    
    print("\nMarket Opportunities:")
    for opportunity in analysis.market_opportunities:
        print(f"  • {opportunity}")
    
    print("\nPlatform-Specific Insights:")
    for insight in analysis.platform_insights:
        print(f"  • {insight.platform}: {insight.insights}")
    
    print("\nRecommendations:")
    for recommendation in analysis.recommendations:
        print(f"  • {recommendation}")
    
    print("="*60)
