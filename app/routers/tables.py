from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import aiosqlite
import logging
from ..internal.db import get_db
from ..internal.auth import verify_api_key

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

router = APIRouter(
    prefix="/tables",
    tags=["tables"],
    dependencies=[Depends(verify_api_key)]
)

@router.get("/")
async def list_tables(db: aiosqlite.Connection = Depends(get_db)) -> List[str]:
    """List all available tables in the database."""
    async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
        tables = await cursor.fetchall()
        return [table[0] for table in tables]

@router.get("/{table_name}")
async def query_table(
    table_name: str,
    limit: int = 100,
    offset: int = 0,
    db: aiosqlite.Connection = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Query a specific table with pagination."""
    # Validate table exists
    async with db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
        (table_name,)
    ) as cursor:
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Table {table_name} not found")
    
    # Get column names
    async with db.execute(f"PRAGMA table_info({table_name})") as cursor:
        columns = [col[1] for col in await cursor.fetchall()]
    
    # Query data
    async with db.execute(
        f"SELECT * FROM {table_name} LIMIT ? OFFSET ?",
        (limit, offset)
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows] 