"""JWT authentication via Supabase JWKS endpoint."""

from fastapi import Depends, HTTPException, Request, status

try:
    import jwt
    from jwt import PyJWKClient
except ImportError:
    raise ImportError(
        "PyJWT and cryptography are required for authentication. "
        "Install them with: pip install PyJWT cryptography"
    )

from app.config import get_settings

settings = get_settings()

# JWKS client caches signing keys internally; lifespan_interval refreshes every 5 min
_jwks_client: PyJWKClient | None = None


def get_jwks_client() -> PyJWKClient:
    """Return a cached JWKS client instance."""
    global _jwks_client
    if _jwks_client is None:
        jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url, lifespan=300)
    return _jwks_client


async def get_current_user(request: Request) -> str | None:
    """FastAPI dependency: extract and verify JWT from Authorization header.

    Returns the user_id (sub claim) if a valid token is present,
    None if no Authorization header is provided,
    or raises 401 if the token is invalid.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    # Expect "Bearer <token>"
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'.",
        )

    token = parts[1]

    try:
        jwks_client = get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "HS256"],
            audience="authenticated",
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing 'sub' claim.",
            )
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


async def require_auth(user_id: str | None = Depends(get_current_user)) -> str:
    """FastAPI dependency: require a valid authenticated user.

    Raises 401 if no user is authenticated.
    """
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return user_id
