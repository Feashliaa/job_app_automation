import urllib.parse
from datetime import datetime
from backend.services.scrapers.base_scraper import BaseScraper


class LinkedInScraper(BaseScraper):
    """LinkedIn scraper (U.S. only)."""
    
    COMPANYS_TO_IGNORE = {
        "Jobs via Dice",
        "Mindrift",
        ""
    }

    BASE_URL = "https://www.linkedin.com/jobs/search/"
    GEO_ID_US = 103644278

    EXPERIENCE_LEVEL_MAP = {
        "Entry Level": 2, 
        "Mid Level": 3, 
        "Senior Level": 4
    }
    
    DATE_POSTED_MAP = {
        "Past 24 Hours": "r86400",
        "Past Week": "r604800",
        "Past Month": "r2592000",
    }
    
    WORKPLACE_TYPE_MAP = {
        "On-site": 1, 
        "Remote": 2, 
        "Hybrid": 3
    }

    def _build_search_url(self, date_posted, experience_level, job_title, location):
        params = {
            "f_E": self.EXPERIENCE_LEVEL_MAP.get(experience_level, 2),
            "f_TPR": self.DATE_POSTED_MAP.get(date_posted, "r604800"),
            "keywords": job_title.replace(" ", " "),
            "geoId": self.GEO_ID_US,
            "f_WT": self._get_workplace_type(location),
            "origin": "JOB_SEARCH_PAGE_JOB_FILTER",
            "refresh": "true",
        }
        query = urllib.parse.urlencode(params)
        return f"{self.BASE_URL}?{query}"

    def _get_workplace_type(self, location):
        return self.WORKPLACE_TYPE_MAP["Remote"] if "remote" in location.lower() else self.WORKPLACE_TYPE_MAP["On-site"]

    def scrape(self, date_posted, experience_level, job_title, location):
        url = self._build_search_url(date_posted, experience_level, job_title, location)
        print(f"[LinkedIn] URL: {url}")

        results = self._scrape_logic(url, job_title, location, date_posted, location)
        
        if not results:
            results = [{
                "JobTitle": job_title,
                "Company": "LinkedIn (Mock)",
                "Location": location,
                "URL": url,
                "Status": "New",
                "DateFound": datetime.today().date().isoformat(),
            }]
        
        return results

    def _scrape_logic(self, url, job_title, location, date_posted, experience_level):
        
        print("Entered _scrape_logic")
        
        self._go_to_url(url)
        
        self._wait_for_elements("ul.jobs-search__results-list")
        
        print(f"Found Element")
        
        results = []
        
        return results