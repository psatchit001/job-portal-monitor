from playwright.async_api import Page
from app.scrapers.base import BaseScraper, JobListing


class AppleScraper(BaseScraper):
    name = "Apple"
    base_url = "https://jobs.apple.com/en-us/search"

    async def scrape(self, page: Page) -> list[JobListing]:
        jobs = []
        for term in self.SEARCH_TERMS:
            try:
                await page.goto(
                    f"{self.base_url}?search={term.replace(' ', '+')}&sort=newest&location=united-states-USA",
                    wait_until="networkidle", timeout=45000,
                )
                await page.wait_for_timeout(3000)

                cards = await page.query_selector_all(
                    "table#search-results tbody tr, [class*='table-row'], .table--advanced-search tbody tr"
                )
                for card in cards:
                    title_el = await card.query_selector("td a, a[class*='result']")
                    if not title_el:
                        continue
                    title = await self._safe_text(title_el)
                    href = await self._safe_attr(title_el, "href")
                    if not title or not href:
                        continue
                    if not href.startswith("http"):
                        href = f"https://jobs.apple.com{href}"
                    loc_el = await card.query_selector("td:nth-child(3), [class*='location']")
                    location = await self._safe_text(loc_el) if loc_el else "United States"
                    jobs.append(JobListing(title=title, url=href, location=location))
            except Exception as e:
                print(f"[Apple] term '{term}' failed: {e}")

        return self._deduplicate(jobs)
