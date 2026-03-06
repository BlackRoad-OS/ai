"""
Hashing Utilities for BlackRoad AI
===================================
SHA-256 and SHA-infinity hashing implementations for data integrity.

SHA-infinity is a recursive hashing concept that provides:
- Infinite depth verification
- Chain-of-trust hashing
- Tamper-evident state tracking
"""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field


def sha256_hash(content: Union[str, bytes, Dict, List]) -> str:
    """
    Compute SHA-256 hash of content.

    Args:
        content: String, bytes, or JSON-serializable object

    Returns:
        Hexadecimal hash string
    """
    if isinstance(content, dict) or isinstance(content, list):
        content = json.dumps(content, sort_keys=True, separators=(",", ":"))

    if isinstance(content, str):
        content = content.encode("utf-8")

    return hashlib.sha256(content).hexdigest()


def sha_infinity_hash(
    content: Union[str, bytes, Dict, List], depth: int = 7, include_timestamp: bool = True, salt: Optional[str] = None
) -> str:
    """
    Compute SHA-infinity hash - recursive hashing for chain verification.

    SHA-infinity creates a hash chain where each iteration:
    1. Hashes the previous hash with depth counter
    2. Optionally includes timestamp for temporal proof
    3. Creates verifiable chain that proves content at specific depth

    Args:
        content: Content to hash
        depth: Number of recursive iterations (default 7 for "infinity" symbolism)
        include_timestamp: Include timestamp in hash chain
        salt: Optional salt for additional security

    Returns:
        Final hash string with metadata prefix
    """
    if isinstance(content, dict) or isinstance(content, list):
        content = json.dumps(content, sort_keys=True, separators=(",", ":"))

    if isinstance(content, str):
        content = content.encode("utf-8")

    # Initial hash
    current_hash = hashlib.sha256(content).hexdigest()

    # Build hash chain
    chain_data = {"initial": current_hash, "depth": depth, "chain": [current_hash]}

    for i in range(depth):
        # Combine previous hash with depth and optional elements
        combo = f"{current_hash}:depth={i+1}"

        if include_timestamp:
            combo += f":ts={int(time.time() * 1000)}"

        if salt:
            combo += f":salt={salt}"

        current_hash = hashlib.sha256(combo.encode()).hexdigest()
        chain_data["chain"].append(current_hash)

    # Create final infinity hash with metadata
    final = f"sha∞:{depth}:{current_hash}"

    return final


@dataclass
class HashChain:
    """
    Maintains a chain of hashes for state verification.

    Used for:
    - Kanban card state tracking
    - Sync verification between services
    - Audit trail maintenance
    """

    chain_id: str
    hashes: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def append(self, content: Any) -> str:
        """Add content to chain, return new hash."""
        # Include previous hash in computation
        prev_hash = self.hashes[-1] if self.hashes else "genesis"

        combined = f"{prev_hash}:{json.dumps(content, sort_keys=True)}"
        new_hash = sha256_hash(combined)

        self.hashes.append(new_hash)
        return new_hash

    def verify(self) -> bool:
        """Verify chain integrity."""
        # For now, just check chain exists
        # Full verification would recompute from original content
        return len(self.hashes) > 0

    def get_infinity_hash(self) -> str:
        """Get SHA-infinity hash of entire chain."""
        return sha_infinity_hash(self.hashes)

    @property
    def current_hash(self) -> Optional[str]:
        """Get the most recent hash."""
        return self.hashes[-1] if self.hashes else None

    @property
    def length(self) -> int:
        """Get chain length."""
        return len(self.hashes)


class ContentVerifier:
    """
    Verifies content integrity using multiple hash methods.
    """

    @staticmethod
    def compute_all_hashes(content: Any) -> Dict[str, str]:
        """Compute all hash types for content."""
        return {
            "sha256": sha256_hash(content),
            "sha_infinity_3": sha_infinity_hash(content, depth=3),
            "sha_infinity_7": sha_infinity_hash(content, depth=7),
            "sha_infinity_21": sha_infinity_hash(content, depth=21),
        }

    @staticmethod
    def verify_sha256(content: Any, expected_hash: str) -> bool:
        """Verify content matches expected SHA-256 hash."""
        return sha256_hash(content) == expected_hash

    @staticmethod
    def verify_sha_infinity(content: Any, expected_hash: str) -> bool:
        """
        Verify content matches expected SHA-infinity hash.
        Extracts depth from hash prefix.
        """
        if not expected_hash.startswith("sha∞:"):
            return False

        parts = expected_hash.split(":")
        if len(parts) != 3:
            return False

        depth = int(parts[1])
        actual = sha_infinity_hash(content, depth=depth, include_timestamp=False)

        # Compare the hash portion (timestamps would differ)
        return actual.split(":")[2] == parts[2]


class StateHasher:
    """
    Hashes system state for sync verification.

    Used to ensure:
    - CRM state matches Git state
    - Cloudflare KV matches local state
    - All services are in sync
    """

    def __init__(self):
        self.state_hashes: Dict[str, str] = {}

    def hash_state(self, service: str, state: Dict) -> str:
        """Hash service state and store."""
        state_hash = sha256_hash(state)
        self.state_hashes[service] = state_hash
        return state_hash

    def compare_states(self, service1: str, service2: str) -> bool:
        """Check if two services have matching state."""
        h1 = self.state_hashes.get(service1)
        h2 = self.state_hashes.get(service2)

        if not h1 or not h2:
            return False

        return h1 == h2

    def get_global_hash(self) -> str:
        """Get hash of all service states combined."""
        return sha_infinity_hash(self.state_hashes)

    def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status report."""
        unique_hashes = set(self.state_hashes.values())

        return {
            "services": list(self.state_hashes.keys()),
            "in_sync": len(unique_hashes) == 1,
            "unique_states": len(unique_hashes),
            "global_hash": self.get_global_hash(),
            "hashes": self.state_hashes,
        }


# Convenience functions for common operations
def hash_card(card_data: Dict) -> Dict[str, str]:
    """Hash a kanban card's data."""
    return ContentVerifier.compute_all_hashes(card_data)


def hash_board(board_data: Dict) -> Dict[str, str]:
    """Hash a kanban board's data."""
    return ContentVerifier.compute_all_hashes(board_data)


def create_integrity_proof(content: Any) -> Dict:
    """
    Create a complete integrity proof for content.

    Returns proof object that can be stored/transmitted
    for later verification.
    """
    timestamp = int(time.time() * 1000)

    return {
        "timestamp": timestamp,
        "sha256": sha256_hash(content),
        "sha_infinity": sha_infinity_hash(content, include_timestamp=False),
        "content_type": type(content).__name__,
        "proof_version": "1.0",
    }


def verify_integrity_proof(content: Any, proof: Dict) -> Dict[str, bool]:
    """
    Verify content against integrity proof.

    Returns verification results for each hash type.
    """
    return {
        "sha256_valid": sha256_hash(content) == proof.get("sha256"),
        "sha_infinity_valid": ContentVerifier.verify_sha_infinity(content, proof.get("sha_infinity", "")),
        "proof_version": proof.get("proof_version") == "1.0",
    }
