from app.scrapers.base import SitemapScraper


class InfineonScraper(SitemapScraper):
    name = "Infineon"
    base_url = "https://jobs.infineon.com/careers"
    sitemap_url = "https://jobs.infineon.com/careers/sitemap.xml"
