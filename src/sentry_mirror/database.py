import os
import re
import sqlite3
import aiosqlite
import json
from typing import Dict, Any, Optional, List
from sentry_mirror.logger import logger
from sentry_mirror.models import InferredSchema, FieldInfo

def get_json_type(value: Any) -> Dict[str, str]:
    if value is None:
        return {"type": "null", "sql": "TEXT"}
    elif isinstance(value, bool):
        return {"type": "boolean", "sql": "INTEGER"}
    elif isinstance(value, int):
        return {"type": "integer", "sql": "INTEGER"}
    elif isinstance(value, float):
        return {"type": "number", "sql": "REAL"}
    elif isinstance(value, str):
        return {"type": "string", "sql": "TEXT"}
    elif isinstance(value, list):
        if value:
            item_type = get_json_type(value[0])
            return {"type": "array", "items": item_type, "sql": "TEXT"}
        return {"type": "array", "items": {}, "sql": "TEXT"}
    elif isinstance(value, dict):
        return {"type": "object", "sql": "TEXT"}
    return {"type": "string", "sql": "TEXT"}

def infer_schema_from_json(data: Any, endpoint_path: str) -> InferredSchema:
    table_name = endpoint_path.strip("/").split("/")[-1].replace("-", "_").replace("/", "_") or "unknown_table"
    fields = {}
    notes = []

    if isinstance(data, dict):
        for key, value in data.items():
            field_info_dict = get_json_type(value)
            fields[key] = FieldInfo(
                type=type(value).__name__,
                sql_type=field_info_dict["sql"],
                example=str(value)[:100] if value is not None else None
            )
            if isinstance(value, (dict, list)):
                notes.append(f"'{key}' → nested/related data")
        json_schema = {"type": "object", "properties": {k: get_json_type(v) for k, v in data.items()}}
    elif isinstance(data, list) and data and isinstance(data[0], dict):
        notes.append("List of records")
        inner_schema = infer_schema_from_json(data[0], endpoint_path)
        fields = inner_schema.fields
        json_schema = {"type": "array", "items": inner_schema.json_schema}
    else:
        json_schema = get_json_type(data)

    return InferredSchema(
        possible_table=table_name,
        fields=fields,
        json_schema=json_schema,
        notes=notes
    )

class DatabaseManager:
    def __init__(self, db_file: str):
        self.db_file = db_file

    def create_database(self, inferred_schemas: Dict[str, InferredSchema]):
        logger.info(f"🗄️ Creating simulated SQLite database: {self.db_file}")
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")

            for url, schema in inferred_schemas.items():
                table_name = schema.possible_table
                if not schema.fields:
                    continue
                columns = []
                for col_name, col_info in schema.fields.items():
                    safe_name = re.sub(r'\W+', '_', col_name)
                    columns.append(f"{safe_name} {col_info.sql_type}")

                if not columns:
                    continue

                create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, {', '.join(columns)});"
                try:
                    cursor.execute(create_sql)
                    # Insert example data
                    example_data = {re.sub(r'\W+', '_', k): v.example for k, v in schema.fields.items() if v.example is not None}
                    if example_data:
                        cols = ", ".join(example_data.keys())
                        vals = ", ".join(["?" for _ in example_data.values()])
                        cursor.execute(f"INSERT OR IGNORE INTO {table_name} ({cols}) VALUES ({vals});", list(example_data.values()))
                except Exception as e:
                    logger.error(f"⚠️ Could not create table {table_name}: {e}")

            conn.commit()
            conn.close()
            logger.info("✅ SQLite database created successfully")
        except Exception as e:
            logger.error(f"❌ Database creation failed: {e}")

    async def get_from_db(self, table: str) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_file) as db:
            db.row_factory = aiosqlite.Row
            try:
                cursor = await db.execute(f"SELECT * FROM {table} LIMIT 20;")
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"Error reading from table {table}: {e}")
                return []

    async def insert_into_db(self, table: str, data: Dict[str, Any]):
        async with aiosqlite.connect(self.db_file) as db:
            cols = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data.values()])
            try:
                await db.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders});", list(data.values()))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Error inserting into table {table}: {e}")
                return False
