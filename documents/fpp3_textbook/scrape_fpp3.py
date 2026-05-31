#!/usr/bin/env python3
"""
FPP3 Textbook Scraper - With Section Numbers
Scrapes all pages from https://otexts.com/fpp3/ and preserves section numbers like 9.1, 9.2, etc.
"""

import subprocess
import time
from pathlib import Path
from bs4 import BeautifulSoup

# Output directory
OUTPUT_DIR = Path("/workspace/fpp3_textbook")

# Delay between requests (be respectful to server)
DELAY = 0.5

# All pages with their expected section numbers
PAGES = {
    # Preface
    "index": "0",
    
    # Chapter 1
    "intro": "1",
    "what-can-be-forecast": "1.1",
    "planning": "1.2",
    "determining-what-to-forecast": "1.3",
    "data-methods": "1.4",
    "case-studies": "1.5",
    "basic-steps": "1.6",
    "perspective": "1.7",
    "intro-exercises": "1.8",
    "intro-reading": "1.9",
    
    # Chapter 2
    "graphics": "2",
    "tsibbles": "2.1",
    "time-plots": "2.2",
    "tspatterns": "2.3",
    "seasonal-plots": "2.4",
    "subseries": "2.5",
    "scatterplots": "2.6",
    "lag-plots": "2.7",
    "acf": "2.8",
    "wn": "2.9",
    "graphics-exercises": "2.10",
    "graphics-reading": "2.11",
    
    # Chapter 3
    "decomposition": "3",
    "transformations": "3.1",
    "components": "3.2",
    "moving-averages": "3.3",
    "classical-decomposition": "3.4",
    "methods-used-by-official-statistics-agencies": "3.5",
    "stl": "3.6",
    "decomposition-exercises": "3.7",
    "decomposition-reading": "3.8",
    
    # Chapter 4
    "features": "4",
    "some-simple-statistics": "4.1",
    "acf-features": "4.2",
    "stlfeatures": "4.3",
    "other-features": "4.4",
    "exploring-australian-tourism-data": "4.5",
    "feast-exercises": "4.6",
    "further-reading": "4.7",
    
    # Chapter 5
    "toolbox": "5",
    "a-tidy-forecasting-workflow": "5.1",
    "simple-methods": "5.2",
    "residuals": "5.3",
    "diagnostics": "5.4",
    "prediction-intervals": "5.5",
    "ftransformations": "5.6",
    "forecasting-decomposition": "5.7",
    "accuracy": "5.8",
    "distaccuracy": "5.9",
    "tscv": "5.10",
    "toolbox-exercises": "5.11",
    "basics-reading": "5.12",
    
    # Chapter 6
    "judgmental": "6",
    "judgmental-limitations": "6.1",
    "judgmental-principles": "6.2",
    "delphimethod": "6.3",
    "analogies": "6.4",
    "scenarios": "6.5",
    "new-products": "6.6",
    "judgmental-adjustments": "6.7",
    "judgmental-reading": "6.8",
    
    # Chapter 7
    "regression": "7",
    "regression-intro": "7.1",
    "least-squares": "7.2",
    "regression-evaluation": "7.3",
    "useful-predictors": "7.4",
    "selecting-predictors": "7.5",
    "forecasting-regression": "7.6",
    "nonlinear-regression": "7.7",
    "causality": "7.8",
    "regression-matrices": "7.9",
    "regression-exercises": "7.10",
    "regression-reading": "7.11",
    
    # Chapter 8
    "expsmooth": "8",
    "ses": "8.1",
    "holt": "8.2",
    "holt-winters": "8.3",
    "taxonomy": "8.4",
    "ets": "8.5",
    "estimation-and-model-selection": "8.6",
    "ets-forecasting": "8.7",
    "expsmooth-exercises": "8.8",
    "expsmooth-reading": "8.9",
    
    # Chapter 9
    "arima": "9",
    "stationarity": "9.1",
    "backshift": "9.2",
    "AR": "9.3",
    "MA": "9.4",
    "non-seasonal-arima": "9.5",
    "arima-estimation": "9.6",
    "arima-r": "9.7",
    "arima-forecasting": "9.8",
    "seasonal-arima": "9.9",
    "arima-ets": "9.10",
    "arima-exercises": "9.11",
    "arima-reading": "9.12",
    
    # Chapter 10
    "dynamic": "10",
    "estimation": "10.1",
    "regarima": "10.2",
    "forecasting": "10.3",
    "stochastic-and-deterministic-trends": "10.4",
    "dhr": "10.5",
    "lagged-predictors": "10.6",
    "dynamic-exercises": "10.7",
    "dynamic-reading": "10.8",
    
    # Chapter 11
    "hierarchical": "11",
    "hts": "11.1",
    "single-level": "11.2",
    "reconciliation": "11.3",
    "tourism": "11.4",
    "rec-prob": "11.5",
    "prison": "11.6",
    "hierarchical-exercises": "11.7",
    "hierarchical-reading": "11.8",
    
    # Chapter 12
    "advanced": "12",
    "complexseasonality": "12.1",
    "prophet": "12.2",
    "VAR": "12.3",
    "nnetar": "12.4",
    "bootstrap": "12.5",
    "advanced-exercises": "12.6",
    "advanced-reading": "12.7",
    
    # Chapter 13
    "practical": "13",
    "weekly": "13.1",
    "counts": "13.2",
    "limits": "13.3",
    "combinations": "13.4",
    "aggregates": "13.5",
    "backcasting": "13.6",
    "long-short-ts": "13.7",
    "training-test": "13.8",
    "missing-outliers": "13.9",
    "further-reading-1": "13.10",
    
    # Appendix
    "appendix-using-r": "A",
    "appendix-for-instructors": "B",
    "appendix-reviews": "C",
    "about-the-authors": "D",
    "bibliography": "E",
}

