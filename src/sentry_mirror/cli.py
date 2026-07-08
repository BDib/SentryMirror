import argparse
import asyncio
import json
import os
from datetime import datetime

from sentry_mirror.logger import logger
from sentry_mirror.config import settings
from sentry_mirror.crawler import Crawler
from sentry_mirror.database import DatabaseManager
from sentry_mirror.api import ApiSimulator
from sentry_mirror.audit import run_security_audit
from sentry_mirror.models import FullAnalysisReport
from sentry_mirror.__about__ import __version__
from sentry_mirror.utils import check_for_updates
from sentry_mirror.web_ui import app as ui_app

async def main_async(args):
    # Override settings with CLI arguments
    if args.output: settings.output_dir = args.output
    if args.db: settings.db_file = args.db
    if args.web_port: settings.web_port = args.web_port
    if args.api_port: settings.api_port = args.api_port
    if args.depth is not None: settings.max_depth = args.depth
    if args.delay is not None: settings.delay_between_requests = args.delay

    os.makedirs(settings.output_dir, exist_ok=True)

    logger.info(f"🚀 Starting full crawl for: {args.url}")
    crawler = Crawler(args.url)
    await crawler.crawl(args.url)

    db_manager = DatabaseManager(settings.db_file)
    if settings.infer_db_structure:
        db_manager.create_database(crawler.inferred_schemas)

    techs = crawler.detect_tech_stack()

    # Generate reports
    report = FullAnalysisReport(
        base_url=args.url,
        domain=crawler.base_domain,
        total_pages=len(crawler.visited),
        technologies=techs,
        api_calls=crawler.api_calls,
        inferred_database_structures=crawler.inferred_schemas,
        openapi_spec={
            "openapi": "3.0.3",
            "info": {"title": f"API Spec for {crawler.base_domain}", "version": "1.0.0"},
            "servers": [{"url": f"http://localhost:{settings.api_port}"}],
            "paths": crawler.openapi_paths
        }
    )

    report_path = os.path.join(settings.output_dir, "full_analysis_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))

    # Security audit
    audit_path = os.path.join(settings.output_dir, "security_report.txt")
    run_security_audit(args.url, audit_path)

    # Launch servers if requested
    if settings.simulate_api or settings.serve_local_site:
        simulator = ApiSimulator(db_manager, crawler.inferred_schemas)
        simulator.app.mount("/dashboard", ui_app)
        if settings.serve_local_site:
            simulator.mount_static_files(settings.output_dir)

        # If both are running on the same server, we must ensure the port matches the rewrite logic
        # Our rewrite logic in crawler.py uses settings.api_port
        port = settings.api_port if settings.simulate_api else settings.web_port
        simulator.run(port)

def main():
    parser = argparse.ArgumentParser(
        description="SentryMirror: Advanced Web Mirror & API Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sentry-mirror https://example.com
  sentry-mirror https://example.com --output ./mirror --web-port 9000
  sentry-mirror https://example.com --depth 2 --delay 0.5
        """
    )
    parser.add_argument("url", nargs="?", help="URL to crawl (e.g. https://example.com)")
    parser.add_argument("--output", help="Folder to save the mirrored site and reports (default: ./full_analysis_mirror)")
    parser.add_argument("--db", help="SQLite database file")
    parser.add_argument("--web-port", type=int, help="Port for local site")
    parser.add_argument("--api-port", type=int, help="Port for simulated API")
    parser.add_argument("--depth", type=int, help="Max crawl depth")
    parser.add_argument("--delay", type=float, help="Seconds between requests to avoid blocking (default: 1.0)")
    parser.add_argument("--check-update", action="store_true", help="Check for tool updates")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")

    args = parser.parse_args()

    if args.check_update:
        check_for_updates()
        if not args.url:
            return

    if not args.url:
        parser.print_help()
        return

    if not args.url.startswith(("http://", "https://")):
        logger.error("❌ Invalid URL — use http:// or https://")
        return

    asyncio.run(main_async(args))

if __name__ == "__main__":
    main()
