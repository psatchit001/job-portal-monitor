from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship, Session, sessionmaker
from datetime import datetime
from config import DATABASE_URL


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    industry = Column(String, default="technology")
    enabled = Column(Boolean, default=True)
    last_scraped = Column(DateTime, nullable=True)
    last_scrape_status = Column(String, default="never")  # never, ok, error
    jobs_found_last_run = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    location = Column(String, default="")
    department = Column(String, default="")
    seniority = Column(String, default="unspecified")  # internship, new_grad, entry_level, mid, senior+, unspecified
    description = Column(Text, default="")
    match_score = Column(Float, default=0.0)
    matched_role = Column(String, default="")  # which of the 6 roles it matched
    status = Column(String, default="new")  # new, saved, applied, not_interested
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    notified = Column(Boolean, default=False)

    company = relationship("Company", back_populates="jobs")


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_jobs_found = Column(Integer, default=0)
    new_jobs = Column(Integer, default=0)
    companies_scraped = Column(Integer, default=0)
    companies_failed = Column(Integer, default=0)
    errors = Column(Text, default="")


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(bind=engine)
    _seed_companies()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


COMPANIES = [
    {"name": "Texas Instruments", "url": "https://careers.ti.com/en/sites/CX", "industry": "semiconductor"},
    {"name": "AMD", "url": "https://careers.amd.com/careers-home/jobs", "industry": "semiconductor"},
    {"name": "Micron", "url": "https://careers.micron.com", "industry": "semiconductor"},
    {"name": "Microchip Technology", "url": "https://wd5.myworkdaysite.com/en-US/recruiting/microchiphr/External", "industry": "semiconductor"},
    {"name": "Infineon", "url": "https://jobs.infineon.com/careers", "industry": "semiconductor"},
    {"name": "Analog Devices", "url": "https://analogdevices.wd1.myworkdayjobs.com/External", "industry": "semiconductor"},
    {"name": "NVIDIA", "url": "https://jobs.nvidia.com/careers", "industry": "semiconductor"},
    {"name": "Intel", "url": "https://intel.wd1.myworkdayjobs.com/External", "industry": "semiconductor"},
    {"name": "Emerson", "url": "https://hdjq.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/jobs", "industry": "technology"},
    {"name": "Samsung", "url": "https://sec.wd3.myworkdayjobs.com/Samsung_Careers", "industry": "semiconductor"},
    {"name": "HCL Tech", "url": "https://careers.hcltech.com/go/NonTPDemand/9558355/", "industry": "technology"},
]


def _seed_companies():
    db = SessionLocal()
    try:
        for c in COMPANIES:
            exists = db.query(Company).filter(Company.name == c["name"]).first()
            if not exists:
                db.add(Company(**c))
        db.commit()
    finally:
        db.close()
