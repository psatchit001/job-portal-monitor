import os
from playwright.async_api import Page
from app.scrapers.base import BaseScraper, JobListing

DEBUG_DIR = "debug"


class CognizantScraper(BaseScraper):
    name = "Cognizant"
    base_url = "https://careers.cognizant.com/global-en/jobs"

    async def scrape(self, page: Page) -> list[JobListing]:
        jobs = []
        first = True
        for term in self.SEARCH_TERMS:
            try:
                await page.goto(
                    f"{self.base_url}?keyword={term.replace(' ', '%20')}&location=United+States",
                    wait_until="networkidle", timeout=45000,
                )
                await page.wait_for_timeout(3000)

                if first:
                    os.makedirs(DEBUG_DIR, exist_ok=True)
                    html = await page.content()
                    debug_path = os.path.join(DEBUG_DIR, "cognizant_rendered.html")
                    with open(debug_path, "w", encoding="utf-8") as f:
                        f.write(html)
                    print(f"[Cognizant] Saved rendered HTML -> {debug_path}  ({len(html):,} bytes)")
                    first = False

                cards = await page.query_selector_all(
                    "[class*='job-card'], [class*='job-item'], [class*='job-listing'], article.job"
                )
                for card in cards:
                    title_el = await card.query_selector("h2 a, h3 a, a[class*='title'], a")
                    if not title_el:
                        continue
                    title = await self._safe_text(title_el)
                    href = await self._safe_attr(title_el, "href")
                    if not title or not href:
                        continue
                    if not href.startswith("http"):
                        href = f"https://careers.cognizant.com{href}"
                    loc_el = await card.query_selector("[class*='location'], [class*='city']")
                    location = await self._safe_text(loc_el) if loc_el else ""
                    jobs.append(JobListing(title=title, url=href, location=location))
            except Exception as e:
                print(f"[Cognizant] term '{term}' failed: {e}")

        return self._deduplicate(jobs)
