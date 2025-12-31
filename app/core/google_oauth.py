from authlib.integrations.starlette_client import OAuth
from app.core.config import settings
import time
from threading import Lock

# Simple in-memory state store untuk OAuth
oauth_state_store = {}
state_store_lock = Lock()

def save_oauth_state(state: str, data: dict):
    """Simpan OAuth state dengan expiry 10 menit"""
    with state_store_lock:
        oauth_state_store[state] = {
            'data': data,
            'exp': time.time() + 600  # 10 minutes
        }

def get_oauth_state(state: str):
    """Ambil OAuth state (tidak xóa - để có thể verify lagi)"""
    with state_store_lock:
        if state in oauth_state_store:
            item = oauth_state_store[state]
            # Check expiry
            if item['exp'] > time.time():
                return item['data']
            else:
                # Expired - xóa
                del oauth_state_store[state]
                return None
    return None

oauth = OAuth()

oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)
