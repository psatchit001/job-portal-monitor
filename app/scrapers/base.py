from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from playwright.async_api import Page


@dataclass
class JobListing:
    title: str
    url: str
    location: str = ""
    department: str = ""
    description: str = ""


class BaseScraper(ABC):
    """All company scrapers inherit from this. Implement scrape() only."""

    name: str = ""
    base_url: str = ""

    # Search terms sent to the portal's search box
    SEARCH_TERMS: list[str] = [
        "software engineer",
        "data scientist",
        "data analyst",
        "data engineer",
        "machine learning",
        "artificial intelligence",
    ]

    async def scrape(self, page: Page) -> list[JobListing]:
        raise NotImplementedError

    async def _safe_text(self, element) -> str:
        try:
            return (await element.text_content() or "").strip()
        except Exception:
            return ""

    async def _safe_attr(self, element, attr: str) -> str:
        try:
            return (await element.get_attribute(attr) or "").strip()
        except Exception:
            return ""

    def _deduplicate(self, jobs: list[JobListing]) -> list[JobListing]:
        seen = set()
        out = []
        for j in jobs:
            if j.url not in seen:
                seen.add(j.url)
                out.append(j)
        return out
