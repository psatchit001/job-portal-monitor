import os
from playwright.async_api import Page
from app.scrapers.base import BaseScraper, JobListing

DEBUG_DIR = "debug"


class TCSScraper(BaseScraper):
    name = "TCS"
    base_url = "https://ibegin.tcsapps.com/candidate/"

    async def scrape(self, page: Page) -> list[JobListing]:
        jobs = []
        try:
            await page.goto(self.base_url, wait_until="networkidle", timeout=45000)
            await page.wait_for_timeout(3000)

            os.makedirs(DEBUG_DIR, exist_ok=True)
            html = await page.content()
            debug_path = os.path.join(DEBUG_DIR, "tcs_rendered.html")
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"[TCS] Saved rendered HTML -> {debug_path}  ({len(html):,} bytes)")

            # TCS uses a custom Angular portal — look for a search input
            search = await page.query_selector("input[placeholder*='Search'], input[placeholder*='search'], input[type='search']")
            if search:
                for term in self.SEARCH_TERMS[:3]:  # limit requests on custom portals
                    await search.triple_click()
                    await search.type(term)
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(2500)

                    cards = await page.query_selector_all(".job-card, [class*='job-item'], [class*='job-listing'], li[class*='job']")
                    for card in cards:
                        title_el = await card.query_selector("h2, h3, a, [class*='title']")
                        if not title_el:
                            continue
                        title = await self._safe_text(title_el)
                        href = await self._safe_attr(title_el, "href")
                        if not title:
                            continue
                        if href and not href.startswith("http"):
                            href = f"https://ibegin.tcsapps.com{href}"
                        jobs.append(JobListing(title=title, url=href or self.base_url, location="United States"))
            else:
                # Fallback: grab whatever jobs are visible on load
                cards = await page.query_selector_all(".job-card, [class*='job-item'], li[class*='job']")
                for card in cards:
                    title_el = await card.query_selector("h2, h3, a")
                    if not title_el:
                        continue
                    title = await self._safe_text(title_el)
                    href = await self._safe_attr(title_el, "href") or self.base_url
                    if title:
                        jobs.append(JobListing(title=title, url=href, location="United States"))

        except Exception as e:
            print(f"[TCS] scrape failed: {e}")

        return self._deduplicate(jobs)
