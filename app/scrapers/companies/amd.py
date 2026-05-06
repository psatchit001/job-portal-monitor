from app.scrapers.base import PhenomAPIScraper


class AMDScraper(PhenomAPIScraper):
    name = "AMD"
    base_url = "https://careers.amd.com/careers-home/jobs"
    api_url = "https://careers.amd.com/api/jobs"
