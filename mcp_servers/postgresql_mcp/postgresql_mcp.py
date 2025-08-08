"""PostgreSQL MCP Server for SuperMon platform."""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncpg
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class PostgreSQLQuery(BaseModel):
    """PostgreSQL query model."""
    sql: str = Field(..., description="SQL query")
    params: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    timeout: Optional[int] = Field(30, description="Query timeout in seconds")


class PostgreSQLTable(BaseModel):
    """PostgreSQL table model."""
    name: str = Field(..., description="Table name")
    schema: str = Field(default="public", description="Schema name")
    columns: Optional[List[Dict[str, Any]]] = Field(None, description="Table columns")
    indexes: Optional[List[Dict[str, Any]]] = Field(None, description="Table indexes")


class PostgreSQLDatabase(BaseModel):
    """PostgreSQL database model."""
    name: str = Field(..., description="Database name")
    owner: Optional[str] = Field(None, description="Database owner")
    encoding: Optional[str] = Field(None, description="Database encoding")
    collation: Optional[str] = Field(None, description="Database collation")


class PostgreSQLMCPResponse(BaseModel):
    """Standard MCP response model."""
    success: bool = Field(..., description="Operation success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class PostgreSQLMCPServer:
    """PostgreSQL MCP Server implementation."""
    
    def __init__(self):
        """Initialize PostgreSQL MCP Server."""
        self.app = FastAPI(title="PostgreSQL MCP Server", version="1.0.0")
        self.pool: Optional[asyncpg.Pool] = None
        self.engine: Optional[AsyncSession] = None
        self.connection_string: Optional[str] = None
        self.databases_cache: Dict[str, Dict[str, Any]] = {}
        self.tables_cache: Dict[str, List[Dict[str, Any]]] = {}
        
        self._setup_routes()
        self._setup_middleware()
    
    def _setup_middleware(self):
        """Setup CORS middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.on_event("startup")
        async def startup_event():
            """Initialize PostgreSQL client on startup."""
            await self._initialize_client()
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Cleanup on shutdown."""
            await self._cleanup()
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": "PostgreSQL MCP Server",
                "connected": self.pool is not None,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.post("/execute-query")
        async def execute_query(query: PostgreSQLQuery):
            """Execute a PostgreSQL query."""
            try:
                result = await self._execute_query(query)
                return PostgreSQLMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error executing query: {e}")
                return PostgreSQLMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/databases")
        async def get_databases():
            """Get all databases."""
            try:
                result = await self._get_databases()
                return PostgreSQLMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting databases: {e}")
                return PostgreSQLMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/tables/{database_name}")
        async def get_tables(database_name: str, schema: str = "public"):
            """Get tables from a database."""
            try:
                result = await self._get_tables(database_name, schema)
                return PostgreSQLMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting tables: {e}")
                return PostgreSQLMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/create-table/{database_name}")
        async def create_table(database_name: str, table: PostgreSQLTable):
            """Create a new table."""
            try:
                result = await self._create_table(database_name, table)
                return PostgreSQLMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error creating table: {e}")
                return PostgreSQLMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/create-database")
        async def create_database(database: PostgreSQLDatabase):
            """Create a new database."""
            try:
                result = await self._create_database(database)
                return PostgreSQLMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error creating database: {e}")
                return PostgreSQLMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/table-info/{database_name}/{table_name}")
        async def get_table_info(database_name: str, table_name: str, schema: str = "public"):
            """Get detailed table information."""
            try:
                result = await self._get_table_info(database_name, table_name, schema)
                return PostgreSQLMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting table info: {e}")
                return PostgreSQLMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/backup-database/{database_name}")
        async def backup_database(database_name: str, backup_path: str):
            """Create a database backup."""
            try:
                result = await self._backup_database(database_name, backup_path)
                return PostgreSQLMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error backing up database: {e}")
                return PostgreSQLMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/restore-database/{database_name}")
        async def restore_database(database_name: str, backup_path: str):
            """Restore a database from backup."""
            try:
                result = await self._restore_database(database_name, backup_path)
                return PostgreSQLMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error restoring database: {e}")
                return PostgreSQLMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/performance-stats")
        async def get_performance_stats():
            """Get database performance statistics."""
            try:
                result = await self._get_performance_stats()
                return PostgreSQLMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting performance stats: {e}")
                return PostgreSQLMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
    
    async def _initialize_client(self):
        """Initialize PostgreSQL client."""
        self.connection_string = os.getenv("DATABASE_URL")
        
        if not self.connection_string:
            logger.warning("DATABASE_URL not found in environment")
            return
        
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=5,
                max_size=20
            )
            
            # Test connection
            async with self.pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                logger.info(f"Connected to PostgreSQL: {version.split(',')[0]}")
            
            # Load initial data
            await self._load_databases()
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL client: {e}")
            self.pool = None
    
    async def _cleanup(self):
        """Cleanup resources."""
        if self.pool:
            await self.pool.close()
    
    async def _execute_query(self, query: PostgreSQLQuery) -> Dict[str, Any]:
        """Execute a PostgreSQL query."""
        if not self.pool:
            raise Exception("PostgreSQL client not initialized")
        
        try:
            async with self.pool.acquire() as conn:
                if query.params:
                    result = await conn.fetch(query.sql, *query.params.values())
                else:
                    result = await conn.fetch(query.sql)
                
                # Convert result to serializable format
                rows = []
                for row in result:
                    row_dict = {}
                    for key, value in row.items():
                        if isinstance(value, datetime):
                            row_dict[key] = value.isoformat()
                        else:
                            row_dict[key] = value
                    rows.append(row_dict)
                
                return {
                    "rows": rows,
                    "row_count": len(rows),
                    "columns": list(result[0].keys()) if result else []
                }
        
        except Exception as e:
            logger.error(f"Error executing PostgreSQL query: {e}")
            raise
    
    async def _get_databases(self) -> Dict[str, Any]:
        """Get all databases."""
        if not self.pool:
            raise Exception("PostgreSQL client not initialized")
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetch("""
                    SELECT 
                        datname as name,
                        pg_get_userbyid(datdba) as owner,
                        pg_encoding_to_char(encoding) as encoding,
                        datcollate as collation
                    FROM pg_database 
                    WHERE datistemplate = false
                    ORDER BY datname
                """)
                
                databases = []
                for row in result:
                    db_data = {
                        "name": row["name"],
                        "owner": row["owner"],
                        "encoding": row["encoding"],
                        "collation": row["collation"]
                    }
                    databases.append(db_data)
                    self.databases_cache[row["name"]] = db_data
                
                return {"databases": databases}
        
        except Exception as e:
            logger.error(f"Error getting PostgreSQL databases: {e}")
            raise
    
    async def _get_tables(self, database_name: str, schema: str = "public") -> Dict[str, Any]:
        """Get tables from a database."""
        if not self.pool:
            raise Exception("PostgreSQL client not initialized")
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetch("""
                    SELECT 
                        table_name,
                        table_type,
                        pg_size_pretty(pg_total_relation_size(quote_ident(table_schema)||'.'||quote_ident(table_name))) as size
                    FROM information_schema.tables 
                    WHERE table_schema = $1
                    ORDER BY table_name
                """, schema)
                
                tables = []
                for row in result:
                    table_data = {
                        "name": row["table_name"],
                        "type": row["table_type"],
                        "size": row["size"],
                        "schema": schema
                    }
                    tables.append(table_data)
                
                cache_key = f"{database_name}:{schema}"
                self.tables_cache[cache_key] = tables
                
                return {"tables": tables}
        
        except Exception as e:
            logger.error(f"Error getting PostgreSQL tables: {e}")
            raise
    
    async def _create_table(self, database_name: str, table: PostgreSQLTable) -> Dict[str, Any]:
        """Create a new table."""
        if not self.pool:
            raise Exception("PostgreSQL client not initialized")
        
        try:
            # Build CREATE TABLE statement
            columns = []
            for column in table.columns or []:
                col_def = f"{column['name']} {column['type']}"
                if column.get('not_null'):
                    col_def += " NOT NULL"
                if column.get('default'):
                    col_def += f" DEFAULT {column['default']}"
                columns.append(col_def)
            
            create_sql = f"""
                CREATE TABLE {table.schema}.{table.name} (
                    {', '.join(columns)}
                )
            """
            
            async with self.pool.acquire() as conn:
                await conn.execute(create_sql)
                
                # Create indexes if specified
                for index in table.indexes or []:
                    index_sql = f"""
                        CREATE INDEX {index['name']} 
                        ON {table.schema}.{table.name} ({index['columns']})
                    """
                    await conn.execute(index_sql)
            
            result = {
                "name": table.name,
                "schema": table.schema,
                "columns": table.columns,
                "indexes": table.indexes
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error creating PostgreSQL table: {e}")
            raise
    
    async def _create_database(self, database: PostgreSQLDatabase) -> Dict[str, Any]:
        """Create a new database."""
        if not self.pool:
            raise Exception("PostgreSQL client not initialized")
        
        try:
            # Connect to postgres database to create new database
            postgres_conn_string = self.connection_string.replace(
                self.connection_string.split('/')[-1], 'postgres'
            )
            
            async with asyncpg.create_pool(postgres_conn_string) as pool:
                async with pool.acquire() as conn:
                    create_sql = f"CREATE DATABASE {database.name}"
                    if database.owner:
                        create_sql += f" OWNER {database.owner}"
                    if database.encoding:
                        create_sql += f" ENCODING '{database.encoding}'"
                    if database.collation:
                        create_sql += f" LC_COLLATE '{database.collation}'"
                    
                    await conn.execute(create_sql)
            
            result = {
                "name": database.name,
                "owner": database.owner,
                "encoding": database.encoding,
                "collation": database.collation
            }
            
            self.databases_cache[database.name] = result
            return result
        
        except Exception as e:
            logger.error(f"Error creating PostgreSQL database: {e}")
            raise
    
    async def _get_table_info(self, database_name: str, table_name: str, schema: str = "public") -> Dict[str, Any]:
        """Get detailed table information."""
        if not self.pool:
            raise Exception("PostgreSQL client not initialized")
        
        try:
            async with self.pool.acquire() as conn:
                # Get column information
                columns_result = await conn.fetch("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale
                    FROM information_schema.columns 
                    WHERE table_schema = $1 AND table_name = $2
                    ORDER BY ordinal_position
                """, schema, table_name)
                
                # Get index information
                indexes_result = await conn.fetch("""
                    SELECT 
                        indexname,
                        indexdef
                    FROM pg_indexes 
                    WHERE schemaname = $1 AND tablename = $2
                """, schema, table_name)
                
                # Get table size
                size_result = await conn.fetchval("""
                    SELECT pg_size_pretty(pg_total_relation_size(quote_ident($1)||'.'||quote_ident($2)))
                """, schema, table_name)
                
                columns = []
                for row in columns_result:
                    col_data = {
                        "name": row["column_name"],
                        "type": row["data_type"],
                        "nullable": row["is_nullable"] == "YES",
                        "default": row["column_default"],
                        "max_length": row["character_maximum_length"],
                        "precision": row["numeric_precision"],
                        "scale": row["numeric_scale"]
                    }
                    columns.append(col_data)
                
                indexes = []
                for row in indexes_result:
                    index_data = {
                        "name": row["indexname"],
                        "definition": row["indexdef"]
                    }
                    indexes.append(index_data)
                
                result = {
                    "name": table_name,
                    "schema": schema,
                    "columns": columns,
                    "indexes": indexes,
                    "size": size_result
                }
                
                return result
        
        except Exception as e:
            logger.error(f"Error getting PostgreSQL table info: {e}")
            raise
    
    async def _backup_database(self, database_name: str, backup_path: str) -> Dict[str, Any]:
        """Create a database backup."""
        try:
            import subprocess
            import os
            
            # Create backup directory if it doesn't exist
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Extract connection details from connection string
            # This is a simplified version - in production you'd parse the connection string properly
            cmd = [
                "pg_dump",
                "-h", "localhost",  # Extract from connection string
                "-U", "postgres",   # Extract from connection string
                "-d", database_name,
                "-f", backup_path,
                "--verbose"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    "database": database_name,
                    "backup_path": backup_path,
                    "size": os.path.getsize(backup_path) if os.path.exists(backup_path) else 0
                }
            else:
                raise Exception(f"Backup failed: {result.stderr}")
        
        except Exception as e:
            logger.error(f"Error backing up PostgreSQL database: {e}")
            raise
    
    async def _restore_database(self, database_name: str, backup_path: str) -> Dict[str, Any]:
        """Restore a database from backup."""
        try:
            import subprocess
            
            cmd = [
                "pg_restore",
                "-h", "localhost",
                "-U", "postgres",
                "-d", database_name,
                "--verbose",
                backup_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    "database": database_name,
                    "backup_path": backup_path,
                    "restored": True
                }
            else:
                raise Exception(f"Restore failed: {result.stderr}")
        
        except Exception as e:
            logger.error(f"Error restoring PostgreSQL database: {e}")
            raise
    
    async def _get_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics."""
        if not self.pool:
            raise Exception("PostgreSQL client not initialized")
        
        try:
            async with self.pool.acquire() as conn:
                # Get active connections
                connections_result = await conn.fetchval("""
                    SELECT count(*) FROM pg_stat_activity WHERE state = 'active'
                """)
                
                # Get cache hit ratio
                cache_result = await conn.fetch("""
                    SELECT 
                        sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as cache_hit_ratio
                    FROM pg_statio_user_tables
                """)
                
                # Get slow queries
                slow_queries_result = await conn.fetch("""
                    SELECT 
                        query,
                        mean_time,
                        calls
                    FROM pg_stat_statements 
                    ORDER BY mean_time DESC 
                    LIMIT 10
                """)
                
                result = {
                    "active_connections": connections_result,
                    "cache_hit_ratio": cache_result[0]["cache_hit_ratio"] if cache_result else 0,
                    "slow_queries": [
                        {
                            "query": row["query"][:100] + "..." if len(row["query"]) > 100 else row["query"],
                            "mean_time": row["mean_time"],
                            "calls": row["calls"]
                        }
                        for row in slow_queries_result
                    ]
                }
                
                return result
        
        except Exception as e:
            logger.error(f"Error getting PostgreSQL performance stats: {e}")
            raise
    
    async def _load_databases(self):
        """Load databases into cache."""
        try:
            await self._get_databases()
            logger.info(f"Loaded {len(self.databases_cache)} databases")
        except Exception as e:
            logger.error(f"Failed to load databases: {e}")


# Create server instance
postgresql_server = PostgreSQLMCPServer()
app = postgresql_server.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006) 