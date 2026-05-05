from playwright.async_api import Page
from app.scrapers.base import BaseScraper, JobListing


class MicronScraper(BaseScraper):
    name = "Micron"
    base_url = "https://micron.wd1.myworkdayjobs.com/en-US/External"

    async def scrape(self, page: Page) -> list[JobListing]:
        jobs = []
        for term in self.SEARCH_TERMS:
            try:
                await page.goto(
                    f"{self.base_url}/jobs?q={term.replace(' ', '+')}",
                    wait_until="networkidle", timeout=45000,
                )
                await page.wait_for_timeout(3000)

                cards = await page.query_selector_all("li[class*='css-'] article, [data-automation-id='jobItem']")
                for card in cards:
                    title_el = await card.query_selector("[data-automation-id='jobPostingTitle'], a")
                    if not title_el:
                        continue
                    title = await self._safe_text(title_el)
                    href = await self._safe_attr(title_el, "href")
                    if not title or not href:
                        continue
                    if not href.startswith("http"):
                        href = f"https://micron.wd1.myworkdayjobs.com{href}"
                    loc_el = await card.query_selector("[data-automation-id='requisitionLocation'] dd, [class*='location']")
                    location = await self._safe_text(loc_el) if loc_el else ""
                    jobs.append(JobListing(title=title, url=href, location=location))
            except Exception as e:
                print(f"[Micron] term '{term}' failed: {e}")

        return self._deduplicate(jobs)
