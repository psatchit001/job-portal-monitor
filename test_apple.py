"""
Run this to scrape only Apple and see every job detail in the terminal.

Usage:
    python test_apple.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from playwright.async_api import async_playwright
from app.scrapers.companies.apple import AppleScraper
from app.matcher import compute_match, detect_seniority

TARGET_KEYWORDS = ["software", "engineer", "ai", "ml", "machine learning",
                   "artificial intelligence", "data", "developer"]

DIVIDER = "-" * 70


async def main():
    scraper = AppleScraper()

    print(DIVIDER)
    print("  Apple -- Job Scraper Test")
    print(DIVIDER)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            ignore_https_errors=True,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        print("\n[1/3] Launching Playwright browser and navigating to Apple careers...\n")
        all_jobs = await scraper.scrape(page)

        await context.close()
        await browser.close()

    print(f"\n{DIVIDER}")
    print(f"  RAW SCRAPE COMPLETE - {len(all_jobs)} total unique jobs found")
    print(DIVIDER)

    print("\n[2/3] Filtering for Software / AI / ML related roles...\n")

    relevant = []
    for job in all_jobs:
        title_lower = job.title.lower()
        if any(kw in title_lower for kw in TARGET_KEYWORDS):
            relevant.append(job)

    print(f"  {len(relevant)} jobs matched keyword filter out of {len(all_jobs)} total")

    print(f"\n[3/3] Running semantic matcher on {len(relevant)} jobs...\n")
    print(DIVIDER)

    matched = []
    for job in relevant:
        score, matched_role = compute_match(job.title, job.description)
        seniority = detect_seniority(job.title, job.description)

        bar_filled = round(score * 20)
        bar = "#" * bar_filled + "." * (20 - bar_filled)

        print(f"  Title    : {job.title}")
        print(f"  URL      : {job.url}")
        print(f"  Location : {job.location or 'Not specified'}")
        print(f"  Seniority: {seniority}")
        print(f"  Score    : [{bar}] {round(score * 100)}%  ->  {matched_role or 'No match'}")
        print()

        if matched_role:
            matched.append((job, score, matched_role, seniority))

    print(DIVIDER)
    print(f"\n  SUMMARY")
    print(f"  Total jobs scraped from Apple      : {len(all_jobs)}")
    print(f"  After keyword filter (SW/AI/ML)    : {len(relevant)}")
    print(f"  After semantic match               : {len(matched)}")
    print()

    if matched:
        print("  MATCHED JOBS:")
        for job, score, role, seniority in sorted(matched, key=lambda x: -x[1]):
            print(f"    [{round(score*100):3d}%] [{seniority:12s}] [{role:18s}] {job.title}")
    else:
        print("  No jobs passed the semantic match threshold.")
        print("  Check debug/apple_rendered.html to inspect the raw page HTML.")

    print(f"\n{DIVIDER}\n")


if __name__ == "__main__":
    asyncio.run(main())
