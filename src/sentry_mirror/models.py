from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class ApiCall(BaseModel):
    url: str
    method: str
    status: int
    type: str
    content_type: str
    is_external: bool
    is_graphql: bool

class FieldInfo(BaseModel):
    type: str
    sql_type: str
    example: Optional[str] = None

class InferredSchema(BaseModel):
    possible_table: str
    fields: Dict[str, FieldInfo]
    json_schema: Dict[str, Any]
    notes: List[str]

class TechInfo(BaseModel):
    versions: List[str]
    categories: List[str]

class FullAnalysisReport(BaseModel):
    base_url: str
    domain: str
    crawl_time: datetime = Field(default_factory=datetime.utcnow)
    total_pages: int
    technologies: Dict[str, Any]
    api_calls: List[ApiCall]
    inferred_database_structures: Dict[str, InferredSchema]
    openapi_spec: Dict[str, Any]
