import os
from playwright.async_api import Page
from app.scrapers.base import BaseScraper, JobListing

DEBUG_DIR = "debug"


class EmersonScraper(BaseScraper):
    name = "Emerson"
    base_url = "https://hdjq.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/jobs"

    async def scrape(self, page: Page) -> list[JobListing]:
        jobs = []

        for term in self.SEARCH_TERMS:
            page_num = 0
            max_pages = 5

            while page_num < max_pages:
                try:
                    url = (
                        f"{self.base_url}?keyword={term.replace(' ', '+')}&location=United+States&page={page_num}"
                        if page_num > 0
                        else f"{self.base_url}?keyword={term.replace(' ', '+')}&location=United+States"
                    )

                    print(f"[Emerson] term='{term}' page={page_num}: {url}")
                    await page.goto(url, wait_until="networkidle", timeout=45000)
                    await page.wait_for_timeout(3000)

                    if term == self.SEARCH_TERMS[0] and page_num == 0:
                        os.makedirs(DEBUG_DIR, exist_ok=True)
                        html = await page.content()
                        debug_path = os.path.join(DEBUG_DIR, "emerson_rendered.html")
                        with open(debug_path, "w", encoding="utf-8") as f:
                            f.write(html)
                        print(f"[Emerson] Saved rendered HTML -> {debug_path}  ({len(html):,} bytes)")

                    containers = await page.query_selector_all(".job-tile.job-list-item")
                    print(f"[Emerson] term='{term}' page={page_num}: {len(containers)} containers")

                    if not containers:
                        break

                    jobs_before = len(jobs)
                    for container in containers:
                        title_el = await container.query_selector("span.job-tile__title")
                        title = await self._safe_text(title_el) if title_el else ""

                        link_el = await container.query_selector("a.job-list-item__link")
                        href = await self._safe_attr(link_el, "href") if link_el else ""

                        if not title or not href:
                            continue
                        if not href.startswith("http"):
                            href = f"https://hdjq.fa.us2.oraclecloud.com{href}"

                        loc_el = await container.query_selector("[data-bind*='primaryLocation']")
                        location = await self._safe_text(loc_el) if loc_el else "United States"

                        jobs.append(JobListing(title=title, url=href, location=location))

                    new_this_page = len(jobs) - jobs_before
                    print(f"[Emerson] term='{term}' page={page_num}: added {new_this_page} jobs")

                    if new_this_page == 0:
                        break

                    next_btn = await page.query_selector(
                        "[aria-label='Next'], [class*='next-page'], button[data-ph-at-id='pagination-next-link']"
                    )
                    if not next_btn:
                        break

                    page_num += 1

                except Exception as e:
                    print(f"[Emerson] term='{term}' page={page_num} failed: {e}")
                    break

        result = self._deduplicate(jobs)
        print(f"[Emerson] Total unique jobs collected: {len(result)}")
        return result
