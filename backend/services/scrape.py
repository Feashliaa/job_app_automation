# backend/services/scrape.py

from datetime import datetime
from backend.services.linkedin_scraper import scrape_linkedin
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

    scraper = Scraper()
    
    try:
        results = scraper.scrape(date_posted, experience_level, job_title, location)
    finally:
        scraper.close()


    print(f"[{datetime.now()}] Scrape completed. Found {len(results)} job(s).")
    return results