"""
Tests for auth module.

Tests authentication, password hashing, JWT handling, and rate limiting.
"""

import time
from datetime import datetime, timedelta

import pytest

from auth.core import (
    AccountLockedError,
    AuthConfig,
    AuthManager,
    InvalidCredentialsError,
    JWTHandler,
    PasswordHasher,
    Session,
    TokenExpiredError,
    TokenInvalidError,
    TokenPayload,
    User,
    UserExistsError,
    UserRole,
)

# =============================================================================
# PASSWORD HASHER TESTS
# =============================================================================


class TestPasswordHasher:
    """Tests for bcrypt-based password hashing."""

    def test_hash_returns_bcrypt_format(self):
        """Hash should return bcrypt-formatted string."""
        hasher = PasswordHasher(rounds=4)  # Low rounds for speed
        password_hash, salt = hasher.hash("SecurePass123!")

        # bcrypt hashes start with $2a$, $2b$, or $2y$
        assert password_hash.startswith(("$2a$", "$2b$", "$2y$"))
        assert salt == ""  # bcrypt embeds salt in hash

    def test_verify_correct_password(self):
        """Should return True for correct password."""
        hasher = PasswordHasher(rounds=4)
        password = "MySecurePassword123!"
        password_hash, _ = hasher.hash(password)

        assert hasher.verify(password, password_hash) is True

    def test_verify_wrong_password(self):
        """Should return False for wrong password."""
        hasher = PasswordHasher(rounds=4)
        password_hash, _ = hasher.hash("CorrectPassword")

        assert hasher.verify("WrongPassword", password_hash) is False

    def test_verify_invalid_hash(self):
        """Should return False for invalid hash format."""
        hasher = PasswordHasher(rounds=4)

        assert hasher.verify("password", "invalid_hash") is False
        assert hasher.verify("password", "") is False

    def test_password_strength_valid(self):
        """Should validate strong password."""
        is_valid, issues = PasswordHasher.validate_strength("SecurePass123!")

        assert is_valid is True
        assert len(issues) == 0

    def test_password_strength_too_short(self):
        """Should reject short password."""
        is_valid, issues = PasswordHasher.validate_strength("Abc1!")

        assert is_valid is False
        assert any("karakter" in issue for issue in issues)

    def test_password_strength_no_uppercase(self):
        """Should reject password without uppercase."""
        is_valid, issues = PasswordHasher.validate_strength("securepass123!")

        assert is_valid is False
        assert any("büyük harf" in issue for issue in issues)

    def test_password_strength_no_special(self):
        """Should reject password without special chars."""
        is_valid, issues = PasswordHasher.validate_strength("SecurePass123")

        assert is_valid is False
        assert any("özel karakter" in issue for issue in issues)

    def test_needs_rehash_old_format(self):
        """Should detect non-bcrypt hashes."""
        hasher = PasswordHasher(rounds=12)

        # Old PBKDF2 style hash (base64)
        assert hasher.needs_rehash("aGFzaGVkX3Bhc3N3b3Jk") is True
        # Plain text
        assert hasher.needs_rehash("password") is True

    def test_needs_rehash_valid_bcrypt(self):
        """Should not require rehash for valid bcrypt."""
        hasher = PasswordHasher(rounds=10)
        password_hash, _ = hasher.hash("password")

        # Same or higher rounds should not need rehash
        assert hasher.needs_rehash(password_hash) is False


# =============================================================================
# JWT HANDLER TESTS
# =============================================================================


class TestJWTHandler:
    """Tests for PyJWT-based token handling."""

    def test_encode_decode_roundtrip(self):
        """Token encode/decode should preserve payload."""
        handler = JWTHandler("test-secret-key-32chars-minimum!")
        payload = {"sub": "user-123", "role": "admin", "exp": int(time.time()) + 3600}

        token = handler.encode(payload)
        decoded = handler.decode(token)

        assert decoded["sub"] == "user-123"
        assert decoded["role"] == "admin"

    def test_expired_token_raises(self):
        """Should raise TokenExpiredError for expired token."""
        handler = JWTHandler("test-secret-key")
        payload = {"sub": "user-123", "exp": int(time.time()) - 100}  # Expired

        token = handler.encode(payload)

        with pytest.raises(TokenExpiredError):
            handler.decode(token)

    def test_invalid_signature_raises(self):
        """Should raise TokenInvalidError for wrong secret."""
        handler1 = JWTHandler("secret-key-1")
        handler2 = JWTHandler("secret-key-2")

        payload = {"sub": "user", "exp": int(time.time()) + 3600}
        token = handler1.encode(payload)

        with pytest.raises(TokenInvalidError):
            handler2.decode(token)

    def test_malformed_token_raises(self):
        """Should raise TokenInvalidError for malformed token."""
        handler = JWTHandler("secret")

        with pytest.raises(TokenInvalidError):
            handler.decode("not.a.valid.token")

    def test_decode_without_verification(self):
        """Should decode without verification (for debugging)."""
        handler = JWTHandler("secret")
        payload = {"sub": "user-123", "exp": int(time.time()) - 100}
        token = handler.encode(payload)

        # Normal decode would fail (expired)
        with pytest.raises(TokenExpiredError):
            handler.decode(token)

        # But without verification works
        decoded = handler.decode_without_verification(token)
        assert decoded["sub"] == "user-123"


# =============================================================================
# AUTH MANAGER TESTS
# =============================================================================


