from app.scrapers.base import WorkdayAPIScraper


class MicronScraper(WorkdayAPIScraper):
    name = "Micron"
    base_url = "https://micron.wd1.myworkdayjobs.com/en-US/External"
    api_url = "https://micron.wd1.myworkdayjobs.com/wday/cxs/micron/External/jobs"
    url_prefix = "https://micron.wd1.myworkdayjobs.com"
