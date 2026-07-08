# SentryMirror API Documentation

SentryMirror can be used as a Python library to programmatically mirror sites and analyze APIs.

## 📦 Installation

```bash
pip install -e .
```

## 🚀 Quick Start

```python
import asyncio
from sentry_mirror import Crawler, DatabaseManager, settings

async def main():
    url = "https://example.com"

    # 1. Initialize and run the crawler
    crawler = Crawler(url)
    await crawler.crawl(url)

    # 2. Access discovered data
    print(f"Discovered {len(crawler.api_calls)} API calls")

    # 3. Create simulated database
    db_manager = DatabaseManager("my_database.db")
    db_manager.create_database(crawler.inferred_schemas)

asyncio.run(main())
```

## 📚 Core Classes

### `Crawler(base_url: str)`
The main class for crawling websites and intercepting API traffic.

- **`async crawl(url: str, depth: int = 0)`**: Starts the crawl from the given URL.
- **`detect_tech_stack() -> dict`**: Uses Wappalyzer to identify the site's technology stack.
- **`api_calls: List[ApiCall]`**: A list of intercepted API calls.
- **`inferred_schemas: Dict[str, InferredSchema]`**: A dictionary mapping URLs to inferred database schemas.

### `DatabaseManager(db_file: str)`
Handles the creation and management of the simulated SQLite database.

- **`create_database(inferred_schemas: Dict[str, InferredSchema])`**: Generates tables and inserts sample data based on inferred schemas.
- **`async get_from_db(table: str) -> List[dict]`**: Retrieves records from a simulated table.
- **`async insert_into_db(table: str, data: dict)`**: Inserts a new record into a simulated table.

### `ApiSimulator(db_manager: DatabaseManager, inferred_schemas: Dict[str, InferredSchema])`
Runs a FastAPI server to simulate the discovered API.

- **`mount_static_files(directory: str)`**: Serves the mirrored static site.
- **`run(port: int)`**: Starts the FastAPI server.

### `audit_security_headers(url: str) -> dict`
Performs a security header audit on the given URL.

## ⚙️ Configuration

You can customize SentryMirror behavior using the `settings` object:

```python
from sentry_mirror import settings

settings.max_depth = 3
settings.delay_between_requests = 2.0
settings.output_dir = "./custom_output"
```

Refer to `src/sentry_mirror/config.py` for a full list of available settings.
