#!/usr/bin/env python3
"""
Setup script for GodOfPrompt Scraper
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="godofprompt-scraper",
    version="1.0.0",
    author="Gabriel Ramos",
    description="Advanced web scraper for GodOfPrompt.ai with anti-blocking and performance optimization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gabrielramos/godofprompt-scraper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: HTML",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-html>=3.1.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "firecrawl": [
            "firecrawl-py>=0.0.5",
        ],
        "performance": [
            "psutil>=5.9.0",
            "memory-profiler>=0.61.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "godofprompt-scraper=integrated_scraper:main",
            "extract-links=extract_links:main",
            "test-scraper=extract_links:test_category",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/gabrielramos/godofprompt-scraper/issues",
        "Source": "https://github.com/gabrielramos/godofprompt-scraper",
        "Documentation": "https://github.com/gabrielramos/godofprompt-scraper/blob/main/README.md",
    },
)