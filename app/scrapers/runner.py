"""
Orchestrates all 17 company scrapers.
Runs them sequentially (one browser instance, one company at a time).
Saves results to DB, runs semantic matching, sends Discord notifications.
"""
import asyncio
import traceback
from datetime import datetime

from playwright.async_api import async_playwright
from sqlalchemy.orm import Session

from app.database import SessionLocal, Company, Job, ScrapeRun
from app.matcher import compute_match, detect_seniority
from app.notifier import send_new_jobs, send_scrape_summary
from app.scrapers.base import JobListing

from app.scrapers.companies.ti import TIScraper
from app.scrapers.companies.amd import AMDScraper
from app.scrapers.companies.micron import MicronScraper
from app.scrapers.companies.microchip import MicrochipScraper
from app.scrapers.companies.infineon import InfineonScraper
from app.scrapers.companies.analog_devices import AnalogDevicesScraper
from app.scrapers.companies.nvidia import NVIDIAScraper
from app.scrapers.companies.intel import IntelScraper
from app.scrapers.companies.emerson import EmersonScraper
from app.scrapers.companies.samsung import SamsungScraper
from app.scrapers.companies.tcs import TCSScraper
from app.scrapers.companies.apple import AppleScraper
from app.scrapers.companies.cognizant import CognizantScraper
from app.scrapers.companies.google import GoogleScraper
from app.scrapers.companies.hcltech import HCLTechScraper
from app.scrapers.companies.marvell import MarvellScraper
from app.scrapers.companies.echostar import EchoStarScraper

SCRAPERS = [
    TIScraper, AMDScraper, MicronScraper, MicrochipScraper,
    InfineonScraper, AnalogDevicesScraper, NVIDIAScraper, IntelScraper,
    EmersonScraper, SamsungScraper, TCSScraper, AppleScraper,
    CognizantScraper, GoogleScraper, HCLTechScraper, MarvellScraper,
    EchoStarScraper,
]


def _save_jobs(db: Session, company: Company, listings: list[JobListing]) -> list[Job]:
    """Persist scraped listings. Returns only the brand-new ones."""
    new_jobs = []
    now = datetime.utcnow()

    for listing in listings:
        existing = db.query(Job).filter(Job.url == listing.url).first()
        if existing:
            existing.last_seen = now
            existing.is_active = True
        else:
            score, matched_role = compute_match(listing.title, listing.description)
            seniority = detect_seniority(listing.title, listing.description)
            job = Job(
                company_id=company.id,
                title=listing.title,
                url=listing.url,
                location=listing.location,
                department=listing.department,
                description=listing.description,
                match_score=score,
                matched_role=matched_role,
                seniority=seniority,
                first_seen=now,
                last_seen=now,
            )
            db.add(job)
            if matched_role:
                new_jobs.append(job)

    # Mark jobs no longer appearing as inactive
    seen_urls = {l.url for l in listings}
    for job in db.query(Job).filter(Job.company_id == company.id, Job.is_active == True).all():
        if job.url not in seen_urls:
            job.is_active = False

    db.commit()

    # Reload to get relationships populated
    for job in new_jobs:
        db.refresh(job)
    return new_jobs


async def run_all_scrapers() -> dict:
    """Entry point called by the scheduler and the manual-trigger API."""
    db = SessionLocal()
    run = ScrapeRun(started_at=datetime.utcnow())
    db.add(run)
    db.commit()

    total_new = 0
    companies_ok = 0
    companies_failed = 0
    all_new_jobs = []
    errors = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)

        for ScraperClass in SCRAPERS:
            scraper = ScraperClass()
            company = db.query(Company).filter(Company.name == scraper.name).first()
            if not company or not company.enabled:
                continue

            page = await browser.new_page()
            await page.set_extra_http_headers({
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            })

            try:
                print(f"[runner] Scraping {scraper.name}...")
                listings = await scraper.scrape(page)
                new_jobs = _save_jobs(db, company, listings)
                company.last_scraped = datetime.utcnow()
                company.last_scrape_status = "ok"
                company.jobs_found_last_run = len(listings)
                db.commit()

                total_new += len(new_jobs)
                all_new_jobs.extend(new_jobs)
                companies_ok += 1
                print(f"[runner] {scraper.name}: {len(listings)} jobs, {len(new_jobs)} new matches")

            except Exception:
                tb = traceback.format_exc()
                print(f"[runner] {scraper.name} FAILED:\n{tb}")
                company.last_scrape_status = "error"
                db.commit()
                companies_failed += 1
                errors.append(f"{scraper.name}: {tb[:300]}")

            finally:
                await page.close()

        await browser.close()

    run.completed_at = datetime.utcnow()
    run.total_jobs_found = sum(c.jobs_found_last_run or 0 for c in db.query(Company).all())
    run.new_jobs = total_new
    run.companies_scraped = companies_ok
    run.companies_failed = companies_failed
    run.errors = "\n---\n".join(errors)
    db.commit()
    db.close()

    await send_new_jobs(all_new_jobs)
    await send_scrape_summary(total_new, companies_ok, companies_failed)

    return {
        "new_jobs": total_new,
        "companies_ok": companies_ok,
        "companies_failed": companies_failed,
    }
