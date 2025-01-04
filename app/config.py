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
            # Keep the full path structure after /data/db
            if path.startswith(self.DB_MOUNT_PATH):
                container_path = path
            else:
                # For paths that don't start with mount path
                relative_path = path.split(self.DB_MOUNT_PATH)[-1].lstrip('/')
                container_path = os.path.join(self.DB_MOUNT_PATH, relative_path)
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
