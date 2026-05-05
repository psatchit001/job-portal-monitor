from playwright.async_api import Page
from app.scrapers.base import BaseScraper, JobListing


class HCLTechScraper(BaseScraper):
    name = "HCL Tech"
    base_url = "https://careers.hcltech.com/go/NonTPDemand/9558355/"

    async def scrape(self, page: Page) -> list[JobListing]:
        jobs = []
        for term in self.SEARCH_TERMS:
            try:
                await page.goto(self.base_url, wait_until="networkidle", timeout=45000)
                await page.wait_for_timeout(2000)

                # SAP SuccessFactors — look for search input
                search = await page.query_selector(
                    "input[id*='search'], input[placeholder*='Search'], input[placeholder*='keyword']"
                )
                if search:
                    await search.triple_click()
                    await search.type(term)
                    await page.keyboard.press("Enter")
                    await page.wait_for_load_state("networkidle", timeout=20000)
                    await page.wait_for_timeout(2000)

                cards = await page.query_selector_all(
                    "[class*='job-item'], [class*='jobListing'], [class*='job-result'], .job-list li"
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
                        href = f"https://careers.hcltech.com{href}"
                    loc_el = await card.query_selector("[class*='location'], [class*='city']")
                    location = await self._safe_text(loc_el) if loc_el else ""
                    jobs.append(JobListing(title=title, url=href, location=location))
            except Exception as e:
                print(f"[HCL Tech] term '{term}' failed: {e}")

        return self._deduplicate(jobs)
