"""
Memory Service Client

Provides access to the Trace Manifold persistent memory system.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from .types import (
    Memory,
    MemoryType,
    MemoryQueryResult,
    Edge,
    ConsolidationState,
)
from .exceptions import MemoryError, RateLimitError
from .auth import PersonaAuthenticator


class MemoryClient:
    """
    Client for the Memory Service API.
    
    Provides access to the Trace Manifold for storing and
    retrieving persistent memories.
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        agent_id: str,
        authenticator: Optional[PersonaAuthenticator] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.agent_id = agent_id
        self.authenticator = authenticator
        self.timeout = timeout
        
        self._client = httpx.AsyncClient(
            base_url=f"{self.base_url}/v1/memory",
            timeout=timeout,
            headers=self._default_headers(),
        )
    
    def _default_headers(self) -> Dict[str, str]:
        """Get default headers for requests."""
        return {
            "X-API-Key": self.api_key,
            "X-Agent-ID": self.agent_id,
            "Content-Type": "application/json",
            "User-Agent": "bravozero-python/1.0.0",
        }
    
    async def _get_attestation(self) -> Optional[str]:
        """Get PERSONA attestation for request signing."""
        if self.authenticator:
            return await self.authenticator.create_attestation()
        return None
    
    async def record(
        self,
        content: str,
        memory_type: str = "semantic",
        importance: float = 0.5,
        namespace: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        """
        Record a new memory to the Trace Manifold.
        
        Args:
            content: The content to remember
            memory_type: Type of memory (episodic, semantic, procedural, working)
            importance: Importance score from 0 to 1
            namespace: Optional namespace for organization
            tags: Optional tags for categorization
            metadata: Optional additional metadata
        
        Returns:
            The created Memory object
        """
        headers = {}
        attestation = await self._get_attestation()
        if attestation:
            headers["X-Persona-Attestation"] = attestation
        
        response = await self._client.post(
            "/record",
            json={
                "content": content,
                "memoryType": memory_type,
                "importance": importance,
                "namespace": namespace or self.agent_id,
                "tags": tags or [],
                "metadata": metadata or {},
            },
            headers=headers,
        )
        
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            raise RateLimitError(
                message="Rate limit exceeded",
                retry_after=retry_after,
            )
        
        response.raise_for_status()
        return self._parse_memory(response.json())
    
    async def query(
        self,
        query: str,
        limit: int = 10,
        min_relevance: float = 0.5,
        memory_types: Optional[List[str]] = None,
        namespace: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[MemoryQueryResult]:
        """
        Query memories by semantic similarity.
        
        Args:
            query: Natural language query
            limit: Maximum number of results
            min_relevance: Minimum relevance threshold (0-1)
            memory_types: Filter by memory types
            namespace: Filter by namespace
            tags: Filter by tags
        
        Returns:
            List of MemoryQueryResult with relevance scores
        """
        response = await self._client.post(
            "/query",
            json={
                "query": query,
                "limit": limit,
                "minRelevance": min_relevance,
                "memoryTypes": memory_types,
                "namespace": namespace,
                "tags": tags,
            },
        )
        
        response.raise_for_status()
        data = response.json()
        
        return [
            MemoryQueryResult(
                memory=self._parse_memory(r["memory"]),
                relevance=r["relevance"],
            )
            for r in data.get("results", [])
        ]
    
    async def get(self, memory_id: str) -> Memory:
        """
        Get a specific memory by ID.
        
        Args:
            memory_id: The memory identifier
        
        Returns:
            The Memory object
        """
        response = await self._client.get(f"/{memory_id}")
        response.raise_for_status()
        return self._parse_memory(response.json())
    
    async def update(
        self,
        memory_id: str,
        content: Optional[str] = None,
        importance: Optional[float] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        """
        Update an existing memory.
        
        Args:
            memory_id: The memory identifier
            content: New content (optional)
            importance: New importance score (optional)
            tags: New tags (optional)
            metadata: New metadata (optional)
        
        Returns:
            The updated Memory object
        """
        update_data = {}
        if content is not None:
            update_data["content"] = content
        if importance is not None:
            update_data["importance"] = importance
        if tags is not None:
            update_data["tags"] = tags
        if metadata is not None:
            update_data["metadata"] = metadata
        
        response = await self._client.patch(
            f"/{memory_id}",
            json=update_data,
        )
        response.raise_for_status()
        return self._parse_memory(response.json())
    
    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: The memory identifier
        
        Returns:
            True if deleted successfully
        """
        response = await self._client.delete(f"/{memory_id}")
        response.raise_for_status()
        return True
    
    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        strength: float = 0.5,
    ) -> Edge:
        """
        Create an edge between two memories.
        
        Args:
            source_id: Source memory ID
            target_id: Target memory ID
            relationship: Type of relationship
            strength: Initial edge strength (0-1)
        
        Returns:
            The created Edge
        """
        response = await self._client.post(
            "/edges",
            json={
                "sourceId": source_id,
                "targetId": target_id,
                "relationship": relationship,
                "strength": strength,
            },
        )
        response.raise_for_status()
        data = response.json()
        
        return Edge(
            source_id=data["sourceId"],
            target_id=data["targetId"],
            relationship=data["relationship"],
            strength=data["strength"],
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")),
            last_strengthened_at=datetime.fromisoformat(data["lastStrengthenedAt"].replace("Z", "+00:00")),
        )
    
    async def get_related(
        self,
        memory_id: str,
        relationship: Optional[str] = None,
        min_strength: float = 0.1,
        limit: int = 20,
    ) -> List[MemoryQueryResult]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: The source memory ID
            relationship: Filter by relationship type
            min_strength: Minimum edge strength
            limit: Maximum results
        
        Returns:
            List of related memories with edge strength as relevance
        """
        params = {
            "minStrength": min_strength,
            "limit": limit,
        }
        if relationship:
            params["relationship"] = relationship
        
        response = await self._client.get(
            f"/{memory_id}/related",
            params=params,
        )
        response.raise_for_status()
        data = response.json()
        
        return [
            MemoryQueryResult(
                memory=self._parse_memory(r["memory"]),
                relevance=r["edgeStrength"],
            )
            for r in data.get("results", [])
        ]
    
    def _parse_memory(self, data: Dict[str, Any]) -> Memory:
        """Parse a memory from API response."""
        return Memory(
            id=data["id"],
            content=data["content"],
            memory_type=MemoryType(data["memoryType"]),
            importance=data["importance"],
            strength=data.get("strength", 1.0),
            consolidation_state=ConsolidationState(data.get("consolidationState", "active")),
            namespace=data["namespace"],
            tags=data.get("tags", []),
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")),
            last_accessed_at=datetime.fromisoformat(data["lastAccessedAt"].replace("Z", "+00:00")),
            access_count=data.get("accessCount", 0),
            embedding=data.get("embedding"),
            metadata=data.get("metadata", {}),
        )
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
