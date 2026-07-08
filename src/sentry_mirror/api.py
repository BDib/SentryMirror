from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any
import uvicorn
from urllib.parse import urlparse

from sentry_mirror.logger import logger
from sentry_mirror.config import settings
from sentry_mirror.database import DatabaseManager
from sentry_mirror.models import InferredSchema

class ApiSimulator:
    def __init__(self, db_manager: DatabaseManager, inferred_schemas: Dict[str, InferredSchema]):
        self.app = FastAPI(title="Simulated Mirrored API", version="1.0")
        self.db_manager = db_manager
        self.inferred_schemas = inferred_schemas
        self.setup_routes()

    def setup_routes(self):
        for url, schema in self.inferred_schemas.items():
            path = urlparse(url).path
            table = schema.possible_table

            self.add_get_route(path, table)
            self.add_post_route(path, table)

    def add_get_route(self, path: str, table: str):
        @self.app.get(path, summary=f"Get {table} records")
        async def get_endpoint():
            try:
                return await self.db_manager.get_from_db(table)
            except Exception as e:
                logger.error(f"API Error (GET {path}): {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def add_post_route(self, path: str, table: str):
        @self.app.post(path, summary=f"Create new {table} record")
        async def post_endpoint(data: Dict[str, Any]):
            try:
                success = await self.db_manager.insert_into_db(table, data)
                if success:
                    return {"status": "created"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to insert into database")
            except Exception as e:
                logger.error(f"API Error (POST {path}): {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def mount_static_files(self, directory: str):
        self.app.mount("/", StaticFiles(directory=directory, html=True), name="site")

    def run(self, port: int):
        logger.info(f"🔌 Simulated API running at: http://localhost:{port}")
        logger.info(f"📚 API docs: http://localhost:{port}/docs")
        uvicorn.run(self.app, host="0.0.0.0", port=port)
