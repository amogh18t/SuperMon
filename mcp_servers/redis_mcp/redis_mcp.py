"""Redis MCP Server for SuperMon platform."""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import redis.asyncio as redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RedisKeyValue(BaseModel):
    """Redis key-value model."""
    key: str = Field(..., description="Redis key")
    value: Union[str, int, float, bool, Dict[str, Any], List[Any]] = Field(..., description="Redis value")
    ttl: Optional[int] = Field(None, description="Time to live in seconds")
    data_type: str = Field(default="string", description="Redis data type")


class RedisHash(BaseModel):
    """Redis hash model."""
    key: str = Field(..., description="Hash key")
    fields: Dict[str, Any] = Field(..., description="Hash fields")
    ttl: Optional[int] = Field(None, description="Time to live in seconds")


class RedisList(BaseModel):
    """Redis list model."""
    key: str = Field(..., description="List key")
    values: List[Any] = Field(..., description="List values")
    ttl: Optional[int] = Field(None, description="Time to live in seconds")


class RedisSet(BaseModel):
    """Redis set model."""
    key: str = Field(..., description="Set key")
    values: List[Any] = Field(..., description="Set values")
    ttl: Optional[int] = Field(None, description="Time to live in seconds")


class RedisSortedSet(BaseModel):
    """Redis sorted set model."""
    key: str = Field(..., description="Sorted set key")
    members: Dict[str, float] = Field(..., description="Set members with scores")
    ttl: Optional[int] = Field(None, description="Time to live in seconds")


