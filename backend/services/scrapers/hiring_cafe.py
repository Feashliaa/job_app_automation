# backend/services/hiring_cafe.py
import json
import urllib.parse
import re
from datetime import datetime
from selenium.webdriver.common.by import By
from backend.services.scrapers.base_scraper import BaseScraper

class HiringCafeScraper(BaseScraper):

    JOB_CARD_SELECTOR = "div.relative.xl\\:z-10"

    BASE_URL = "https://hiring.cafe/"

    DATE_POSTED_MAP = {
        "Past Month": 61,
        "Past Week": 14,
        "Past 3 Days": 4,
        "Past 24 Hours": 2,
    }

    EXPERIENCE_LEVEL_MAP = {
        "No Prior Experience": "No Prior Experience",
        "Entry Level": "Entry Level",
        "Mid Level": "Mid Level",
        "Senior Level": "Senior Level",
    }

    JOB_TITLE_QUERY_MAP = {
        "Software Engineer": "software+engineer",
        "Software Developer": "software+developer",
        "Quality Assurance Engineer": "quality+assurance+engineer",
        "Software Test Engineer": "software+test+engineer",
        "Automation Engineer": "automation+engineer",
        "Data Analyst": "data+analyst",
        "Frontend Developer": "frontend+developer",
        "Backend Developer": "backend+developer",
        "Web Developer": "web+developer",
        "Full-Stack Developer": "full+stack+developer",
    }

    def _build_search_url(self, date_posted, experience_level, job_title, location):
        
        # Map inputs to values or provide fallbacks
        date_posted_val = self.DATE_POSTED_MAP.get(date_posted, 14)
        exp_val = self.EXPERIENCE_LEVEL_MAP.get(experience_level, "Entry Level")
        
          # Normalize experience / seniority
        exp_norm = experience_level.strip().lower()
        
        # if entry level, add in "No Prior Experience" as well
        if exp_norm in (
                "entry level",
                "entry-level",
                "no prior experience",
                "no prior experience required",
            ):
            seniority_values = ["Entry Level", "No Prior Experience Required"]
        else:
            seniority_values = [exp_val]
            

        # if typed job title not in map, auto-generate token
        if job_title in self.JOB_TITLE_QUERY_MAP:
            job_val = self.JOB_TITLE_QUERY_MAP[job_title]
        else:
            job_val = urllib.parse.quote_plus(job_title.strip().lower())

        # Determine workplace type
        workplace_type = (
            ["Remote"] if "remote" in location.lower() else [location.title()]
        )

        # Build the JSON search state
        search_state = {
            "dateFetchedPastNDays": date_posted_val,
            "searchQuery": job_val,
            "workplaceTypes": workplace_type,
            "seniorityLevel": seniority_values,
        }

        # URL-encode the JSON
        encoded_state = urllib.parse.quote(json.dumps(search_state))

        return f"{self.BASE_URL}?searchState={encoded_state}"

    def _scrape_logic(self, url, location):  # core scraping logic
        
        print("inner:", self.driver.execute_script("return window.innerWidth"))
        
        self._go_to_url(url)
        
        print("screen:", self.driver.execute_script("return screen.width"))
        
        try:
            ok = self.driver.save_screenshot("/app/uploads/debug_wait.png")
            print("SCREENSHOT RETURN VALUE:", ok)
        except Exception as e:
            print("SCREENSHOT ERROR:", e)
        
        print("\n--- DEBUG PAGE INFO ---")
        print("URL:", self.driver.current_url)
        print("Title:", self.driver.title)
        print("Body Snippet:\n", self.driver.find_element(By.TAG_NAME, "body").text[:15000])
        print("--- END DEBUG ---\n")
        
        logs = self.driver.get_log("browser")
        for entry in logs:
            print("BROWSER LOG:", entry)

        # Wait for job postings to load
        result = self._wait_for_elements(HiringCafeScraper.JOB_CARD_SELECTOR)
        
        if result == "__CAUGHT_UP__":
            print("No new job postings found (caught up).")
            return []

        # Extract job cards using the appropriate selector
        job_cards = self.driver.find_elements(
            By.CSS_SELECTOR, HiringCafeScraper.JOB_CARD_SELECTOR
        )

        print(f"Found {len(job_cards)} job postings.")

        results = []
        for card in job_cards:
            try:
                title = card.find_element(
                    By.CSS_SELECTOR, "span.font-bold.text-start"
                ).text
            except:
                title = "N/A"
            try:
                company = card.find_element(
                    By.CSS_SELECTOR, "span.line-clamp-3.font-light span.font-bold"
                ).text
                # Remove trailing colon, e.g. "Navigant: " → "Navigant"
                company = company.rstrip(":").strip()
            except:
                company = "N/A"
            try:
                link = card.find_element(
                    By.CSS_SELECTOR, "a[href*='viewjob']"
                ).get_attribute("href")
            except:
                link = "N/A"

            salary = None
            try:
                spans = card.find_elements(
                    By.XPATH, ".//div[contains(@class, 'flex-wrap')]/span"
                )
                for s in spans:
                    text = s.text.strip()
                    if re.search(r"\$\s*\d", text):
                        salary = text
                        break
            except Exception as e:
                print(f"Salary extraction error: {e}")
                salary = None

            try:
                skills = card.find_element(
                    By.CSS_SELECTOR,
                    "div.flex.flex-col.space-y-1 span.line-clamp-2.font-light",
                ).text
            except:
                skills = "N/A"

            results.append(
                {
                    "JobTitle": title,
                    "Company": company,
                    "Location": location,
                    "Salary": salary,
                    "URL": link,
                    "Skills": skills,
                    "Status": "New",
                    "DateFound": datetime.today().date().isoformat(),
                }
            )

            print(f"Parsed: {title} | {company} | {skills[:60]} | {salary}")

        print(f"\nExtracted {len(results)} jobs:")

        print(f"Total jobs before filtering: {len(results)}")

        return results

    def scrape(self, date_posted, experience_level, job_title, location):
        print(
            f"[Hiring Cafe] Scraping '{job_title}' in '{location}' "
            f"({experience_level}, {date_posted})"
        )

        url = self._build_search_url(date_posted, experience_level, job_title, location)
        print(f"[Hiring Cafe] URL: {url}")

        results = self._scrape_logic(url, location)

        return results