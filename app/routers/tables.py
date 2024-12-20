from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
import aiosqlite
import json
import logging
from ..internal.db import get_db
from ..internal.auth import verify_api_key

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

router = APIRouter(
    dependencies=[Depends(verify_api_key)]
)

async def get_db_dependency(db_name: str):
    async for db in get_db(db_name):
        print(f"TABLES MODULE - Got DB connection")
        yield db

@router.get("/{db_name}")
async def list_tables(
    db_name: str, 
    db: aiosqlite.Connection = Depends(get_db_dependency)
) -> List[str]:
    """List all available tables in the database."""
    try:
        async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
            tables = await cursor.fetchall()
            if not tables:
                raise HTTPException(
                    status_code=404,
                    detail=f"No tables found in database '{db_name}'"
                )
            print(f"TABLES MODULE - Found tables: {tables[0]}")
            return [table[0] for table in tables]
    except aiosqlite.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

@router.get("/{db_name}/{table_name}")
async def query_table(
    db_name: str,
    table_name: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    order_by: Optional[str] = "timestamp",
    order: Optional[str] = Query("desc", regex="^(asc|desc)$"),
    filters: Optional[str] = None,  # JSON string of column:value pairs
    db: aiosqlite.Connection = Depends(get_db_dependency)
) -> List[Dict[str, Any]]:
    """Query a specific table with pagination, ordering, and filtering."""
    # Parse filters
    filter_dict = {}
    if filters:
        try:
            filter_dict = json.loads(filters)
            if not isinstance(filter_dict, dict):
                raise ValueError("Filters must be a dictionary")
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid filters JSON format"
            )
    
    # Get column names and validate
    async with db.execute(f"PRAGMA table_info({table_name})") as cursor:
        columns = [col[1] for col in await cursor.fetchall()]
        if order_by and order_by not in columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid order_by column: {order_by}. Available columns: {columns}"
            )
        
        # Validate filter columns
        invalid_columns = [col for col in filter_dict.keys() if col not in columns]
        if invalid_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid filter columns: {invalid_columns}. Available columns: {columns}"
            )
    
    # Build query
    where_clauses = []
    query_params = []
    
    for col, val in filter_dict.items():
        where_clauses.append(f"{col} = ?")
        query_params.append(val)
    
    where_clause = " AND ".join(where_clauses) if where_clauses else ""
    if where_clause:
        where_clause = f"WHERE {where_clause}"
    
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