class RedisMCPResponse(BaseModel):
    """Standard MCP response model."""
    success: bool = Field(..., description="Operation success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class RedisMCPServer:
    """Redis MCP Server implementation."""
    
    def __init__(self):
        """Initialize Redis MCP Server."""
        self.app = FastAPI(title="Redis MCP Server", version="1.0.0")
        self.client: Optional[redis.Redis] = None
        self.connection_string: Optional[str] = None
        self.keys_cache: Dict[str, Dict[str, Any]] = {}
        
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
            """Initialize Redis client on startup."""
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
                "service": "Redis MCP Server",
                "connected": self.client is not None,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.post("/set")
        async def set_key_value(kv: RedisKeyValue):
            """Set a key-value pair."""
            try:
                result = await self._set_key_value(kv)
                return RedisMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error setting key-value: {e}")
                return RedisMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/get/{key}")
        async def get_value(key: str):
            """Get a value by key."""
            try:
                result = await self._get_value(key)
                return RedisMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting value: {e}")
                return RedisMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.delete("/delete/{key}")
        async def delete_key(key: str):
            """Delete a key."""
            try:
                result = await self._delete_key(key)
                return RedisMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error deleting key: {e}")
                return RedisMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/set-hash")
        async def set_hash(hash_data: RedisHash):
            """Set a hash."""
            try:
                result = await self._set_hash(hash_data)
                return RedisMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error setting hash: {e}")
                return RedisMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/get-hash/{key}")
        async def get_hash(key: str):
            """Get a hash."""
            try:
                result = await self._get_hash(key)
                return RedisMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting hash: {e}")
                return RedisMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/set-list")
        async def set_list(list_data: RedisList):
            """Set a list."""
            try:
                result = await self._set_list(list_data)
                return RedisMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error setting list: {e}")
                return RedisMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/get-list/{key}")
        async def get_list(key: str, start: int = 0, end: int = -1):
            """Get a list."""
            try:
                result = await self._get_list(key, start, end)
                return RedisMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting list: {e}")
                return RedisMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/set-set")
        async def set_set(set_data: RedisSet):
            """Set a set."""
            try:
                result = await self._set_set(set_data)
                return RedisMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error setting set: {e}")
                return RedisMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/get-set/{key}")
        async def get_set(key: str):
            """Get a set."""
            try:
                result = await self._get_set(key)
                return RedisMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting set: {e}")
                return RedisMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/set-sorted-set")
        async def set_sorted_set(sorted_set_data: RedisSortedSet):
            """Set a sorted set."""
            try:
                result = await self._set_sorted_set(sorted_set_data)
                return RedisMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error setting sorted set: {e}")
                return RedisMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/get-sorted-set/{key}")
        async def get_sorted_set(key: str, start: int = 0, end: int = -1, with_scores: bool = False):
            """Get a sorted set."""
            try:
                result = await self._get_sorted_set(key, start, end, with_scores)
                return RedisMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting sorted set: {e}")
                return RedisMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/keys")
        async def get_keys(pattern: str = "*"):
            """Get keys matching pattern."""
            try:
                result = await self._get_keys(pattern)
                return RedisMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting keys: {e}")
                return RedisMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/info")
        async def get_info():
            """Get Redis server information."""
            try:
                result = await self._get_info()
                return RedisMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting Redis info: {e}")
                return RedisMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/expire/{key}")
        async def set_expiry(key: str, ttl: int):
            """Set expiry for a key."""
            try:
                result = await self._set_expiry(key, ttl)
                return RedisMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error setting expiry: {e}")
                return RedisMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/ttl/{key}")
        async def get_ttl(key: str):
            """Get TTL for a key."""
            try:
                result = await self._get_ttl(key)
                return RedisMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting TTL: {e}")
                return RedisMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/flush")
        async def flush_database():
            """Flush the database."""
            try:
                result = await self._flush_database()
                return RedisMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error flushing database: {e}")
                return RedisMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
    
    async def _initialize_client(self):
        """Initialize Redis client."""
        self.connection_string = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        try:
            self.client = redis.from_url(
                self.connection_string,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.client.ping()
            logger.info("Connected to Redis server")
            
            # Load initial data
            await self._load_keys()
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            self.client = None
    
    async def _cleanup(self):
        """Cleanup resources."""
        if self.client:
            await self.client.close()
    
    async def _set_key_value(self, kv: RedisKeyValue) -> Dict[str, Any]:
        """Set a key-value pair."""
        if not self.client:
            raise Exception("Redis client not initialized")
        
        try:
            # Convert value to appropriate format
            if kv.data_type == "json":
                value = json.dumps(kv.value)
            else:
                value = str(kv.value)
            
            # Set the key
            await self.client.set(kv.key, value)
            
            # Set TTL if specified
            if kv.ttl:
                await self.client.expire(kv.key, kv.ttl)
            
            result = {
                "key": kv.key,
                "value": kv.value,
                "data_type": kv.data_type,
                "ttl": kv.ttl
            }
            
            self.keys_cache[kv.key] = result
            return result
        
        except Exception as e:
            logger.error(f"Error setting Redis key-value: {e}")
            raise
    
    async def _get_value(self, key: str) -> Dict[str, Any]:
        """Get a value by key."""
        if not self.client:
            raise Exception("Redis client not initialized")
        
        try:
            value = await self.client.get(key)
            
            if value is None:
                raise Exception(f"Key {key} not found")
            
            # Try to parse as JSON
            try:
                parsed_value = json.loads(value)
                data_type = "json"
            except (json.JSONDecodeError, TypeError):
                parsed_value = value
                data_type = "string"
            
            # Get TTL
            ttl = await self.client.ttl(key)
            
            result = {
                "key": key,
                "value": parsed_value,
                "data_type": data_type,
                "ttl": ttl if ttl > 0 else None
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error getting Redis value: {e}")
            raise
    
    async def _delete_key(self, key: str) -> Dict[str, Any]:
        """Delete a key."""
        if not self.client:
            raise Exception("Redis client not initialized")
        
        try:
            deleted = await self.client.delete(key)
            
            if key in self.keys_cache:
                del self.keys_cache[key]
            
            return {
                "key": key,
                "deleted": deleted > 0
            }
        
        except Exception as e:
            logger.error(f"Error deleting Redis key: {e}")
            raise
    
    async def _set_hash(self, hash_data: RedisHash) -> Dict[str, Any]:
        """Set a hash."""
        if not self.client:
            raise Exception("Redis client not initialized")
        
        try:
            # Set hash fields
            await self.client.hset(hash_data.key, mapping=hash_data.fields)
            
            # Set TTL if specified
            if hash_data.ttl:
                await self.client.expire(hash_data.key, hash_data.ttl)
            
            result = {
                "key": hash_data.key,
                "fields": hash_data.fields,
                "ttl": hash_data.ttl
            }
            
            self.keys_cache[hash_data.key] = result
            return result
        
        except Exception as e:
            logger.error(f"Error setting Redis hash: {e}")
            raise
    
    async def _get_hash(self, key: str) -> Dict[str, Any]:
        """Get a hash."""
        if not self.client:
            raise Exception("Redis client not initialized")
        
        try:
            fields = await self.client.hgetall(key)
            
            if not fields:
                raise Exception(f"Hash {key} not found")
            
            # Get TTL
            ttl = await self.client.ttl(key)
            
            result = {
                "key": key,
                "fields": fields,
                "ttl": ttl if ttl > 0 else None
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error getting Redis hash: {e}")
            raise
    
    async def _set_list(self, list_data: RedisList) -> Dict[str, Any]:
        """Set a list."""
        if not self.client:
            raise Exception("Redis client not initialized")
        
        try:
            # Clear existing list
            await self.client.delete(list_data.key)
            
            # Add values to list
            if list_data.values:
                await self.client.rpush(list_data.key, *list_data.values)
            
            # Set TTL if specified
            if list_data.ttl:
                await self.client.expire(list_data.key, list_data.ttl)
            
            result = {
                "key": list_data.key,
                "values": list_data.values,
                "ttl": list_data.ttl
            }
            
            self.keys_cache[list_data.key] = result
            return result
        
        except Exception as e:
            logger.error(f"Error setting Redis list: {e}")
            raise
    
    async def _get_list(self, key: str, start: int = 0, end: int = -1) -> Dict[str, Any]:
        """Get a list."""
        if not self.client:
            raise Exception("Redis client not initialized")
        
        try:
            values = await self.client.lrange(key, start, end)
            
            if not values:
                raise Exception(f"List {key} not found")
            
            # Get TTL
            ttl = await self.client.ttl(key)
            
            result = {
                "key": key,
                "values": values,
                "start": start,
                "end": end,
                "ttl": ttl if ttl > 0 else None
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error getting Redis list: {e}")
            raise
    
    async def _set_set(self, set_data: RedisSet) -> Dict[str, Any]:
        """Set a set."""
        if not self.client:
            raise Exception("Redis client not initialized")
        
        try:
            # Clear existing set
            await self.client.delete(set_data.key)
            
            # Add values to set
            if set_data.values:
                await self.client.sadd(set_data.key, *set_data.values)
            
            # Set TTL if specified
            if set_data.ttl:
                await self.client.expire(set_data.key, set_data.ttl)
            
            result = {
                "key": set_data.key,
                "values": set_data.values,
                "ttl": set_data.ttl
            }
            
            self.keys_cache[set_data.key] = result
            return result
        
        except Exception as e:
            logger.error(f"Error setting Redis set: {e}")
            raise
    
    async def _get_set(self, key: str) -> Dict[str, Any]:
        """Get a set."""
        if not self.client:
            raise Exception("Redis client not initialized")
        
        try:
            values = await self.client.smembers(key)
            
            if not values:
                raise Exception(f"Set {key} not found")
            
            # Get TTL
            ttl = await self.client.ttl(key)
            
            result = {
                "key": key,
                "values": list(values),
                "ttl": ttl if ttl > 0 else None
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error getting Redis set: {e}")
            raise
    
    async def _set_sorted_set(self, sorted_set_data: RedisSortedSet) -> Dict[str, Any]:
        """Set a sorted set."""
        if not self.client:
            raise Exception("Redis client not initialized")
        
        try:
            # Clear existing sorted set
            await self.client.delete(sorted_set_data.key)
            
            # Add members to sorted set
            if sorted_set_data.members:
                await self.client.zadd(sorted_set_data.key, sorted_set_data.members)
            
            # Set TTL if specified
            if sorted_set_data.ttl:
                await self.client.expire(sorted_set_data.key, sorted_set_data.ttl)
            
            result = {
                "key": sorted_set_data.key,
                "members": sorted_set_data.members,
                "ttl": sorted_set_data.ttl
            }
            
            self.keys_cache[sorted_set_data.key] = result
            return result
        
        except Exception as e:
            logger.error(f"Error setting Redis sorted set: {e}")
            raise
    
    async def _get_sorted_set(self, key: str, start: int = 0, end: int = -1, with_scores: bool = False) -> Dict[str, Any]:
        """Get a sorted set."""
        if not self.client:
            raise Exception("Redis client not initialized")
        
        try:
            if with_scores:
                members = await self.client.zrange(key, start, end, withscores=True)
                members_dict = {member: score for member, score in members}
            else:
                members = await self.client.zrange(key, start, end)
                members_dict = {member: None for member in members}
            
            if not members:
                raise Exception(f"Sorted set {key} not found")
            
            # Get TTL
            ttl = await self.client.ttl(key)
            
            result = {
                "key": key,
                "members": members_dict,
                "start": start,
                "end": end,
                "with_scores": with_scores,
                "ttl": ttl if ttl > 0 else None
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error getting Redis sorted set: {e}")
            raise
    
    async def _get_keys(self, pattern: str = "*") -> Dict[str, Any]:
        """Get keys matching pattern."""
        if not self.client:
            raise Exception("Redis client not initialized")
        
        try:
            keys = await self.client.keys(pattern)
            
            result = {
                "pattern": pattern,
                "keys": keys,
                "count": len(keys)
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error getting Redis keys: {e}")
            raise
    
    async def _get_info(self) -> Dict[str, Any]:
        """Get Redis server information."""
        if not self.client:
            raise Exception("Redis client not initialized")
        
        try:
            info = await self.client.info()
            
            # Parse info into sections
            sections = {}
            current_section = None
            
            for line in info.split('\n'):
                if line.startswith('#'):
                    current_section = line[1:].strip()
                    sections[current_section] = {}
                elif ':' in line and current_section:
                    key, value = line.split(':', 1)
                    sections[current_section][key.strip()] = value.strip()
            
            result = {
                "server": sections.get("Server", {}),
                "clients": sections.get("Clients", {}),
                "memory": sections.get("Memory", {}),
                "persistence": sections.get("Persistence", {}),
                "stats": sections.get("Stats", {}),
                "replication": sections.get("Replication", {}),
                "cpu": sections.get("CPU", {}),
                "cluster": sections.get("Cluster", {}),
                "keyspace": sections.get("Keyspace", {})
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error getting Redis info: {e}")
            raise
    
    async def _set_expiry(self, key: str, ttl: int) -> Dict[str, Any]:
        """Set expiry for a key."""
        if not self.client:
            raise Exception("Redis client not initialized")
        
        try:
            result = await self.client.expire(key, ttl)
            
            return {
                "key": key,
                "ttl": ttl,
                "set": result
            }
        
        except Exception as e:
            logger.error(f"Error setting Redis expiry: {e}")
            raise
    
    async def _get_ttl(self, key: str) -> Dict[str, Any]:
        """Get TTL for a key."""
        if not self.client:
            raise Exception("Redis client not initialized")
        
        try:
            ttl = await self.client.ttl(key)
            
            return {
                "key": key,
                "ttl": ttl if ttl > 0 else None,
                "exists": ttl != -2
            }
        
        except Exception as e:
            logger.error(f"Error getting Redis TTL: {e}")
            raise
    
    async def _flush_database(self) -> Dict[str, Any]:
        """Flush the database."""
        if not self.client:
            raise Exception("Redis client not initialized")
        
        try:
            result = await self.client.flushdb()
            
            # Clear cache
            self.keys_cache.clear()
            
            return {
                "flushed": result,
                "message": "Database flushed successfully"
            }
        
        except Exception as e:
            logger.error(f"Error flushing Redis database: {e}")
            raise
    
    async def _load_keys(self):
        """Load keys into cache."""
        try:
            keys = await self._get_keys()
            logger.info(f"Loaded {keys['count']} keys")
        except Exception as e:
            logger.error(f"Failed to load keys: {e}")


# Create server instance
redis_server = RedisMCPServer()
app = redis_server.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009) 