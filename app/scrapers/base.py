from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from playwright.async_api import Page
import httpx
import xml.etree.ElementTree as ET


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


class WorkdayAPIScraper(BaseScraper):
    """Calls the Workday CXS JSON API directly — no browser needed, bypasses Cloudflare."""
    api_url: str = ""
    url_prefix: str = ""

    _WD_LIMIT = 20
    _WD_MAX_PAGES = 10

    _HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
    }

    async def scrape(self, page) -> list[JobListing]:
        jobs = []
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for term in self.SEARCH_TERMS:
                offset = 0
                while offset < self._WD_LIMIT * self._WD_MAX_PAGES:
                    body = {
                        "appliedFacets": {},
                        "limit": self._WD_LIMIT,
                        "offset": offset,
                        "searchText": term,
                    }
                    try:
                        resp = await client.post(self.api_url, json=body, headers=self._HEADERS)
                        resp.raise_for_status()
                        data = resp.json()
                    except Exception as e:
                        print(f"[{self.name}] API error for '{term}' offset={offset}: {e}")
                        break
                    postings = data.get("jobPostings", [])
                    if not postings:
                        break
                    for p in postings:
                        title = p.get("title", "")
                        path = p.get("externalPath", "")
                        url = f"{self.url_prefix}{path}" if path else self.base_url
                        location = p.get("locationsText", "United States")
                        if title:
                            jobs.append(JobListing(title=title, url=url, location=location))
                    if len(postings) < self._WD_LIMIT:
                        break
                    offset += self._WD_LIMIT
        print(f"[{self.name}] API returned {len(jobs)} raw listings")
        return self._deduplicate(jobs)


class PhenomAPIScraper(BaseScraper):
    """Calls Phenom People's /api/jobs REST endpoint directly — no browser needed."""
    api_url: str = ""

    async def scrape(self, page) -> list[JobListing]:
        jobs = []
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for term in self.SEARCH_TERMS:
                try:
                    params = {"keywords": term, "location": "United States", "limit": 100}
                    resp = await client.get(self.api_url, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    print(f"[{self.name}] API error for '{term}': {e}")
                    continue
                listings = data.get("jobs", data.get("jobPostings", []))
                for item in listings:
                    p = item.get("data", item)  # unwrap Phenom's nested data wrapper
                    title = p.get("title", "")
                    slug = p.get("slug", "")
                    url = (
                        p.get("applyUrl")
                        or p.get("url")
                        or (f"{self.base_url}/{slug}" if slug else self.base_url)
                    )
                    location = p.get("primary_location") or p.get("location") or p.get("city", "")
                    if title:
                        jobs.append(JobListing(title=title, url=url, location=location))
        print(f"[{self.name}] API returned {len(jobs)} raw listings")
        return self._deduplicate(jobs)


class SitemapScraper(BaseScraper):
    """Fetches all jobs from an Eightfold AI sitemap — no browser, Cloudflare-proof."""
    sitemap_url: str = ""
    _SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

    async def scrape(self, page) -> list[JobListing]:
        jobs = []
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            try:
                resp = await client.get(self.sitemap_url)
                resp.raise_for_status()
                root = ET.fromstring(resp.content)
                ns = {"sm": self._SITEMAP_NS}
                all_locs = [u.findtext("sm:loc", default="", namespaces=ns) for u in root.findall("sm:url", ns)]
                for loc in all_locs:
                    if not loc or "/careers/job/" not in loc:
                        continue
                    # Strip query string, grab slug after /careers/job/
                    slug = loc.split("?")[0].split("/careers/job/", 1)[1]
                    # Remove numeric job ID prefix: e.g. "893382356411-senior-..."
                    slug = slug.lstrip("0123456789").lstrip("-")
                    # Split title from location on "-us-" boundary
                    if "-us-" in slug:
                        title_part, _, loc_part = slug.partition("-us-")
                        title = title_part.replace("-", " ")
                        location = "US " + loc_part.replace("-", " ")
                    else:
                        title = slug.replace("-", " ")
                        location = ""
                    if title:
                        jobs.append(JobListing(title=title, url=loc, location=location))

            except Exception as e:
                print(f"[{self.name}] Sitemap error: {e}")
        print(f"[{self.name}] Sitemap returned {len(jobs)} raw listings")
        return self._deduplicate(jobs)
