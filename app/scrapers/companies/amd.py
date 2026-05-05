from playwright.async_api import Page
from app.scrapers.base import BaseScraper, JobListing


class AMDScraper(BaseScraper):
    name = "AMD"
    base_url = "https://careers.amd.com/careers-home/jobs"

    async def scrape(self, page: Page) -> list[JobListing]:
        jobs = []
        for term in self.SEARCH_TERMS:
            try:
                await page.goto(
                    f"{self.base_url}?keywords={term.replace(' ', '%20')}&location=United%20States&stretch=10&stretchUnit=MILES",
                    wait_until="networkidle", timeout=45000,
                )
                await page.wait_for_timeout(2500)

                cards = await page.query_selector_all("li[class*='jobs-list-item'], .job-list-item")
                for card in cards:
                    title_el = await card.query_selector("a[data-ph-at-id='job-link'], h2 a, h3 a, a")
                    if not title_el:
                        continue
                    title = await self._safe_text(title_el)
                    href = await self._safe_attr(title_el, "href")
                    if not title or not href:
                        continue
                    if not href.startswith("http"):
                        href = f"https://careers.amd.com{href}"
                    loc_el = await card.query_selector("[data-ph-at-id='job-location'], [class*='job-location']")
                    location = await self._safe_text(loc_el) if loc_el else ""
                    jobs.append(JobListing(title=title, url=href, location=location))
            except Exception as e:
                print(f"[AMD] term '{term}' failed: {e}")

        return self._deduplicate(jobs)
