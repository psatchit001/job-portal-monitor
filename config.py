import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
MATCHER_BACKEND = os.getenv("MATCHER_BACKEND", "local")  # "local" or "openai"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SCRAPE_INTERVAL_HOURS = int(os.getenv("SCRAPE_INTERVAL_HOURS", "3"))
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.30"))
DATABASE_URL = "sqlite:///./jobs.db"

# What you're looking for — used for semantic matching
TARGET_ROLE_DESCRIPTIONS = [
    "AI Engineer: artificial intelligence, machine learning, deep learning, LLM, generative AI, NLP, computer vision, model deployment",
    "ML Engineer: machine learning, MLOps, model training, feature engineering, PyTorch, TensorFlow, scikit-learn, model serving",
    "Software Engineer: software development, programming, backend, frontend, full stack, algorithms, system design, APIs",
    "Data Scientist: data analysis, statistical modeling, machine learning, experimentation, Python, R, SQL, predictive analytics",
    "Data Analyst: data analysis, SQL, business intelligence, dashboards, reporting, Tableau, Power BI, Excel, insights",
    "Data Engineer: ETL, data pipelines, data warehousing, Apache Spark, Airflow, dbt, cloud data platforms, BigQuery, Snowflake",
]

# Keywords used to detect entry-level / internship roles
ENTRY_LEVEL_KEYWORDS = [
    "intern", "internship", "new grad", "new graduate", "new college grad",
    "entry level", "entry-level", "early career", "junior", "associate",
    "graduate", "co-op", "coop", "recent grad",
]

SENIOR_KEYWORDS = [
    "senior", "staff", "principal", "lead ", "director", "manager",
    "vp ", "vice president", "head of", "distinguished", "fellow",
]

# Search terms sent to each career portal
SEARCH_TERMS = [
    "software engineer",
    "data scientist",
    "data analyst",
    "data engineer",
    "machine learning",
    "artificial intelligence",
]
