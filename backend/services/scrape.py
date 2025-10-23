# backend/services/scrape.py

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.services.scrapers.linkedin_scraper import LinkedInScraper
from backend.services.scrapers.hiring_cafe import HiringCafeScraper
from backend.services.scraper import Scraper

def run_scraper(date_posted: str, 
                experience_level: str, 
                job_title: str, 
                location: str):
    """
    Entry point to run the appropriate scraper based on the platform.
    Returns a list of job dicts formatted to match the 'jobs' table.
    """

    print(f"[{datetime.now()}] Starting scrape for ...")

    # Original Scraper
    
    #scraper = Scraper()
    #hiring_cafe_scraper = HiringCafeScraper()
    linked_in_scraper = LinkedInScraper()
    
    try:
        #results = scraper.scrape(date_posted, experience_level, job_title, location)
        #results = hiring_cafe_scraper.scrape(date_posted, experience_level, job_title, location)
        results = linked_in_scraper.scrape(date_posted, experience_level, job_title, location)
    finally:
        #scraper.close()
        #hiring_cafe_scraper.close()
        linked_in_scraper.close()


    print(f"[{datetime.now()}] Scrape completed. Found {len(results)} job(s).")
    return results  
    
    
    """     
    scrapers = [
        ("Hiring Cafe", HiringCafeScraper()),
    ]
    
    results = []
    
    # Run each scraper in its own thread
    with ThreadPoolExecutor(max_workers=len(scrapers)) as executor:
        futures = { # expected items
            executor.submit(scraper.scrape, date_posted, experience_level, job_title, location): (name, scraper)
            for name, scraper in scrapers
        }

        for future in as_completed(futures): # fill the results dictionary
            name, scraper = futures[future]
            try:
                data = future.result()
                results.extend(data)
                print(f"[{name}] Completed with {len(data)} results.")
            except Exception as e:
                print(f"[{name}] Failed: {e}")
            finally:
                scraper.close()

    print(f"[{datetime.now()}] All scrapers completed. Total: {len(results)} jobs.")
    return results 
    """