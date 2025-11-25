import json
import urllib.parse
import re
import asyncio
import random
from datetime import datetime
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
        date_posted_val = self.DATE_POSTED_MAP.get(date_posted, 14)
        exp_val = self.EXPERIENCE_LEVEL_MAP.get(experience_level, "Entry Level")

        if job_title in self.JOB_TITLE_QUERY_MAP:
            job_val = self.JOB_TITLE_QUERY_MAP[job_title]
        else:
            job_val = urllib.parse.quote_plus(job_title.strip().lower())

        workplace_type = ["Remote"] if "remote" in location.lower() else [location.title()]

        search_state = {
            "dateFetchedPastNDays": date_posted_val,
            "searchQuery": job_val,
            "workplaceTypes": workplace_type,
            "seniorityLevel": [exp_val],
        }

        encoded_state = urllib.parse.quote(json.dumps(search_state))
        return f"{self.BASE_URL}?searchState={encoded_state}"

    async def _scrape_logic(self, url, job_title, location, date_posted, experience_level):

        await self._go_to_url(url)

        # Wait for job cards
        job_cards = await self._wait_for_elements(self.JOB_CARD_SELECTOR)

        if not isinstance(job_cards, list):
            job_cards = [job_cards]

        print(f"Found {len(job_cards)} job postings.")

        results = []

        for card in job_cards:
            # TITLE
            try:
                title_el = await card.query_selector("span.font-bold.text-start")
                title_text = await title_el.text_content() if title_el else ""
                title = title_text.strip() if title_text else "N/A"
            except Exception:
                title = "N/A"

            # COMPANY
            try:
                company_el = await card.query_selector("span.line-clamp-3.font-light span.font-bold")
                company_text = await company_el.text_content() if company_el else ""
                company = company_text.strip().rstrip(":").strip() if company_text else "N/A"
            except Exception:
                company = "N/A"

            # LINK
            try:
                link_el = await card.query_selector("a[href*='viewjob']")
                link = await link_el.get_attribute("href") if link_el else "N/A"
                # If relative link, make absolute
                if link and link.startswith("/"):
                    link = urllib.parse.urljoin(self.BASE_URL, link)
            except Exception:
                link = "N/A"

            # SALARY
            salary = None
            try:
                spans = await card.query_selector_all("div.flex-wrap span")
                for s in spans:
                    text = await s.text_content() or ""
                    text = text.strip()
                    if re.search(r"\$\s*\d", text):
                        salary = text
                        break
            except Exception:
                salary = None

            # SKILLS
            try:
                skills_el = await card.query_selector("div.flex.flex-col.space-y-1 span.line-clamp-2.font-light")
                skills_text = await skills_el.text_content() if skills_el else ""
                skills = skills_text.strip() if skills_text else "N/A"
            except Exception:
                skills = "N/A"

            results.append({
                "JobTitle": title,
                "Company": company,
                "Location": location,
                "Salary": salary,
                "URL": link,
                "Skills": skills,
                "Status": "New",
                "DateFound": datetime.today().date().isoformat(),
            })

            print(f"Parsed: {title} | {company} | {skills[:60]} | {salary}")

            await asyncio.sleep(0.1 + random.random() * 0.2)

        print(f"\nExtracted {len(results)} jobs.")
        return results

    async def scrape(self, date_posted, experience_level, job_title, location, cdp_url: str = "http://localhost:9222"):
        """Public async entry point."""
        print(
            f"[Hiring Cafe] Scraping '{job_title}' in '{location}' "
            f"({experience_level}, {date_posted})"
        )

        url = self._build_search_url(date_posted, experience_level, job_title, location)
        print(f"[Hiring Cafe] URL: {url}")

        # ensure browser/page is started and attached to real Chrome
        if not self.page:
            await self.start(cdp_url=cdp_url)

        return await self._scrape_logic(
            url, job_title, location, date_posted, experience_level
        )
