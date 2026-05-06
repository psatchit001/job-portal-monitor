from app.scrapers.base import WorkdayAPIScraper


class AnalogDevicesScraper(WorkdayAPIScraper):
    name = "Analog Devices"
    base_url = "https://analogdevices.wd1.myworkdayjobs.com/en-US/External"
    api_url = "https://analogdevices.wd1.myworkdayjobs.com/wday/cxs/analogdevices/External/jobs"
    url_prefix = "https://analogdevices.wd1.myworkdayjobs.com"
