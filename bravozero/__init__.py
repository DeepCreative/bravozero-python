"""
Bravo Zero Python SDK

Official SDK for interacting with Breaking the Limits APIs:
- Constitution Agent: Governance and alignment enforcement
- Memory Service: Trace Manifold persistent memory
- Forge Bridge: VFS and repository access
"""

from .client import Client
from .constitution import ConstitutionClient
from .memory import MemoryClient
from .bridge import BridgeClient
from .types import (
    EvaluationResult,
    Decision,
    Memory,
    MemoryType,
    FileInfo,
    OmegaScore,
)
from .exceptions import (
    BravoZeroError,
    AuthenticationError,
    RateLimitError,
    ConstitutionDeniedError,
    MemoryError,
    BridgeError,
)

__version__ = "1.0.0"
__all__ = [
    # Main client
    "Client",
    # Service clients
    "ConstitutionClient",
    "MemoryClient",
    "BridgeClient",
    # Types
    "EvaluationResult",
    "Decision",
    "Memory",
    "MemoryType",
    "FileInfo",
    "OmegaScore",
    # Exceptions
    "BravoZeroError",
    "AuthenticationError",
    "RateLimitError",
    "ConstitutionDeniedError",
    "MemoryError",
    "BridgeError",
]
