import jwt
from fastapi import HTTPException, Header
from fastapi.security import HTTPBearer

from backend.config import JWT_SECRET

security = HTTPBearer(auto_error=False)


def get_current_user_id(authorization: str = Header(None)):
    """FastAPI dependency helper to extract user_id from JWT token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.split(" ", 1)[1] if authorization.lower().startswith("bearer ") else authorization
    
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return int(data["user_id"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired — please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")