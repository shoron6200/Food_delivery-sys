"""Dependencies shared by the API routes."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User, UserRole

# Tells FastAPI (and the Swagger "Authorize" button) where tokens come from.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: DbSession
) -> User:
    """Find the logged-in user from the token in the request header."""
    user_id = decode_access_token(token)
    user = db.get(User, user_id) if user_id is not None else None
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: UserRole):
    """Build a dependency that lets in only logged-in users with one of these roles."""

    def check_role(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to do this",
            )
        return user

    return check_role


# Ready-made "only this role" dependencies for the routers.
Customer = Annotated[User, Depends(require_role(UserRole.customer))]
Vendor = Annotated[User, Depends(require_role(UserRole.vendor))]
Rider = Annotated[User, Depends(require_role(UserRole.rider))]
Admin = Annotated[User, Depends(require_role(UserRole.admin))]
