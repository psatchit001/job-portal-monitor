from app.scrapers.base import WorkdayAPIScraper


class MicrochipScraper(WorkdayAPIScraper):
    name = "Microchip Technology"
    base_url = "https://wd5.myworkdaysite.com/en-US/recruiting/microchiphr/External"
    api_url = "https://wd5.myworkdaysite.com/wday/cxs/microchiphr/External/jobs"
    url_prefix = "https://wd5.myworkdaysite.com"
