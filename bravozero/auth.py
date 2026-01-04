"""
PERSONA Authentication

Handles Ed25519 signing for PERSONA attestation.
"""

import base64
import json
import time
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


class PersonaAuthenticator:
    """
    PERSONA authenticator for signing attestations.
    
    Uses Ed25519 signatures to create cryptographically
    verifiable attestations for API requests.
    """
    
    def __init__(
        self,
        agent_id: str,
        private_key_path: Optional[Path] = None,
        private_key_bytes: Optional[bytes] = None,
    ):
        """
        Initialize the authenticator.
        
        Args:
            agent_id: PERSONA agent identifier
            private_key_path: Path to Ed25519 private key PEM file
            private_key_bytes: Raw private key bytes (alternative to path)
        """
        self.agent_id = agent_id
        
        if private_key_path:
            self._private_key = self._load_private_key(private_key_path)
        elif private_key_bytes:
            self._private_key = serialization.load_pem_private_key(
                private_key_bytes, password=None
            )
        else:
            raise ValueError(
                "Either private_key_path or private_key_bytes required"
            )
        
        if not isinstance(self._private_key, Ed25519PrivateKey):
            raise ValueError("Private key must be Ed25519")
    
    def _load_private_key(self, path: Path) -> Ed25519PrivateKey:
        """Load private key from PEM file."""
        with open(path, "rb") as f:
            key = serialization.load_pem_private_key(f.read(), password=None)
        
        if not isinstance(key, Ed25519PrivateKey):
            raise ValueError(f"Key at {path} is not Ed25519")
        
        return key
    
    async def create_attestation(
        self,
        action: Optional[str] = None,
        nonce: Optional[str] = None,
    ) -> str:
        """
        Create a signed PERSONA attestation.
        
        Args:
            action: Optional action being attested
            nonce: Optional nonce for replay protection
        
        Returns:
            Base64-encoded attestation string
        """
        timestamp = int(time.time())
        
        # Build attestation payload
        payload = {
            "agent_id": self.agent_id,
            "timestamp": timestamp,
            "nonce": nonce or f"{timestamp}-{id(self)}",
        }
        
        if action:
            payload["action"] = action
        
        # Serialize payload
        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        
        # Sign with Ed25519
        signature = self._private_key.sign(payload_bytes)
        
        # Combine payload and signature
        attestation = {
            "payload": base64.b64encode(payload_bytes).decode("ascii"),
            "signature": base64.b64encode(signature).decode("ascii"),
            "algorithm": "Ed25519",
        }
        
        # Return as base64 JSON
        return base64.b64encode(
            json.dumps(attestation).encode("utf-8")
        ).decode("ascii")
    
    def get_public_key(self) -> bytes:
        """Get the public key in PEM format."""
        public_key = self._private_key.public_key()
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    
    def get_public_key_base64(self) -> str:
        """Get the raw public key as base64."""
        public_key = self._private_key.public_key()
        raw = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return base64.b64encode(raw).decode("ascii")
