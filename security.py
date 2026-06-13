from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "30543bd93ab0934a339278d8f7f5b7db0005e21b41378f00e43b096d1dd0905b"
ALGORITHM = "HS256"

def create_access_token(data: dict):

    payload = data.copy()

    payload["exp"] = datetime.utcnow() + timedelta(hours=24)

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(
    plain_password: str,
    hashed_password: str
):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )