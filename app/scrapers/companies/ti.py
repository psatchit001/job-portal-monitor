from playwright.async_api import Page
from app.scrapers.base import BaseScraper, JobListing


class TIScraper(BaseScraper):
    name = "Texas Instruments"
    base_url = "https://careers.ti.com/en/sites/CX/jobs"

    async def scrape(self, page: Page) -> list[JobListing]:
        jobs = []
        for term in self.SEARCH_TERMS:
            try:
                await page.goto(
                    f"{self.base_url}?keyword={term.replace(' ', '+')}&location=United+States",
                    wait_until="networkidle", timeout=45000,
                )
                await page.wait_for_timeout(2000)

                cards = await page.query_selector_all("article.job-tile, li.job-tile, [class*='job-tile']")
                if not cards:
                    cards = await page.query_selector_all("[data-ph-at-id='job-link'], a[href*='/jobs/']")

                for card in cards:
                    title_el = await card.query_selector("h2, h3, [class*='title'], a")
                    link_el = await card.query_selector("a[href*='/jobs/']")
                    if not title_el:
                        continue
                    title = await self._safe_text(title_el)
                    href = await self._safe_attr(link_el or title_el, "href") if link_el else await self._safe_attr(title_el, "href")
                    if not title or not href:
                        continue
                    if not href.startswith("http"):
                        href = f"https://careers.ti.com{href}"
                    loc_el = await card.query_selector("[class*='location'], [data-ph-at-id*='location']")
                    location = await self._safe_text(loc_el) if loc_el else "United States"
                    jobs.append(JobListing(title=title, url=href, location=location))
            except Exception as e:
                print(f"[TI] term '{term}' failed: {e}")

        return self._deduplicate(jobs)
