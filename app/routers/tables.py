from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
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
    order_by: Optional[str] = "timestamp",
    order: Optional[str] = "desc",
    filter_column: Optional[str] = None,
    filter_value: Optional[str] = None,
    db: aiosqlite.Connection = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Query a specific table with pagination, ordering, and filtering."""
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
        if order_by and order_by not in columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid order_by column: {order_by}. Available columns: {columns}"
            )
        if filter_column and filter_column not in columns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid filter column: {filter_column}. Available columns: {columns}"
            )
    
    # Validate order direction
    order = order.lower()
    if order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=400,
            detail="Order must be either 'asc' or 'desc'"
        )
    
    # Build query with optional filter
    where_clause = ""
    query_params = []
    
    if filter_column and filter_value is not None:
        where_clause = f"WHERE {filter_column} = ?"
        query_params.append(filter_value)
    
    query_params.extend([limit, offset])
    
    query = f"""
        SELECT * FROM {table_name}
        {where_clause}
        {f'ORDER BY {order_by} {order.upper()}' if order_by else ''}
        LIMIT ? OFFSET ?
    """
    logger.debug(f"Executing query: {query} with params: {query_params}")
    
    async with db.execute(query, query_params) as cursor:
        rows = await cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows] 