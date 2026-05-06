from app.scrapers.base import WorkdayAPIScraper


class SamsungScraper(WorkdayAPIScraper):
    name = "Samsung"
    base_url = "https://sec.wd3.myworkdayjobs.com/en-US/Samsung_Careers"
    api_url = "https://sec.wd3.myworkdayjobs.com/wday/cxs/sec/Samsung_Careers/jobs"
    url_prefix = "https://sec.wd3.myworkdayjobs.com"
