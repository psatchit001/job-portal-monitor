import os
from playwright.async_api import Page
from app.scrapers.base import BaseScraper, JobListing

DEBUG_DIR = "debug"


class TIScraper(BaseScraper):
    name = "Texas Instruments"
    base_url = "https://careers.ti.com/en/sites/CX/jobs"

    async def scrape(self, page: Page) -> list[JobListing]:
        jobs = []
        page_num = 0
        max_pages = 10  # ~25 jobs/page → up to 250 roles

        while page_num < max_pages:
            try:
                url = (
                    f"{self.base_url}?location=United+States&page={page_num}"
                    if page_num > 0
                    else f"{self.base_url}?location=United+States"
                )

                print(f"[TI] Fetching page {page_num}: {url}")
                await page.goto(url, wait_until="networkidle", timeout=45000)
                await page.wait_for_timeout(3000)

                if page_num == 0:
                    os.makedirs(DEBUG_DIR, exist_ok=True)
                    html = await page.content()
                    debug_path = os.path.join(DEBUG_DIR, "ti_rendered.html")
                    with open(debug_path, "w", encoding="utf-8") as f:
                        f.write(html)
                    print(f"[TI] Saved rendered HTML -> {debug_path}  ({len(html):,} bytes)")

                containers = await page.query_selector_all(".job-tile.job-list-item")
                print(f"[TI] Page {page_num}: {len(containers)} job tile containers")

                if not containers:
                    print(f"[TI] Page {page_num}: no containers — stopping")
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
                        href = f"https://careers.ti.com{href}"

                    loc_el = await container.query_selector("[data-bind*='primaryLocation']")
                    location = await self._safe_text(loc_el) if loc_el else "United States"

                    jobs.append(JobListing(title=title, url=href, location=location))

                new_this_page = len(jobs) - jobs_before
                print(f"[TI] Page {page_num}: added {new_this_page} jobs")

                if new_this_page == 0:
                    print(f"[TI] No new jobs on page {page_num} — done paginating")
                    break

                next_btn = await page.query_selector(
                    "[aria-label='Next'], [class*='next-page'], button[data-ph-at-id='pagination-next-link']"
                )
                if not next_btn:
                    print(f"[TI] No next-page button — done paginating")
                    break

                page_num += 1

            except Exception as e:
                print(f"[TI] Page {page_num} failed: {e}")
                break

        result = self._deduplicate(jobs)
        print(f"[TI] Total unique jobs collected: {len(result)}")
        return result
