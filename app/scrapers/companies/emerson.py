from playwright.async_api import Page
from app.scrapers.base import BaseScraper, JobListing


class EmersonScraper(BaseScraper):
    name = "Emerson"
    base_url = "https://hdjq.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/jobs"

    async def scrape(self, page: Page) -> list[JobListing]:
        jobs = []
        for term in self.SEARCH_TERMS:
            try:
                await page.goto(
                    f"{self.base_url}?keyword={term.replace(' ', '+')}",
                    wait_until="networkidle", timeout=45000,
                )
                await page.wait_for_timeout(3000)

                cards = await page.query_selector_all(
                    "[class*='job-list-item'], .job-list li, [data-bind*='job'], article"
                )
                for card in cards:
                    title_el = await card.query_selector("h2 a, h3 a, a[class*='job-title'], a")
                    if not title_el:
                        continue
                    title = await self._safe_text(title_el)
                    href = await self._safe_attr(title_el, "href")
                    if not title or not href:
                        continue
                    if not href.startswith("http"):
                        href = f"https://hdjq.fa.us2.oraclecloud.com{href}"
                    loc_el = await card.query_selector("[class*='location']")
                    location = await self._safe_text(loc_el) if loc_el else ""
                    jobs.append(JobListing(title=title, url=href, location=location))
            except Exception as e:
                print(f"[Emerson] term '{term}' failed: {e}")

        return self._deduplicate(jobs)
