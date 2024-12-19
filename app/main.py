from fastapi import FastAPI
from .routers import tables
from .config import settings
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting up with databases config: {settings.databases}")
    logger.info(f"DB mount path: {settings.DB_MOUNT_PATH}")
    logger.info(f"SQLITE_DBS: {settings.SQLITE_DBS}")

app.include_router(tables.router)

@app.get("/")
async def root():
    return {"message": "SQLite REST API Service"}
