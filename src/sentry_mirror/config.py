from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Dict, Optional

class Settings(BaseSettings):
    output_dir: str = Field("./full_analysis_mirror", env="OUTPUT_DIR")
    db_file: str = Field("./simulated_database.db", env="DB_FILE")
    api_port: int = Field(8081, env="API_PORT")
    web_port: int = Field(8080, env="WEB_PORT")
    max_depth: int = Field(5, env="MAX_DEPTH")
    delay_between_requests: float = Field(1.0, env="DELAY_BETWEEN_REQUESTS")
    respect_robots_txt: bool = True
    save_api_responses: bool = True
    rewrite_api_calls: bool = True
    infer_db_structure: bool = True
    generate_openapi: bool = True
    simulate_sqlite: bool = True
    simulate_api: bool = True
    serve_local_site: bool = True
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

    class Config:
        env_file = ".env"

settings = Settings()
