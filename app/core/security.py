import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from jose import jwt
from passlib.context import CryptContext

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password) #return về string

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password) #trả về kiểu bool

def create_access_token(subject):
    expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM) #trả về string là token


#Nếu token hợp lệ và chưa hết hạn, trả về payload
#Nếu token hết hạn hoặc không hợp lệ, nó raise exception (JWTError, ExpiredSignatureError…)
def decode_access_token(token):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def is_token_expired(token):
    try:
        payload = decode_access_token(token)
        exp = payload.get("exp")
        return datetime.utcnow().timestamp() > exp #Kiểm tra còn hạn không, trả về bool
    except:
        return True
