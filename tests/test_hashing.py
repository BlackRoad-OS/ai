"""Tests for the hashing utilities module."""

from utils.hashing import sha256_hash, sha_infinity_hash, ContentVerifier


def test_sha256_hash_returns_string():
    """Test that sha256_hash returns a string."""
    result = sha256_hash("test content")
    assert isinstance(result, str)
    assert len(result) == 64  # SHA-256 hex digest is 64 chars


def test_sha256_hash_deterministic():
    """Test that same input produces same hash."""
    content = "hello world"
    assert sha256_hash(content) == sha256_hash(content)


def test_sha256_hash_different_inputs():
    """Test that different inputs produce different hashes."""
    assert sha256_hash("content a") != sha256_hash("content b")


def test_sha_infinity_hash_returns_string():
    """Test that sha_infinity_hash returns a string."""
    result = sha_infinity_hash("test content", include_timestamp=False)
    assert isinstance(result, str)
    assert len(result) > 0


def test_sha_infinity_hash_deterministic_without_timestamp():
    """Test that sha_infinity_hash without timestamp is deterministic."""
    content = "hello world"
    h1 = sha_infinity_hash(content, include_timestamp=False)
    h2 = sha_infinity_hash(content, include_timestamp=False)
    assert h1 == h2


def test_content_verifier_sha256():
    """Test ContentVerifier SHA-256 verification."""
    content = "verify me"
    hash_value = sha256_hash(content)
    assert ContentVerifier.verify_sha256(content, hash_value) is True
    assert ContentVerifier.verify_sha256(content, "wronghash") is False
