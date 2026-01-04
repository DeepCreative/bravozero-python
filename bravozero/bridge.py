"""
Forge Bridge Client

Provides VFS access to repositories through the Forge-Logos bridge.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from .types import FileInfo, DirectoryListing, SyncStatus
from .exceptions import BridgeError, RateLimitError
from .auth import PersonaAuthenticator


class BridgeClient:
    """
    Client for the Forge Bridge API.
    
    Provides access to the Virtualized Filesystem (VFS) for
    reading and writing repository files.
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
            base_url=f"{self.base_url}/v1/bridge",
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
    
    async def list_files(
        self,
        path: str,
        recursive: bool = False,
        pattern: Optional[str] = None,
    ) -> DirectoryListing:
        """
        List files in a directory.
        
        Args:
            path: Directory path to list
            recursive: Whether to list recursively
            pattern: Optional glob pattern to filter files
        
        Returns:
            DirectoryListing with file information
        """
        response = await self._client.get(
            "/files",
            params={
                "path": path,
                "recursive": str(recursive).lower(),
                "pattern": pattern,
            },
        )
        
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            raise RateLimitError(
                message="Rate limit exceeded",
                retry_after=retry_after,
            )
        
        response.raise_for_status()
        data = response.json()
        
        return DirectoryListing(
            path=data["path"],
            files=[self._parse_file_info(f) for f in data["files"]],
            total_count=data.get("totalCount", len(data["files"])),
        )
    
    async def read_file(self, path: str) -> str:
        """
        Read a file's contents.
        
        Args:
            path: Path to the file
        
        Returns:
            File contents as string
        """
        headers = {}
        attestation = await self._get_attestation()
        if attestation:
            headers["X-Persona-Attestation"] = attestation
        
        response = await self._client.get(
            "/file",
            params={"path": path},
            headers=headers,
        )
        
        response.raise_for_status()
        data = response.json()
        return data["content"]
    
    async def read_file_bytes(self, path: str) -> bytes:
        """
        Read a file as bytes.
        
        Args:
            path: Path to the file
        
        Returns:
            File contents as bytes
        """
        headers = {"Accept": "application/octet-stream"}
        attestation = await self._get_attestation()
        if attestation:
            headers["X-Persona-Attestation"] = attestation
        
        response = await self._client.get(
            "/file/bytes",
            params={"path": path},
            headers=headers,
        )
        
        response.raise_for_status()
        return response.content
    
    async def write_file(
        self,
        path: str,
        content: str,
        create_dirs: bool = True,
    ) -> FileInfo:
        """
        Write content to a file.
        
        Args:
            path: Path to the file
            content: Content to write
            create_dirs: Whether to create parent directories
        
        Returns:
            FileInfo for the written file
        """
        headers = {}
        attestation = await self._get_attestation()
        if attestation:
            headers["X-Persona-Attestation"] = attestation
        
        response = await self._client.put(
            "/file",
            json={
                "path": path,
                "content": content,
                "createDirs": create_dirs,
            },
            headers=headers,
        )
        
        response.raise_for_status()
        return self._parse_file_info(response.json())
    
    async def delete_file(self, path: str) -> bool:
        """
        Delete a file.
        
        Args:
            path: Path to the file
        
        Returns:
            True if deleted successfully
        """
        headers = {}
        attestation = await self._get_attestation()
        if attestation:
            headers["X-Persona-Attestation"] = attestation
        
        response = await self._client.delete(
            "/file",
            params={"path": path},
            headers=headers,
        )
        
        response.raise_for_status()
        return True
    
    async def get_file_info(self, path: str) -> FileInfo:
        """
        Get information about a file.
        
        Args:
            path: Path to the file
        
        Returns:
            FileInfo object
        """
        response = await self._client.get(
            "/file/info",
            params={"path": path},
        )
        
        response.raise_for_status()
        return self._parse_file_info(response.json())
    
    async def sync(self, path: str = "/") -> SyncStatus:
        """
        Trigger VFS synchronization.
        
        Args:
            path: Path to sync (default: root)
        
        Returns:
            SyncStatus with sync information
        """
        response = await self._client.post(
            "/sync",
            json={"path": path},
        )
        
        response.raise_for_status()
        data = response.json()
        
        return SyncStatus(
            path=data["path"],
            synced=data["synced"],
            last_sync_at=datetime.fromisoformat(data["lastSyncAt"].replace("Z", "+00:00")) if data.get("lastSyncAt") else None,
            pending_changes=data.get("pendingChanges", 0),
        )
    
    async def get_sync_status(self, path: str = "/") -> SyncStatus:
        """
        Get current sync status.
        
        Args:
            path: Path to check
        
        Returns:
            SyncStatus object
        """
        response = await self._client.get(
            "/sync/status",
            params={"path": path},
        )
        
        response.raise_for_status()
        data = response.json()
        
        return SyncStatus(
            path=data["path"],
            synced=data["synced"],
            last_sync_at=datetime.fromisoformat(data["lastSyncAt"].replace("Z", "+00:00")) if data.get("lastSyncAt") else None,
            pending_changes=data.get("pendingChanges", 0),
        )
    
    def _parse_file_info(self, data: Dict[str, Any]) -> FileInfo:
        """Parse file info from API response."""
        return FileInfo(
            path=data["path"],
            name=data["name"],
            size=data["size"],
            is_directory=data["isDirectory"],
            modified_at=datetime.fromisoformat(data["modifiedAt"].replace("Z", "+00:00")),
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")) if data.get("createdAt") else None,
            permissions=data.get("permissions", ""),
        )
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
