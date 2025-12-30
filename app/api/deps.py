from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from fastapi import Depends

def get_current_user(db: Session = Depends(get_db)):
    # HARD CODE USER ID = 1
    user = db.query(User).filter(User.id == 1).first()

    if not user:
        raise Exception("Hardcoded user not found")

    return user
