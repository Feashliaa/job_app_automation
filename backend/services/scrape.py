# backend/services/scrape.py

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.services.scrapers.linkedin_scraper import LinkedInScraper
from backend.services.scrapers.hiring_cafe import HiringCafeScraper

def run_scraper(date_posted: str, 
                experience_level: str, 
                job_title: str, 
                location: str):
    """
    Entry point to run the appropriate scraper based on the platform.
    Returns a list of job dicts formatted to match the 'jobs' table.
    """

    print(f"[{datetime.now()}] Starting scrape for ...")

    scrapers = [
        ("Hiring Cafe", HiringCafeScraper()),
        #("LinkedIn", LinkedInScraper())
    ]
    
    results = []
    start = datetime.now()
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
                try:
                    scraper.close()
                except Exception as e:
                    print(f"[{name}] Failed: {e}")

    print(f"Total scrape time: {(datetime.now() - start).total_seconds():.2f}s")
    print(f"[{datetime.now()}] All scrapers completed. Total: {len(results)} jobs.")
    return results 