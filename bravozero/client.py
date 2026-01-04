"""
Main Bravo Zero Client

Provides unified access to all Breaking the Limits services.
"""

import os
from pathlib import Path
from typing import Optional

from .constitution import ConstitutionClient
from .memory import MemoryClient
from .bridge import BridgeClient
from .auth import PersonaAuthenticator


class Client:
    """
    Main client for Bravo Zero Breaking the Limits APIs.
    
    Provides access to:
    - Constitution Agent for governance
    - Memory Service for persistent memory
    - Forge Bridge for VFS access
    
    Example:
        ```python
        from bravozero import Client
        
        client = Client(
            api_key="your-api-key",
            agent_id="your-agent-id",
        )
        
        # Evaluate an action
        result = client.constitution.evaluate(
            action="read_file",
            context={"path": "/src/main.py"}
        )
        
        # Store a memory
        memory = client.memory.record(
            content="User prefers dark mode",
            memory_type="semantic"
        )
        
        # Access files
        content = client.bridge.read_file("/project/README.md")
        ```
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        agent_id: Optional[str] = None,
        private_key_path: Optional[str] = None,
        base_url: Optional[str] = None,
        environment: str = "production",
        timeout: float = 30.0,
    ):
        """
        Initialize the Bravo Zero client.
        
        Args:
            api_key: API key for authentication. Defaults to BRAVOZERO_API_KEY env var.
            agent_id: PERSONA agent identifier. Defaults to BRAVOZERO_AGENT_ID env var.
            private_key_path: Path to Ed25519 private key for signing attestations.
            base_url: Override the default API base URL.
            environment: Environment to use (production, staging, development).
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key or os.environ.get("BRAVOZERO_API_KEY")
        self.agent_id = agent_id or os.environ.get("BRAVOZERO_AGENT_ID")
        self.environment = environment
        self.timeout = timeout
        
        if not self.api_key:
            raise ValueError(
                "API key required. Set BRAVOZERO_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        if not self.agent_id:
            raise ValueError(
                "Agent ID required. Set BRAVOZERO_AGENT_ID environment variable "
                "or pass agent_id parameter."
            )
        
        # Determine base URL
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = self._get_base_url(environment)
        
        # Initialize authenticator
        key_path = private_key_path or os.environ.get("BRAVOZERO_PRIVATE_KEY_PATH")
        if key_path:
            self._authenticator = PersonaAuthenticator(
                agent_id=self.agent_id,
                private_key_path=Path(key_path).expanduser(),
            )
        else:
            self._authenticator = None
        
        # Initialize service clients
        self._constitution: Optional[ConstitutionClient] = None
        self._memory: Optional[MemoryClient] = None
        self._bridge: Optional[BridgeClient] = None
    
    def _get_base_url(self, environment: str) -> str:
        """Get base URL for environment."""
        urls = {
            "production": "https://api.bravozero.ai",
            "staging": "https://api.staging.bravozero.ai",
            "development": "http://localhost:8080",
        }
        return urls.get(environment, urls["production"])
    
    @property
    def constitution(self) -> ConstitutionClient:
        """Get the Constitution Agent client."""
        if self._constitution is None:
            self._constitution = ConstitutionClient(
                base_url=self.base_url,
                api_key=self.api_key,
                agent_id=self.agent_id,
                authenticator=self._authenticator,
                timeout=self.timeout,
            )
        return self._constitution
    
    @property
    def memory(self) -> MemoryClient:
        """Get the Memory Service client."""
        if self._memory is None:
            self._memory = MemoryClient(
                base_url=self.base_url,
                api_key=self.api_key,
                agent_id=self.agent_id,
                authenticator=self._authenticator,
                timeout=self.timeout,
            )
        return self._memory
    
    @property
    def bridge(self) -> BridgeClient:
        """Get the Forge Bridge client."""
        if self._bridge is None:
            self._bridge = BridgeClient(
                base_url=self.base_url,
                api_key=self.api_key,
                agent_id=self.agent_id,
                authenticator=self._authenticator,
                timeout=self.timeout,
            )
        return self._bridge
    
    async def close(self) -> None:
        """Close all client connections."""
        if self._constitution:
            await self._constitution.close()
        if self._memory:
            await self._memory.close()
        if self._bridge:
            await self._bridge.close()
    
    async def __aenter__(self) -> "Client":
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