class TestAuthManagerRegistration:
    """Tests for user registration."""

    def test_register_new_user(self):
        """Should register new user successfully."""
        auth = AuthManager()

        user = auth.register(
            email="test@example.com", username="testuser", password="SecurePass123!"
        )

        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password_hash.startswith("$2")  # bcrypt
        assert user.role == UserRole.USER

    def test_register_duplicate_email_raises(self):
        """Should raise UserExistsError for duplicate email."""
        auth = AuthManager()

        auth.register("test@example.com", "user1", "SecurePass123!")

        with pytest.raises(UserExistsError):
            auth.register("test@example.com", "user2", "SecurePass123!")

    def test_register_weak_password_raises(self):
        """Should reject weak passwords."""
        auth = AuthManager()

        with pytest.raises(Exception):  # AuthError
            auth.register("test@example.com", "user", "weak")


class TestAuthManagerLogin:
    """Tests for user login."""

    def test_login_success(self):
        """Should login with correct credentials."""
        auth = AuthManager()
        auth.register("test@example.com", "testuser", "SecurePass123!")

        session = auth.login("test@example.com", "SecurePass123!")

        assert session is not None
        assert session.access_token is not None
        assert session.refresh_token is not None
        assert session.user_id is not None

    def test_login_wrong_password_raises(self):
        """Should raise InvalidCredentialsError for wrong password."""
        auth = AuthManager()
        auth.register("test@example.com", "testuser", "SecurePass123!")

        with pytest.raises(InvalidCredentialsError):
            auth.login("test@example.com", "WrongPassword!")

    def test_login_nonexistent_user_raises(self):
        """Should raise InvalidCredentialsError for unknown email."""
        auth = AuthManager()

        with pytest.raises(InvalidCredentialsError):
            auth.login("unknown@example.com", "password")


class TestRateLimiting:
    """Tests for login rate limiting."""

    def test_account_locks_after_max_attempts(self):
        """Should lock account after max failed attempts."""
        config = AuthConfig(max_login_attempts=3, lockout_duration_minutes=1)
        auth = AuthManager(config=config)

        auth.register("test@example.com", "user", "SecurePass123!")

        # Fail 3 times
        for _ in range(3):
            try:
                auth.login("test@example.com", "WrongPassword!")
            except (InvalidCredentialsError, AccountLockedError):
                pass

        # 4th attempt should be locked
        with pytest.raises(AccountLockedError):
            auth.login("test@example.com", "SecurePass123!")  # Even correct password

    def test_successful_login_resets_attempts(self):
        """Should reset failed attempts on successful login."""
        config = AuthConfig(max_login_attempts=5)
        auth = AuthManager(config=config)

        auth.register("test@example.com", "user", "SecurePass123!")

        # Fail twice
        for _ in range(2):
            try:
                auth.login("test@example.com", "Wrong!")
            except InvalidCredentialsError:
                pass

        # Successful login
        session = auth.login("test@example.com", "SecurePass123!")
        assert session is not None

        # Should be able to fail 5 more times (counter reset)
        for _ in range(4):
            try:
                auth.login("test@example.com", "Wrong!")
            except InvalidCredentialsError:
                pass

        # Still not locked (only 4 fails after reset)
        session = auth.login("test@example.com", "SecurePass123!")
        assert session is not None


class TestTokenVerification:
    """Tests for token verification."""

    def test_verify_valid_token(self):
        """Should verify valid access token."""
        auth = AuthManager()
        auth.register("test@example.com", "user", "SecurePass123!")
        session = auth.login("test@example.com", "SecurePass123!")

        payload = auth.verify_token(session.access_token)

        assert payload is not None
        assert payload.sub is not None
        assert payload.type == "access"

    def test_verify_refresh_token(self):
        """Should verify valid refresh token."""
        auth = AuthManager()
        auth.register("test@example.com", "user", "SecurePass123!")
        session = auth.login("test@example.com", "SecurePass123!")

        # Refresh token should be decodable
        payload = auth.jwt.decode(session.refresh_token)

        assert payload is not None
        assert payload.get("type") == "refresh"


class TestSessionManagement:
    """Tests for session management."""

    def test_logout_invalidates_session(self):
        """Should invalidate session on logout."""
        auth = AuthManager()
        auth.register("test@example.com", "user", "SecurePass123!")
        session = auth.login("test@example.com", "SecurePass123!")

        result = auth.logout(session.id)

        assert result is True

    def test_logout_all_sessions(self):
        """Should invalidate all sessions for user."""
        auth = AuthManager()
        user = auth.register("test@example.com", "user", "SecurePass123!")

        # Create multiple sessions
        auth.login("test@example.com", "SecurePass123!")
        auth.login("test@example.com", "SecurePass123!")
        auth.login("test@example.com", "SecurePass123!")

        count = auth.logout_all(user.id)

        assert count == 3


# =============================================================================
# USER MODEL TESTS
# =============================================================================


class TestUserModel:
    """Tests for User dataclass."""

    def test_user_to_dict(self):
        """Should serialize user to dict."""
        user = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            password_hash="$2b$12$hash",
            salt="",
        )

        data = user.to_dict()

        assert data["id"] == "user-123"
        assert data["email"] == "test@example.com"
        assert "password_hash" not in data  # Sensitive data excluded

    def test_user_from_dict(self):
        """Should deserialize user from dict."""
        data = {
            "id": "user-123",
            "email": "test@example.com",
            "username": "testuser",
            "password_hash": "$2b$12$hash",
            "salt": "",
            "created_at": "2025-01-01T00:00:00",
        }

        user = User.from_dict(data)

        assert user.id == "user-123"
        assert user.email == "test@example.com"

    def test_user_is_locked(self):
        """Should detect locked status."""
        user = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            password_hash="hash",
            salt="",
            locked_until=datetime.utcnow() + timedelta(minutes=10),
        )

        assert user.is_locked is True

    def test_user_is_not_locked(self):
        """Should detect unlocked status."""
        user = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            password_hash="hash",
            salt="",
            locked_until=None,
        )

        assert user.is_locked is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