# Chapter directories mapping
CHAPTER_DIRS = {
    "0": "00_preface",
    "1": "01_getting_started",
    "2": "02_time_series_graphics",
    "3": "03_time_series_decomposition",
    "4": "04_time_series_features",
    "5": "05_forecaster_toolbox",
    "6": "06_judgmental_forecasts",
    "7": "07_regression_models",
    "8": "08_exponential_smoothing",
    "9": "09_arima_models",
    "10": "10_dynamic_regression",
    "11": "11_hierarchical_time_series",
    "12": "12_advanced_methods",
    "13": "13_practical_issues",
    "A": "99_appendix",
    "B": "99_appendix",
    "C": "99_appendix",
    "D": "99_appendix",
    "E": "99_appendix",
}


def fetch_with_curl(url):
    """Fetch URL using curl command."""
    try:
        result = subprocess.run(
            ["curl", "-s", "-L", "--max-time", "30", url],
            capture_output=True,
            text=True,
            timeout=35
        )
        return result.stdout if result.returncode == 0 else None
    except Exception as e:
        print(f"Curl error: {e}")
        return None


def extract_content(html):
    """Extract content with section numbers preserved."""
    if not html:
        return None, None
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Find main content
    content = soup.find("div", class_="book-body")
    if not content:
        content = soup.find("body")
    if not content:
        return None, None
    
    # Get section title
    title = None
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    
    lines = []
    
    # Process all headings and content
    for element in content.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "pre"]):
        text = element.get_text(strip=True)
        if not text:
            continue
            
        if element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(element.name[1])
            lines.append(f"\n{'#' * level} {text}\n")
        elif element.name == "p":
            lines.append(f"\n{text}\n")
        elif element.name == "li":
            lines.append(f"- {text}")
        elif element.name == "blockquote":
            lines.append(f"\n> {text}\n")
        elif element.name == "pre":
            code = element.get_text()
            lines.append(f"\n```\n{code}\n```\n")
    
    return title, "\n".join(lines)


def get_filename(section_num, slug):
    """Generate filename with section number prefix."""
    clean_slug = slug.replace("-", "_")
    
    if section_num == "0":
        return "preface.md"
    elif section_num in ["A", "B", "C", "D", "E"]:
        return f"{section_num.lower()}_{clean_slug}.md"
    elif "." in section_num:
        parts = section_num.split(".")
        return f"{parts[0]}_{parts[1]}_{clean_slug}.md"
    else:
        return f"ch{section_num}_{clean_slug}.md"


def main():
    print("=" * 60)
    print("FPP3 Textbook Scraper (with section numbers)")
    print("=" * 60)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    success = 0
    failed = []
    
    for slug, section_num in PAGES.items():
        url = f"https://otexts.com/fpp3/{slug}.html"
        
        # Determine directory
        chapter_num = section_num.split(".")[0] if "." in section_num else section_num
        chapter_dir = CHAPTER_DIRS.get(chapter_num, "99_appendix")
        
        dir_path = OUTPUT_DIR / chapter_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Fetch and extract
        html = fetch_with_curl(url)
        title, content = extract_content(html)
        
        if content:
            filename = get_filename(section_num, slug)
            filepath = dir_path / filename
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            
            print(f"[{section_num}] {slug} -> {chapter_dir}/{filename}")
            success += 1
        else:
            failed.append((section_num, slug))
            print(f"[{section_num}] FAILED: {slug}")
        
        time.sleep(DELAY)
    
    print("\n" + "=" * 60)
    print(f"Complete: {success} success, {len(failed)} failed")
    if failed:
        print(f"Failed: {failed}")


if __name__ == "__main__":
    main()
