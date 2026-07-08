import os
import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import jsbeautifier
from wappalyzer import Wappalyzer, WebPage
from typing import Set, List, Dict, Any, Optional
import json

from sentry_mirror.logger import logger
from sentry_mirror.config import settings
from sentry_mirror.models import ApiCall, InferredSchema
from sentry_mirror.database import infer_schema_from_json

class Crawler:
    def __init__(self, base_url: str):
        self.base_url = base_url
        parsed = urlparse(base_url)
        self.base_domain = parsed.netloc
        self.base_scheme = parsed.scheme
        self.visited: Set[str] = set()
        self.api_calls: List[ApiCall] = []
        self.inferred_schemas: Dict[str, InferredSchema] = {}
        self.openapi_paths: Dict[str, Any] = {}
        self.output_dir = settings.output_dir

    def get_local_path(self, url: str):
        parsed = urlparse(url)
        path = parsed.path.lstrip("/") or "index.html"
        if parsed.query:
            path += f"__{quote(parsed.query, safe='')}"
        return os.path.join(self.output_dir, path), path

    async def save_content(self, url: str, content: Any, is_binary: bool = False):
        local_path, _ = self.get_local_path(url)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        try:
            mode = "wb" if is_binary else "w"
            enc = None if is_binary else "utf-8"
            if is_binary:
                with open(local_path, mode) as f:
                    f.write(content)
            else:
                with open(local_path, mode, encoding=enc, errors="replace") as f:
                    f.write(content)
            return True
        except Exception as e:
            logger.error(f"Failed to save content for {url}: {e}")
            return False

    def rewrite_html_and_scripts(self, soup: BeautifulSoup, current_url: str):
        tags_attrs = {"a": "href", "link": "href", "script": "src", "img": "src", "iframe": "src", "form": "action"}
        for tag, attr in tags_attrs.items():
            for el in soup.find_all(tag):
                val = el.get(attr)
                if val:
                    abs_url = urljoin(current_url, val)
                    if urlparse(abs_url).netloc == self.base_domain:
                        _, rel = self.get_local_path(abs_url)
                        el[attr] = rel

        if settings.rewrite_api_calls:
            js_code = f"""
            const origFetch = window.fetch;
            const origOpen = XMLHttpRequest.prototype.open;
            window.fetch = async function(i, init) {{
                let u = typeof i === 'string' ? i : i.url;
                if(u.startsWith('/') || u.includes('{self.base_domain}')) {{
                    u = u.replace(/^https?:\\/\\/[^/]+/, 'http://localhost:{settings.api_port}');
                }}
                return origFetch(u, init);
            }};
            XMLHttpRequest.prototype.open = function(m, u, ...a) {{
                if(u.startsWith('/') || u.includes('{self.base_domain}')) {{
                    u = u.replace(/^https?:\\/\\/[^/]+/, 'http://localhost:{settings.api_port}');
                }}
                return origOpen.call(this, m, u, ...a);
            }};
            """
            script = soup.new_tag("script", type="text/javascript")
            script.string = jsbeautifier.beautify(js_code)
            if soup.head:
                soup.head.append(script)
            elif soup.body:
                soup.body.append(script)
        return soup

    async def intercept_and_process_request(self, page):
        async def handle_request(req):
            if req.resource_type in ["xhr", "fetch"] and req.method in ["GET", "POST"]:
                try:
                    resp = await req.response()
                    if not resp: return
                    status = resp.status
                    ctype = resp.headers.get("content-type", "").split(";")[0]
                    body = await resp.body()
                    text = body.decode("utf-8", errors="replace")
                    parsed = urlparse(req.url)
                    path = parsed.path

                    call = ApiCall(
                        url=req.url, method=req.method, status=status,
                        type=req.resource_type, content_type=ctype,
                        is_external=parsed.netloc != self.base_domain,
                        is_graphql="graphql" in req.url.lower() or "graphql" in ctype
                    )
                    self.api_calls.append(call)

                    if not call.is_external:
                        await self.save_content(req.url + (".json" if "json" in ctype else ".txt"), text)
                        schema = None
                        if settings.infer_db_structure and "json" in ctype:
                            try:
                                schema = infer_schema_from_json(json.loads(text), path)
                                self.inferred_schemas[req.url] = schema
                            except Exception as e:
                                logger.debug(f"Schema inference failed for {req.url}: {e}")

                        if settings.generate_openapi and status in (200, 201):
                            self.add_to_openapi(req.method, path, status, ctype, schema)
                except Exception as e:
                    logger.debug(f"Request interception failed: {e}")

        page.on("requestfinished", lambda r: asyncio.create_task(handle_request(r)))

    def add_to_openapi(self, method: str, path: str, status: int, content_type: str, schema: Optional[InferredSchema]):
        if path not in self.openapi_paths:
            self.openapi_paths[path] = {}
        method = method.lower()
        if method not in self.openapi_paths[path]:
            self.openapi_paths[path][method] = {
                "summary": f"{method.upper()} {path}",
                "responses": {
                    str(status): {
                        "description": "Successful response",
                        "content": {content_type: {"schema": schema.json_schema if schema else {}}}
                    }
                }
            }

    async def crawl(self, url: str, depth: int = 0):
        if url in self.visited or depth > settings.max_depth:
            return
        self.visited.add(url)
        logger.info(f"🔍 Crawling [{depth}]: {url}")
        await asyncio.sleep(settings.delay_between_requests)

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(user_agent=settings.user_agent)
                await self.intercept_and_process_request(page)
                await page.goto(url, wait_until="networkidle", timeout=45000)
                html = await page.content()
                await browser.close()

            soup = self.rewrite_html_and_scripts(BeautifulSoup(html, "lxml"), url)
            await self.save_content(url, str(soup))

            # Download assets
            assets = []
            for t, a in [("img", "src"), ("script", "src"), ("link", "href")]:
                for el in soup.find_all(t):
                    if el.get(a):
                        abs_u = urljoin(url, el[a])
                        if abs_u not in self.visited and urlparse(abs_u).netloc == self.base_domain:
                            assets.append(abs_u)

            async with aiohttp.ClientSession(headers={"User-Agent": settings.user_agent}) as s:
                await asyncio.gather(*[self.save_asset(s, u) for u in assets], return_exceptions=True)

            # Crawl links
            next_links = [urljoin(url, a["href"]) for a in soup.find_all("a", href=True)
                          if urlparse(urljoin(url, a["href"])).netloc == self.base_domain]
            await asyncio.gather(*[self.crawl(u, depth + 1) for u in next_links if u not in self.visited], return_exceptions=True)

        except Exception as e:
            logger.error(f"❌ Failed to crawl {url}: {e}")

    async def save_asset(self, session, url):
        try:
            async with session.get(url) as r:
                if r.status == 200:
                    await self.save_content(url, await r.read(), is_binary=True)
        except Exception as e:
            logger.debug(f"Failed to save asset {url}: {e}")

    def detect_tech_stack(self):
        try:
            wappalyzer = Wappalyzer.latest()
            webpage = WebPage.new_from_url(self.base_url, headers={"User-Agent": settings.user_agent}, timeout=15)
            return wappalyzer.analyze_with_versions_and_categories(webpage)
        except Exception as e:
            logger.warning(f"⚠️ Tech detection failed: {e}")
            return {}
