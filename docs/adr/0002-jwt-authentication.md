# JWT-Based Authentication

* Status: Accepted
* Deciders: FinPilot Development Team
* Date: 2025-01-15

## Context

The application needed a secure authentication mechanism for its API endpoints. Requirements:

1. **Stateless**: No server-side session storage required
2. **Scalable**: Must work across multiple server instances
3. **Secure**: Must prevent common attacks (replay, CSRF, XSS)
4. **Performant**: Minimal overhead per request
5. **Standard**: Use well-established protocols

## Decision

Implement JWT (JSON Web Token) based authentication using PyJWT with bcrypt password hashing:

### Token Structure

```
Header.Payload.Signature
```

- **Access Token**: Short-lived (15 minutes), used for API access
- **Refresh Token**: Longer-lived (7 days), used to obtain new access tokens

### Security Measures

1. **HS256 Signing**: HMAC-SHA256 with secret key from environment
2. **bcrypt Hashing**: Cost factor 12 for password storage
3. **Token Rotation**: Refresh tokens rotated on use
4. **Rate Limiting**: 5 failed attempts trigger 15-minute lockout

### Implementation

```python
from core.auth import JWTAuth, hash_password, verify_password

# Password hashing
hashed = hash_password(raw_password)
if verify_password(raw_password, hashed):
    token = JWTAuth.create_token(user_id)
```

## Consequences

### Positive

* **Stateless**: No session database needed
* **Scalable**: Works in distributed deployments
* **Self-Contained**: User info in token, no DB lookup per request
* **Standard**: Wide library support, well-understood
* **Cross-Domain**: Works with mobile apps, SPAs

### Negative

* **Token Size**: JWTs are larger than session IDs (~300 bytes)
* **Revocation Complexity**: Cannot immediately revoke tokens (mitigated by short expiry)
* **Secret Management**: Secret key must be securely managed

### Neutral

* Adds ~5ms overhead per request for validation
* Requires HTTPS for transport security

## Alternatives Considered

### Option 1: Session-Based Authentication

Server stores session in memory/Redis.

**Pros:**
* Immediate revocation
* Simple implementation
* Smaller cookies

**Cons:**
* Requires session store
* Scaling complexity
* CSRF vulnerabilities

**Verdict**: Rejected due to scaling requirements

### Option 2: OAuth 2.0

Full OAuth implementation with authorization server.

**Pros:**
* Industry standard
* Third-party login support
* Fine-grained scopes

**Cons:**
* Complex implementation
* Overkill for internal API
* Requires separate auth server

**Verdict**: Rejected as unnecessarily complex for current needs

### Option 3: API Keys

Static API keys per user.

**Pros:**
* Simple
* No expiration management
* Easy to implement

**Cons:**
* No expiration (unless manual)
* Hard to rotate
* No user context

**Verdict**: Rejected due to security limitations

## Security Considerations

### Token Storage (Client)
- Access Token: Memory only (never localStorage)
- Refresh Token: httpOnly cookie

### Token Validation
```python
def validate_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=['HS256']
        )
        if payload['exp'] < time.time():
            raise AuthenticationError("Token expired")
        return payload
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(str(e))
```

### Brute Force Protection
- Failed attempts tracked per IP
- Exponential backoff on failures
- Account lockout after 5 failures

## References

* [RFC 7519: JSON Web Token (JWT)](https://datatracker.ietf.org/doc/html/rfc7519)
* [OWASP JWT Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_Cheat_Sheet_for_Java.html)
* [bcrypt Password Hashing](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
* [ADR-0001: Pickle to JSON Migration](0001-pickle-to-json.md)
