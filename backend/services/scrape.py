# backend/services/scrape.py

import asyncio
from datetime import datetime
from backend.services.scrapers.hiring_cafe import HiringCafeScraper
# from backend.services.scrapers.linkedin_scraper import LinkedInScraper


async def run_scraper(date_posted: str,
                      experience_level: str,
                      job_title: str,
                      location: str):
    """
    Async entry point for running scrapers.
    All scrapers must be async-compatible.
    """

    print(f"[{datetime.now()}] Starting scrape for ...")

    scrapers = [
        ("Hiring Cafe", HiringCafeScraper()),
        # ("LinkedIn", LinkedInScraper())  # must also be async to work here
    ]

    results = []
    start = datetime.now()

    # Start all scrapers asynchronously
    tasks = []

    for name, scraper in scrapers:
        async def run_single_scraper(name=name, scraper=scraper):
            try:
                await scraper.start()
                data = await scraper.scrape(date_posted, experience_level, job_title, location)
                print(f"[{name}] Completed with {len(data)} results.")
                return data
            except Exception as e:
                print(f"[{name}] Failed: {e}")
                return []
            finally:
                await scraper.close()

        tasks.append(run_single_scraper())

    # Run them concurrently
    results_lists = await asyncio.gather(*tasks)

    # Flatten results
    for lst in results_lists:
        results.extend(lst)

    print(f"Total scrape time: {(datetime.now() - start).total_seconds():.2f}s")
    print(f"[{datetime.now()}] All scrapers completed. Total: {len(results)} jobs.")

    return results
