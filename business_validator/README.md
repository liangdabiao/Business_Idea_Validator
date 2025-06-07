# Business Validator

A Python package for validating business ideas by scraping and analyzing discussions from HackerNews and Reddit.

## Overview

This package helps entrepreneurs and product managers validate business ideas by:

1. Generating relevant search keywords for the business idea
2. Scraping HackerNews and Reddit for discussions related to these keywords
3. Analyzing the posts and comments for:
   - Pain points mentioned
   - Existing solutions
   - Market signals
   - Overall sentiment
   - Engagement levels
4. Generating a comprehensive validation report with:
   - Overall validation score (0-100)
   - Key pain points discovered
   - Existing solutions in the market
   - Market opportunities
   - Platform-specific insights
   - Recommendations for moving forward

## Installation

```bash
# Clone the repository
git clone <repository-url>

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from business_validator import validate_business_idea, print_validation_report

# Validate a business idea
business_idea = "A subscription service for eco-friendly cleaning products"
analysis = validate_business_idea(business_idea)

# Print the validation report
print_validation_report(analysis, business_idea)
```

### Example Script

See `business_validator_example.py` for a complete example of how to use the package.

```bash
python business_validator_example.py
```

## Package Structure

```
business_validator/
├── __init__.py                 # Package exports
├── config.py                   # Configuration settings
├── models.py                   # Pydantic models
├── validator.py                # Main validation orchestration
├── utils/
│   ├── __init__.py
│   ├── environment.py          # Setup, logging, checkpoints
│   └── reporting.py            # Report generation and printing
├── scrapers/
│   ├── __init__.py
│   ├── hackernews.py           # HN scraping functions
│   └── reddit.py               # Reddit scraping functions
└── analyzers/
    ├── __init__.py
    ├── keyword_generator.py    # Keyword generation
    ├── hackernews_analyzer.py  # HN analysis
    ├── reddit_analyzer.py      # Reddit analysis
    └── combined_analyzer.py    # Final analysis generation
```

## Configuration

You can modify the configuration settings in `config.py`:

- `SCRAPERAPI_KEY`: Your ScraperAPI key for web scraping
- `MAX_PAGES_PER_KEYWORD_HN`: Number of HackerNews pages to scrape per keyword
- `MAX_PAGES_PER_KEYWORD_REDDIT`: Number of Reddit pages to scrape per keyword
- `MAX_POSTS_TO_ANALYZE`: Maximum Reddit posts to analyze comments for
- `MAX_COMMENTS_PER_POST`: Maximum comments to analyze per Reddit post
- `HN_DELAY` and `REDDIT_DELAY`: Delay between requests to avoid rate limiting
- `CHECKPOINT_INTERVAL`: How often to save checkpoints during processing

## Data Storage

All scraped data and analysis results are saved to the `validation_data` directory, organized by run ID (based on the business idea and timestamp). This allows you to:

- Review the raw data collected
- Analyze the results in more detail
- Resume validation if the process is interrupted
- Compare different business ideas

## Dependencies

- requests: For making HTTP requests
- pydantic: For data validation and serialization
- SimplerLLM: For LLM-based analysis
- BeautifulSoup4: For HTML parsing (used in some scraping functions)

## License

[MIT License](LICENSE)
