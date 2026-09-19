"""Fastcrawl — official Python SDK.

Thin client for the Fastcrawl API (https://fastcrawl.net).
One API key, all endpoints: scrape, crawl, map, search, extract,
batch scrape, PDF parse, screenshot, PDF capture, usage.

    from fastcrawl import Fastcrawl
    fc = Fastcrawl(api_key="fc_...")
    result = fc.scrape("https://example.com")
    print(result["markdown"])
"""

from __future__ import annotations

import base64
from typing import Any

import httpx

__version__ = "0.1.3"

DEFAULT_BASE_URL = "https://fastcrawl.net"
_UA = f"fastcrawl-python/{__version__}"


class FastcrawlError(Exception):
    """Raised for API-level errors; carries the machine-readable error_code."""

    def __init__(self, status: int, message: str, error_code: str | None = None):
        super().__init__(message)
        self.status = status
        self.error_code = error_code


class Fastcrawl:
    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL):
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {api_key}", "User-Agent": _UA},
            timeout=120.0,
        )

    # ── helpers ──────────────────────────────────────────────────────
    def _post(self, path: str, **json: Any) -> dict:
        try:
            r = self._client.post(f"/api/v1/{path}", json=json or None)
        except httpx.TimeoutException as e:
            raise FastcrawlError(0, f"request timed out: {e}") from e
        try:
            body = r.json()
        except ValueError:
            raise FastcrawlError(r.status_code, f"non-JSON response ({r.status_code})") from None
        if r.status_code >= 400 or not body.get("success", True):
            raise FastcrawlError(r.status_code, body.get("error") or body.get("detail") or str(body),
                                 body.get("error_code"))
        return body

    def _credits(self, resp: httpx.Response) -> int | None:
        v = resp.headers.get("X-Credits-Remaining")
        return int(v) if v else None

    # ── endpoints ────────────────────────────────────────────────────
    def scrape(self, url: str, formats: list[str] | None = None, headers: dict | None = None,
               cookies: dict | None = None, only_main_content: bool = False,
               remove_base64: bool = False, include_tags: list[str] | None = None,
               exclude_tags: list[str] | None = None, **extra: Any) -> dict:
        """Scrape a URL to clean markdown (default) and/or html."""
        payload: dict[str, Any] = {"url": url, "onlyMainContent": only_main_content,
                                   "removeBase64": remove_base64}
        if formats:
            payload["formats"] = formats
        if headers:
            payload["headers"] = headers
        if cookies:
            payload["cookies"] = cookies
        if include_tags:
            payload["includeTags"] = include_tags
        if exclude_tags:
            payload["excludeTags"] = exclude_tags
        payload.update(extra)
        resp = self._client.post("/api/v1/scrape/", json=payload)
        body = resp.json()
        if resp.status_code >= 400:
            raise FastcrawlError(resp.status_code, body.get("error") or str(body), body.get("error_code"))
        body["credits_remaining"] = self._credits(resp)
        return body

    def crawl(self, url: str, max_pages: int = 10, max_depth: int = 2,
              webhook_url: str | None = None) -> dict:
        """Start an async crawl; poll with crawl_status()."""
        payload: dict[str, Any] = {"url": url, "max_pages": max_pages, "max_depth": max_depth}
        if webhook_url:
            payload["webhook_url"] = webhook_url
        return self._post("crawl/", **payload)

    def crawl_status(self, crawl_id: str) -> dict:
        return self._client.get(f"/api/v1/crawl/{crawl_id}").json()

    def map(self, url: str, max_urls: int = 50) -> dict:
        return self._post("map/", url=url, max_urls=max_urls)

    def search(self, query: str, limit: int = 5) -> dict:
        return self._post("search/", query=query, limit=limit)

    def extract(self, url: str, schema: dict, prompt: str | None = None) -> dict:
        payload: dict[str, Any] = {"url": url, "schema": schema}
        if prompt:
            payload["prompt"] = prompt
        return self._post("extract/", **payload)

    def extract_many(self, urls: list[str], schema: dict, prompt: str | None = None) -> dict:
        payload: dict[str, Any] = {"urls": urls, "schema": schema}
        if prompt:
            payload["prompt"] = prompt
        return self._post("extract/", **payload)

    def batch_scrape(self, urls: list[str], formats: list[str] | None = None) -> dict:
        payload: dict[str, Any] = {"urls": urls}
        if formats:
            payload["formats"] = formats
        return self._post("batch/scrape/", **payload)

    def parse(self, url: str, pages: int | None = None) -> dict:
        """PDF → clean markdown (pdf-inspector engine)."""
        payload: dict[str, Any] = {"url": url}
        if pages:
            payload["pages"] = pages
        return self._post("parse/", **payload)

    def screenshot(self, url: str, output_path: str | None = None) -> bytes:
        """Return PNG bytes; optionally write to output_path."""
        r = self._client.post("/api/v1/screenshot/", json={"url": url})
        if r.status_code >= 400:
            raise FastcrawlError(r.status_code, r.text[:200])
        png = base64.b64decode(r.json()["data"]) if r.json().get("data") else r.content
        if output_path:
            with open(output_path, "wb") as f:
                f.write(png)
        return png

    def pdf(self, url: str, output_path: str | None = None) -> bytes:
        """Page → PDF bytes; optionally write to output_path."""
        r = self._client.post("/api/v1/pdf/", json={"url": url})
        if r.status_code >= 400:
            raise FastcrawlError(r.status_code, r.text[:200])
        data = base64.b64decode(r.json()["data"]) if r.json().get("data") else r.content
        if output_path:
            with open(output_path, "wb") as f:
                f.write(data)
        return data

    def usage(self) -> dict:
        r = self._client.get("/api/v1/usage/")
        return r.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "Fastcrawl":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
