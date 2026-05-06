import os
from playwright.async_api import Page
from app.scrapers.base import BaseScraper, JobListing

DEBUG_DIR = "debug"


class InfineonScraper(BaseScraper):
    name = "Infineon"
    base_url = "https://jobs.infineon.com/careers"

    async def scrape(self, page: Page) -> list[JobListing]:
        jobs = []
        first = True
        for term in self.SEARCH_TERMS:
            try:
                await page.goto(
                    f"{self.base_url}?keywords={term.replace(' ', '%20')}&location=United+States",
                    wait_until="networkidle", timeout=45000,
                )
                await page.wait_for_timeout(3000)

                if first:
                    os.makedirs(DEBUG_DIR, exist_ok=True)
                    html = await page.content()
                    debug_path = os.path.join(DEBUG_DIR, "infineon_rendered.html")
                    with open(debug_path, "w", encoding="utf-8") as f:
                        f.write(html)
                    print(f"[Infineon] Saved rendered HTML -> {debug_path}  ({len(html):,} bytes)")
                    first = False

                cards = await page.query_selector_all(
                    ".phs-job-result-card, [class*='job-result'], [class*='job-card'], article"
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
                        href = f"https://jobs.infineon.com{href}"
                    loc_el = await card.query_selector("[class*='location'], [class*='city']")
                    location = await self._safe_text(loc_el) if loc_el else ""
                    jobs.append(JobListing(title=title, url=href, location=location))
            except Exception as e:
                print(f"[Infineon] term '{term}' failed: {e}")

        return self._deduplicate(jobs)
