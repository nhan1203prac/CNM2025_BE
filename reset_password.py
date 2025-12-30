from app.db.session import SessionLocal
from app.models.user import User
from app.models.profile import Profile
from app.core.security import get_password_hash

# 1. Kết nối Database
db = SessionLocal()

def reset_admin_password():
    email_to_reset = "user@example.com"
    new_password = "123456"
    
    try:
        # 2. Tìm user
        user = db.query(User).filter(User.email == email_to_reset).first()
        
        if user:
            # 3. Cập nhật mật khẩu mới (được hash bằng code hiện tại)
            hashed_pw = get_password_hash(new_password)
            user.password = hashed_pw
            
            # Đảm bảo tài khoản đang active và là admin
            user.is_active = True 
            user.isAdmin = True
            
            db.commit()
            print(f"✅ Đã reset mật khẩu cho {email_to_reset}")
            print(f"👉 Mật khẩu mới: {new_password}")
            print(f"👉 Hash mới trong DB: {hashed_pw}")
        else:
            print(f"❌ Không tìm thấy user có email: {email_to_reset}")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin_password()