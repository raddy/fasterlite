import logging
from fastapi import Depends
import aiosqlite
from ..config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

async def get_db(db_name: str):
    db_path = settings.databases[db_name]
    logger.info(f"Database name: {db_name}")
    logger.info(f"Database path: {db_path}")
    logger.info(f"All available databases: {settings.databases}")
    
    try:
        db = await aiosqlite.connect(db_path)
        async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
            tables = await cursor.fetchall()
            logger.info(f"Found tables: {tables}")
        try:
            yield db
        finally:
            await db.close()
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise