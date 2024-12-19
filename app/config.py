from typing import Dict
from pathlib import Path
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Format: "name1:file1.db,name2:file2.db"
    SQLITE_DBS: str
    DB_MOUNT_PATH: str = "/data/db"
    API_KEY: str

    @property
    def databases(self) -> Dict[str, str]:
        dbs = {}
        for db_config in self.SQLITE_DBS.split(','):
            name, path = db_config.split(':')
            # Replace the original path with the mounted path
            filename = os.path.basename(path)
            container_path = os.path.join(self.DB_MOUNT_PATH, filename)
            dbs[name] = container_path
        return dbs

    class Config:
        env_file = ".env"

settings = Settings()

# Validate database configuration
def validate_databases() -> None:
    for name, path in settings.databases.items():
        if not path.exists():
            raise FileNotFoundError(f"Database '{name}' not found at {path}") 