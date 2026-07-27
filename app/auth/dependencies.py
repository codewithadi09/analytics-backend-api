"""
FastAPI dependencies for authentication.

Import get_current_user into any route that should require a valid
JWT -- e.g.:

    @router.get("/dashboard/kpis")
    async def get_kpis(current_user: CurrentUser = Depends(get_current_user)):
        ...
"""

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.auth.jwt import TokenRevokedError, verify_access_token
from app.schemas.auth import CurrentUser

logger = logging.getLogger(__name__)

# auto_error=True means FastAPI itself returns 401 if the header is
# missing entirely, before our code even runs -- one less case to
# handle manually.
_bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> CurrentUser:
    """
    Resolves the authenticated user from the request's bearer token.

    Raises 401 for any failure mode (invalid signature, expired,
    revoked) -- deliberately the same status/message for all of
    them, so a caller probing the API can't distinguish "expired"
    from "revoked" from "tampered" and infer internal state.
    """
    token = credentials.credentials

    try:
        payload = await verify_access_token(token)
    except TokenRevokedError:
        logger.info("Rejected revoked token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid or expired token", "code": "TOKEN_INVALID"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        logger.info("Rejected invalid/expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid or expired token", "code": "TOKEN_INVALID"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(email=payload.sub, user_id=payload.sub)