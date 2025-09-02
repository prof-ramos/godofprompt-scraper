# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **web scraper** specifically designed to extract prompt links from GodOfPrompt.ai. The project uses Selenium WebDriver to handle the site's dynamic JavaScript content and pagination.

## Architecture

### Core Script: `extract_links.py`
- **Main function**: `main()` - Orchestrates full extraction across all categories
- **Test function**: `test_category()` - Tests extraction for a single category
- **Key extraction logic**: `extract_category_links()` - Handles pagination and link extraction for one category
- **Driver management**: `create_driver()` - Configures Chrome WebDriver with anti-detection settings
- **Data processing**: JavaScript execution via `execute_script()` for dynamic content extraction

### Configuration: `links.yaml`
Defines 8 prompt categories with expected counts:
- Vendas (252), Educação (276), Empreendedores Individuais (201)
- SEO (223), Produtividade (218), Escrita (383)  
- Negócios (293), Marketing (177)

### Output Structure
- **JSON files**: Timestamped with statistics and extracted data
- **Logs**: `extraction_log.txt` with detailed execution information
- **Format**: Hierarchical structure with category-level and overall statistics

## Core Technologies

- **Selenium WebDriver**: Handles dynamic content and JavaScript rendering
- **Chrome Driver**: Configured with headless mode and anti-bot detection measures
- **BeautifulSoup**: HTML parsing (imported but primarily uses Selenium's JS execution)
- **PyYAML**: Configuration management
- **Logging**: Comprehensive file and console logging

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies  
pip install -r requirements.txt
```

### Running the Scraper
```bash
# Test single category (interactive selection)
python3 extract_links.py --test

# Test specific category
python3 extract_links.py --test "Marketing"

# Full extraction (all categories)
python3 extract_links.py
```

### Testing
```bash
# Run tests (if available)
pytest

# Check code quality
black extract_links.py
flake8 extract_links.py
mypy extract_links.py
```

## Key Implementation Details

### Dynamic Content Handling
The site uses JavaScript-generated content with Wized attributes:
- `[wized="plp_prompt_item_all"]` - Prompt container elements
- `[wized="plp_prompt_item_link"]` - Prompt URLs
- `[wized="plp_prompt_name"]` - Prompt titles
- `[wized="pagin-next"]` - Pagination controls

### Anti-Detection Measures
Chrome driver configured with:
- Headless execution
- Realistic User-Agent strings
- Disabled automation features
- Standard window dimensions (1920x1080)

### Error Handling & Robustness
- Comprehensive try-catch blocks with driver cleanup
- Timeout handling for page loads and element waits
- Maximum page limits (50 pages per category) to prevent infinite loops
- Duplicate URL detection and removal

### Performance Considerations
- Single driver reuse across categories to reduce overhead
- Strategic delays between requests (2-3 seconds)
- Maximum page limits and timeout controls
- Memory-efficient processing with immediate result storage

## Important Notes

- **Not a git repository**: This project doesn't use version control
- **Python 3.8+ required**: Check compatibility with current Python version
- **Chrome browser required**: For Selenium WebDriver functionality
- **Rate limiting**: Built-in delays respect server resources
- **Data validation**: URLs are verified and normalized before storage
- **Resumability**: Individual category failures don't stop overall extraction