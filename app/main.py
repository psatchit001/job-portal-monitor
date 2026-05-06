from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import init_db, get_db, Company, Job, ScrapeRun
from app.scrapers.runner import run_all_scrapers
from config import SCRAPE_INTERVAL_HOURS

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.add_job(run_all_scrapers, "interval", hours=SCRAPE_INTERVAL_HOURS, id="main_scrape")
    scheduler.start()
    print(f"[scheduler] Running every {SCRAPE_INTERVAL_HOURS} hours.")
    yield
    scheduler.shutdown()


app = FastAPI(title="Career Portal Monitor", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("static/index.html")


# ── Companies ─────────────────────────────────────────────────────────────────

@app.get("/api/companies")
def get_companies(db: Session = Depends(get_db)):
    companies = db.query(Company).order_by(Company.name).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "url": c.url,
            "industry": c.industry,
            "enabled": c.enabled,
            "last_scraped": c.last_scraped.isoformat() if c.last_scraped else None,
            "last_scrape_status": c.last_scrape_status,
            "jobs_found_last_run": c.jobs_found_last_run,
        }
        for c in companies
    ]


@app.patch("/api/companies/{company_id}/toggle")
def toggle_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    company.enabled = not company.enabled
    db.commit()
    return {"id": company.id, "enabled": company.enabled}


# ── Jobs ──────────────────────────────────────────────────────────────────────

@app.get("/api/jobs")
def get_jobs(
    company_id: int | None = None,
    status: str | None = None,
    seniority: str | None = None,
    matched_only: bool = True,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    q = db.query(Job).join(Company)

    if matched_only:
        q = q.filter(Job.matched_role != "")
    if company_id:
        q = q.filter(Job.company_id == company_id)
    if status:
        q = q.filter(Job.status == status)
    if seniority:
        q = q.filter(Job.seniority == seniority)
    if search:
        q = q.filter(Job.title.ilike(f"%{search}%"))

    total = q.count()
    jobs = q.order_by(desc(Job.first_seen)).offset(offset).limit(limit).all()

    return {
        "total": total,
        "jobs": [_job_dict(j) for j in jobs],
    }


@app.delete("/api/jobs")
def clear_all_jobs(db: Session = Depends(get_db)):
    deleted = db.query(Job).delete()
    db.commit()
    return {"deleted": deleted}


@app.patch("/api/jobs/{job_id}/status")
def update_job_status(job_id: int, body: dict, db: Session = Depends(get_db)):
    new_status = body.get("status")
    if new_status not in ("new", "saved", "applied", "not_interested"):
        raise HTTPException(status_code=400, detail="Invalid status")
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = new_status
    db.commit()
    return {"id": job.id, "status": job.status}


# ── Stats ─────────────────────────────────────────────────────────────────────

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total_jobs = db.query(Job).filter(Job.matched_role != "").count()
    new_jobs = db.query(Job).filter(Job.status == "new", Job.matched_role != "").count()
    saved = db.query(Job).filter(Job.status == "saved").count()
    applied = db.query(Job).filter(Job.status == "applied").count()
    companies_ok = db.query(Company).filter(Company.last_scrape_status == "ok").count()
    companies_err = db.query(Company).filter(Company.last_scrape_status == "error").count()
    last_run = db.query(ScrapeRun).order_by(desc(ScrapeRun.started_at)).first()

    return {
        "total_matched_jobs": total_jobs,
        "new": new_jobs,
        "saved": saved,
        "applied": applied,
        "companies_ok": companies_ok,
        "companies_error": companies_err,
        "last_run": last_run.completed_at.isoformat() if last_run and last_run.completed_at else None,
        "next_run_hours": SCRAPE_INTERVAL_HOURS,
    }


# ── Manual scrape trigger ─────────────────────────────────────────────────────

@app.post("/api/scrape")
async def trigger_scrape(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_all_scrapers)
    return {"message": "Scrape started in background"}


# ── Scrape history ────────────────────────────────────────────────────────────

@app.get("/api/runs")
def get_runs(limit: int = 10, db: Session = Depends(get_db)):
    runs = db.query(ScrapeRun).order_by(desc(ScrapeRun.started_at)).limit(limit).all()
    return [
        {
            "id": r.id,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "new_jobs": r.new_jobs,
            "companies_scraped": r.companies_scraped,
            "companies_failed": r.companies_failed,
        }
        for r in runs
    ]


def _job_dict(job: Job) -> dict:
    return {
        "id": job.id,
        "title": job.title,
        "url": job.url,
        "company": job.company.name if job.company else "",
        "company_id": job.company_id,
        "location": job.location,
        "department": job.department,
        "seniority": job.seniority,
        "match_score": job.match_score,
        "matched_role": job.matched_role,
        "status": job.status,
        "first_seen": job.first_seen.isoformat() if job.first_seen else None,
        "is_active": job.is_active,
    }
