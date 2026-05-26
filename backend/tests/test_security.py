"""
test_security.py — Unit tests for src/core/security.py

Coverage targets:
  ✓ get_password_hash() produces bcrypt hashes
  ✓ verify_password() returns True for correct password, False for wrong
  ✓ create_access_token() returns a valid JWT string
  ✓ JWT payload contains 'sub', 'role', and 'exp' fields
  ✓ Token expiry is honoured (timedelta override)
  ✓ get_current_user_token() decodes a valid token into TokenData
  ✓ get_current_user_token() raises 401 for tampered tokens
  ✓ get_current_user_token() raises 401 for expired tokens
  ✓ RoleChecker allows access for matching role
  ✓ RoleChecker allows National Coordinator to bypass role restriction
  ✓ RoleChecker raises 403 for mismatched role
"""

import pytest
from datetime import timedelta
from jose import jwt

from src.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user_token,
    RoleChecker,
    TokenData,
    ROLE_NATIONAL_COORDINATOR,
    ROLE_COUNTY_VETERINARIAN,
)
from src.core.config import settings
from fastapi import HTTPException


# ── Password Hashing ──────────────────────────────────────────────────────────

class TestPasswordHashing:
    def test_hash_is_different_from_plaintext(self):
        hashed = get_password_hash("secure_password")
        assert hashed != "secure_password"

    def test_hash_starts_with_bcrypt_prefix(self):
        hashed = get_password_hash("test")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_verify_correct_password_returns_true(self):
        hashed = get_password_hash("my_password")
        assert verify_password("my_password", hashed) is True

    def test_verify_wrong_password_returns_false(self):
        hashed = get_password_hash("my_password")
        assert verify_password("wrong_password", hashed) is False

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt salts should ensure uniqueness."""
        h1 = get_password_hash("same")
        h2 = get_password_hash("same")
        assert h1 != h2


# ── JWT Token Creation ────────────────────────────────────────────────────────

class TestCreateAccessToken:
    def test_returns_string(self):
        token = create_access_token({"sub": "user@test.com", "role": "viewer"})
        assert isinstance(token, str)

    def test_token_has_three_segments(self):
        token = create_access_token({"sub": "user@test.com"})
        assert len(token.split(".")) == 3

    def test_token_contains_sub(self):
        token = create_access_token({"sub": "alice", "role": ROLE_COUNTY_VETERINARIAN})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "alice"

    def test_token_contains_role(self):
        token = create_access_token({"sub": "alice", "role": ROLE_COUNTY_VETERINARIAN})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["role"] == ROLE_COUNTY_VETERINARIAN

    def test_token_contains_exp(self):
        token = create_access_token({"sub": "alice"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in payload

    def test_custom_expiry_respected(self):
        """Token created with 1-minute expiry should have exp ~60 sec ahead."""
        import time
        token = create_access_token({"sub": "x"}, expires_delta=timedelta(minutes=1))
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        remaining = payload["exp"] - int(time.time())
        assert 30 < remaining <= 60


# ── Token Decoding ────────────────────────────────────────────────────────────

class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_valid_token_returns_token_data(self):
        token = create_access_token({"sub": "nurse_01", "role": ROLE_COUNTY_VETERINARIAN})
        result = await get_current_user_token(token=token)
        assert isinstance(result, TokenData)
        assert result.username == "nurse_01"
        assert result.role == ROLE_COUNTY_VETERINARIAN

    @pytest.mark.asyncio
    async def test_tampered_token_raises_401(self):
        token = create_access_token({"sub": "legit_user"})
        tampered = token[:-4] + "XXXX"
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_token(token=tampered)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_token_raises_401(self):
        token = create_access_token({"sub": "user"}, expires_delta=timedelta(seconds=-1))
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_token(token=token)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_token_without_sub_raises_401(self):
        """A token missing 'sub' is invalid per RBAC contract."""
        from datetime import datetime, timezone
        payload = {"role": "viewer", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_token(token=token)
        assert exc_info.value.status_code == 401


# ── Role-Based Access Control ─────────────────────────────────────────────────

class TestRoleChecker:
    """Tests for the injectable RoleChecker dependency class."""

    def _make_user(self, role: str) -> TokenData:
        return TokenData(username="test_user", role=role)

    def test_matching_role_returns_user(self):
        checker = RoleChecker([ROLE_COUNTY_VETERINARIAN])
        user = self._make_user(ROLE_COUNTY_VETERINARIAN)
        result = checker(current_user=user)
        assert result.username == "test_user"

    def test_national_coordinator_bypasses_restriction(self):
        """National Coordinator must have global access to any role-gated endpoint."""
        checker = RoleChecker([ROLE_COUNTY_VETERINARIAN])
        coordinator = self._make_user(ROLE_NATIONAL_COORDINATOR)
        result = checker(current_user=coordinator)
        assert result.username == "test_user"

    def test_wrong_role_raises_403(self):
        checker = RoleChecker([ROLE_NATIONAL_COORDINATOR])
        vet = self._make_user(ROLE_COUNTY_VETERINARIAN)
        with pytest.raises(HTTPException) as exc_info:
            checker(current_user=vet)
        assert exc_info.value.status_code == 403

    def test_unknown_role_raises_403(self):
        checker = RoleChecker([ROLE_NATIONAL_COORDINATOR])
        guest = self._make_user("guest")
        with pytest.raises(HTTPException) as exc_info:
            checker(current_user=guest)
        assert exc_info.value.status_code == 403

    def test_multi_role_list_allows_any_matching_role(self):
        """RoleChecker with multiple allowed roles should accept any matching one."""
        checker = RoleChecker([ROLE_COUNTY_VETERINARIAN, "County Clinician"])
        clinician = self._make_user("County Clinician")
        result = checker(current_user=clinician)
        assert result.username == "test_user"

    def test_403_message_includes_required_roles(self):
        """Error message must list the required roles for debugging."""
        checker = RoleChecker([ROLE_NATIONAL_COORDINATOR])
        vet = self._make_user(ROLE_COUNTY_VETERINARIAN)
        with pytest.raises(HTTPException) as exc_info:
            checker(current_user=vet)
        assert ROLE_NATIONAL_COORDINATOR in str(exc_info.value.detail)
