from datetime import datetime, timedelta, timezone
from core.auth.config import SECRET_KEY, ALGORITHM
import jwt


def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=60)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
