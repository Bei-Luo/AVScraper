import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.scraper import scraper
from src.crawlers.generic import Javbus

def test_scraper_initialization():
    print("Testing Scraper Initialization...")
    if scraper.crawler_manager:
        print("CrawlerManager initialized successfully.")
    else:
        print("Failed to initialize CrawlerManager.")
        return

    crawlers = scraper.crawler_manager.crawlers
    print(f"Registered crawlers: {len(crawlers)}")
    
    if len(crawlers) > 0:
        first_crawler = crawlers[0]
        print(f"First crawler type: {type(first_crawler)}")
        if isinstance(first_crawler, Javbus):
            print("First crawler is GenericCrawler as expected.")
            print(f"Base URL: {first_crawler.base_url}")
        else:
            print("First crawler is NOT GenericCrawler.")
    else:
        print("No crawlers registered. Check config.")

if __name__ == "__main__":
    test_scraper_initialization()
