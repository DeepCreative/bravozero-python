"""
Type definitions for Bravo Zero SDK
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Decision(str, Enum):
    """Constitution evaluation decision."""
    PERMIT = "permit"
    DENY = "deny"
    ESCALATE = "escalate"


class MemoryType(str, Enum):
    """Type of memory."""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"


class ConsolidationState(str, Enum):
    """Memory consolidation state."""
    ACTIVE = "active"
    CONSOLIDATING = "consolidating"
    CONSOLIDATED = "consolidated"
    DECAYING = "decaying"
    DORMANT = "dormant"


class AppliedRule(BaseModel):
    """A rule that was applied during evaluation."""
    rule_id: str
    name: str
    matched: bool
    contribution: float


class EvaluationResult(BaseModel):
    """Result of a Constitution Agent evaluation."""
    request_id: str
    decision: Decision
    confidence: float = Field(ge=0, le=1)
    alignment_score: float
    applied_rules: List[AppliedRule] = []
    reasoning: str = ""
    evaluated_at: datetime
    
    class Config:
        frozen = True


class OmegaScore(BaseModel):
    """Global Omega alignment score."""
    omega: float = Field(ge=0, le=1)
    components: Dict[str, float] = {}
    trend: str  # "improving", "stable", "degrading"
    timestamp: datetime
    
    class Config:
        frozen = True


class Memory(BaseModel):
    """A memory from the Trace Manifold."""
    id: str
    content: str
    memory_type: MemoryType
    importance: float = Field(ge=0, le=1)
    strength: float = Field(ge=0, le=1)
    consolidation_state: ConsolidationState
    namespace: str
    tags: List[str] = []
    created_at: datetime
    last_accessed_at: datetime
    access_count: int = 0
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = {}
    
    class Config:
        frozen = True


class MemoryQueryResult(BaseModel):
    """Result from a memory query."""
    memory: Memory
    relevance: float = Field(ge=0, le=1)
    
    class Config:
        frozen = True


class Edge(BaseModel):
    """An edge connecting two memories."""
    source_id: str
    target_id: str
    relationship: str
    strength: float = Field(ge=0, le=1)
    created_at: datetime
    last_strengthened_at: datetime
    
    class Config:
        frozen = True


class FileInfo(BaseModel):
    """Information about a file in the VFS."""
    path: str
    name: str
    size: int
    is_directory: bool
    modified_at: datetime
    created_at: Optional[datetime] = None
    permissions: str = ""
    
    class Config:
        frozen = True


class DirectoryListing(BaseModel):
    """Listing of files in a directory."""
    path: str
    files: List[FileInfo]
    total_count: int
    
    class Config:
        frozen = True


class SyncStatus(BaseModel):
    """VFS synchronization status."""
    path: str
    synced: bool
    last_sync_at: Optional[datetime] = None
    pending_changes: int = 0
    
    class Config:
        frozen = True


class RateLimitInfo(BaseModel):
    """Rate limit information."""
    limit: int
    remaining: int
    reset_at: datetime
    
    class Config:
        frozen = True
