import os
from playwright.async_api import Page
from app.scrapers.base import BaseScraper, JobListing

DEBUG_DIR = "debug"


class GoogleScraper(BaseScraper):
    name = "Google"
    base_url = "https://www.google.com/about/careers/applications/jobs/results"

    async def scrape(self, page: Page) -> list[JobListing]:
        jobs = []
        first = True
        for term in self.SEARCH_TERMS:
            try:
                await page.goto(
                    f"{self.base_url}?q={term.replace(' ', '+')}&location=United+States",
                    wait_until="networkidle", timeout=45000,
                )
                await page.wait_for_timeout(3000)

                if first:
                    os.makedirs(DEBUG_DIR, exist_ok=True)
                    html = await page.content()
                    debug_path = os.path.join(DEBUG_DIR, "google_rendered.html")
                    with open(debug_path, "w", encoding="utf-8") as f:
                        f.write(html)
                    print(f"[Google] Saved rendered HTML -> {debug_path}  ({len(html):,} bytes)")
                    first = False

                cards = await page.query_selector_all(
                    "li[class*='lLd3Je'], [class*='job-result'], [jsname='N2UJec'] li"
                )
                for card in cards:
                    title_el = await card.query_selector("h3, h2, a[class*='WpHeLc'], a")
                    link_el = await card.query_selector("a[href*='/jobs/results/']")
                    if not title_el:
                        continue
                    title = await self._safe_text(title_el)
                    href = await self._safe_attr(link_el or title_el, "href")
                    if not title or not href:
                        continue
                    if not href.startswith("http"):
                        href = f"https://www.google.com{href}"
                    loc_el = await card.query_selector("[class*='location'], [class*='r0wTof']")
                    location = await self._safe_text(loc_el) if loc_el else ""
                    jobs.append(JobListing(title=title, url=href, location=location))
            except Exception as e:
                print(f"[Google] term '{term}' failed: {e}")

        return self._deduplicate(jobs)
