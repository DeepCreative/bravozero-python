"""
Constitution Agent Client

Provides governance and alignment enforcement for AI agents.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from .types import AppliedRule, Decision, EvaluationResult, OmegaScore
from .exceptions import ConstitutionDeniedError, RateLimitError
from .auth import PersonaAuthenticator


class ConstitutionClient:
    """
    Client for the Constitution Agent API.
    
    Evaluates agent actions against the constitution and provides
    alignment scoring.
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
            base_url=f"{self.base_url}/v1/constitution",
            timeout=timeout,
            headers=self._default_headers(),
        )
    
    def _default_headers(self) -> Dict[str, str]:
        """Get default headers for requests."""
        headers = {
            "X-API-Key": self.api_key,
            "X-Agent-ID": self.agent_id,
            "Content-Type": "application/json",
            "User-Agent": "bravozero-python/1.0.0",
        }
        return headers
    
    async def _get_attestation(self) -> Optional[str]:
        """Get PERSONA attestation for request signing."""
        if self.authenticator:
            return await self.authenticator.create_attestation()
        return None
    
    async def evaluate(
        self,
        action: str,
        context: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
    ) -> EvaluationResult:
        """
        Evaluate an action against the constitution.
        
        Args:
            action: The action to evaluate (e.g., "read_file", "execute_code")
            context: Additional context for evaluation
            priority: Request priority (normal, high, critical)
        
        Returns:
            EvaluationResult with decision and reasoning
        
        Raises:
            ConstitutionDeniedError: If action is denied
            RateLimitError: If rate limit exceeded
        """
        headers = {}
        attestation = await self._get_attestation()
        if attestation:
            headers["X-Persona-Attestation"] = attestation
        
        response = await self._client.post(
            "/evaluate",
            json={
                "agentId": self.agent_id,
                "action": action,
                "context": context or {},
                "priority": priority,
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
        data = response.json()
        
        result = EvaluationResult(
            request_id=data["requestId"],
            decision=Decision(data["decision"]),
            confidence=data["confidence"],
            alignment_score=data["alignmentScore"],
            applied_rules=[
                AppliedRule(
                    rule_id=r["ruleId"],
                    name=r["name"],
                    matched=r["matched"],
                    contribution=r["contribution"],
                )
                for r in data.get("appliedRules", [])
            ],
            reasoning=data.get("reasoning", ""),
            evaluated_at=datetime.fromisoformat(data["evaluatedAt"].replace("Z", "+00:00")),
        )
        
        if result.decision == Decision.DENY:
            raise ConstitutionDeniedError(
                message=result.reasoning,
                result=result,
            )
        
        return result
    
    async def get_omega(self) -> OmegaScore:
        """
        Get the current global Omega alignment score.
        
        Returns:
            OmegaScore with current value and components
        """
        response = await self._client.get("/omega")
        response.raise_for_status()
        data = response.json()
        
        return OmegaScore(
            omega=data["omega"],
            components=data.get("components", {}),
            trend=data.get("trend", "stable"),
            timestamp=datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00")),
        )
    
    async def list_rules(
        self,
        category: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List constitution rules.
        
        Args:
            category: Filter by category
            priority: Filter by priority (critical, high, medium, low)
        
        Returns:
            List of rule definitions
        """
        params = {}
        if category:
            params["category"] = category
        if priority:
            params["priority"] = priority
        
        response = await self._client.get("/rules", params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_rule(self, rule_id: str) -> Dict[str, Any]:
        """
        Get a specific rule by ID.
        
        Args:
            rule_id: The rule identifier
        
        Returns:
            Rule definition
        """
        response = await self._client.get(f"/rules/{rule_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_values(self) -> Dict[str, Any]:
        """
        Get the current values database.
        
        Returns:
            Values database with current value definitions
        """
        response = await self._client.get("/values")
        response.raise_for_status()
        return response.json()
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
