from app.scrapers.base import SitemapScraper


class NVIDIAScraper(SitemapScraper):
    name = "NVIDIA"
    base_url = "https://jobs.nvidia.com/careers"
    sitemap_url = "https://jobs.nvidia.com/careers/sitemap.xml"
