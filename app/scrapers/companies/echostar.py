from playwright.async_api import Page
from app.scrapers.base import BaseScraper, JobListing


class EchoStarScraper(BaseScraper):
    name = "EchoStar"
    base_url = "https://jobs.echostar.com/jobs"

    async def scrape(self, page: Page) -> list[JobListing]:
        jobs = []
        for term in self.SEARCH_TERMS:
            try:
                await page.goto(
                    f"{self.base_url}?keywords={term.replace(' ', '%20')}&location=United+States",
                    wait_until="networkidle", timeout=45000,
                )
                await page.wait_for_timeout(3000)

                # iCIMS portal
                cards = await page.query_selector_all(
                    "[class*='iCIMS_JobsTable'] tr, [class*='job-listing'], article.job"
                )
                for card in cards:
                    title_el = await card.query_selector("a[href*='/job/'], h2 a, h3 a, a")
                    if not title_el:
                        continue
                    title = await self._safe_text(title_el)
                    href = await self._safe_attr(title_el, "href")
                    if not title or not href:
                        continue
                    if not href.startswith("http"):
                        href = f"https://jobs.echostar.com{href}"
                    loc_el = await card.query_selector("[class*='location'], td:nth-child(2)")
                    location = await self._safe_text(loc_el) if loc_el else ""
                    jobs.append(JobListing(title=title, url=href, location=location))
            except Exception as e:
                print(f"[EchoStar] term '{term}' failed: {e}")

        return self._deduplicate(jobs)
