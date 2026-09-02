# Fastcrawl Python SDK

The official Python client for [Fastcrawl](https://fastcrawl.net) — clean,
LLM-ready markdown from any URL, for your agents.

```bash
pip install fastcrawl
```

```python
from fastcrawl import Fastcrawl

fc = Fastcrawl(api_key="fc_your_key")

# Scrape → markdown
result = fc.scrape("https://example.com", only_main_content=True)
print(result["markdown"])          # clean, LLM-ready markdown
print(result["credits_remaining"]) # usage meter on every response

# Crawl a site (async) → poll
crawl = fc.crawl("https://example.com", max_pages=20)
print(crawl["crawl_id"])
print(fc.crawl_status(crawl["crawl_id"]))

# Map a site, search the web, extract structured data
fc.map("https://example.com", max_urls=100)
fc.search("best AI scraping API", limit=5)
fc.extract("https://example.com/product", schema={"type": "object", "properties": {"name": {"type": "string"}}})

# PDFs, batch, captures
fc.parse("https://example.com/report.pdf")          # PDF → markdown
fc.batch_scrape(["https://a.com", "https://b.com"])
fc.screenshot("https://example.com", output_path="page.png")
fc.pdf("https://example.com", output_path="page.pdf")

# Watch your meter
fc.usage()
```

Every error carries a machine-readable `error_code` (e.g. `scrape_timeout`,
`rate_limited`) — failed requests are never charged.

## Notes
- 1 credit = 1 successful page operation; failed requests never charge
- Free tier: 2,000 credits/month, 100/day · Go: $5/mo, 5,000 included, $1 per extra 1,000
