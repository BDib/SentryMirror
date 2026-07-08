# 🛡️ SentryMirror v0.4.1.3

**The proactive diagnostic toolkit for web mirroring, API analysis, and security hardening.**

SentryMirror is a sophisticated tool designed for developers to "twin" their own web applications. By capturing real-time API traffic, inferring database schemas, and performing automated security header audits, it serves as a critical bridge for modernizing legacy projects and hardening live environments.

---

## ✨ Features
✅ **Full offline mirror** — saves all pages, assets, CSS, JS, images  
✅ **Tech stack detection** — identifies frameworks, backend, servers, and databases  
✅ **API capture** — records all REST, XHR, Fetch, and GraphQL calls  
✅ **Schema inference** — guesses table structures, fields, and data types from responses  
✅ **Simulated SQLite database** — creates tables and inserts sample data automatically  
✅ **Mirrored API server** — replicates endpoints with correct schemas and data  
✅ **OpenAPI/Swagger spec** — generates standard API documentation  
✅ **Security Audit** — analyzes security headers for hardening
✅ **Extensible Architecture** — modular design for easy customization

---

## 📦 Getting Started

### Prerequisites
* Python 3.10+
* [Playwright](https://playwright.dev/) installed

### Installation
```bash
pip install -e .
playwright install chromium
```

### Usage (CLI)

**1. Mirror & Analyze a Site:**

```bash
sentry-mirror https://your-site.com
```

**Custom Options:**
```bash
sentry-mirror https://your-site.com \
  --output ./my_offline_site \
  --db ./my_database.db \
  --web-port 5000 \
  --api-port 5001 \
  --depth 4 \
  --delay 1.5 \
  --check-update
```

### Usage (Library)
For detailed library usage, see [API.md](API.md).

```python
import asyncio
from sentry_mirror import Crawler, DatabaseManager, ApiSimulator

async def main():
    url = "https://example.com"
    crawler = Crawler(url)
    await crawler.crawl(url)

    db_manager = DatabaseManager("local.db")
    db_manager.create_database(crawler.inferred_schemas)

    # ... use results ...

asyncio.run(main())
```

---

## 📂 Project Structure
```text
src/sentry_mirror/
├── api.py       → FastAPI simulation logic
├── audit.py     → Security header analysis
├── cli.py       → Command-line interface
├── config.py    → Pydantic configuration
├── crawler.py   → Playwright-based crawler
├── database.py  → SQLite & schema inference
├── logger.py    → Structured logging
├── models.py    → Pydantic data models
└── utils.py     → Helper functions
```

---

## ⚠️ Legal & Ethical Notice
SentryMirror is intended for authorized use only. **Do not use this tool on domains you do not own or have explicit written permission to test.**

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
