from app.scrapers.base import WorkdayAPIScraper


class IntelScraper(WorkdayAPIScraper):
    name = "Intel"
    base_url = "https://intel.wd1.myworkdayjobs.com/en-US/External"
    api_url = "https://intel.wd1.myworkdayjobs.com/wday/cxs/intel/External/jobs"
    url_prefix = "https://intel.wd1.myworkdayjobs.com"
