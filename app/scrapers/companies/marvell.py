from app.scrapers.base import WorkdayAPIScraper


class MarvellScraper(WorkdayAPIScraper):
    name = "Marvell"
    base_url = "https://marvell.wd1.myworkdayjobs.com/en-US/MarvellCareers"
    api_url = "https://marvell.wd1.myworkdayjobs.com/wday/cxs/marvell/MarvellCareers/jobs"
    url_prefix = "https://marvell.wd1.myworkdayjobs.com"
