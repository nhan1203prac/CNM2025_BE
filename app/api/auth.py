from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import secrets

from app.db.session import get_db
from app.models.user import User
from app.models.profile import Profile
from app.schemas.userDto import (
    ProfileResponse,
    ProfileUpdate,
    UserCreate,
    UserLogin,
    Token,
    VerifyCodeRequest,
    ResendVerificationRequest,
    UserResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.email_utils import generate_verification_code, send_verification_email, send_password_reset_email
from app.core.validators import validate_email, validate_password, validate_username
from app.core.dependencies import get_current_user
from app.core.google_oauth import oauth, save_oauth_state, get_oauth_state

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Constants
VERIFICATION_CODE_EXPIRY_MINUTES = 15
MAX_VERIFICATION_ATTEMPTS = 3

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Đăng ký tài khoản mới"""
    try:
        # Validate input
        validate_username(user_in.username)
        validate_email(user_in.email)
        validate_password(user_in.password)
        
        # Kiểm tra user đã tồn tại
        user_exists = db.query(User).filter(
            (User.email == user_in.email) | (User.username == user_in.username)
        ).first()
        
        if user_exists:
            logger.warning(f"Register attempt with existing email/username: {user_in.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username hoặc Email đã tồn tại"
            )

        # Tạo mã xác thực
        verification_code = generate_verification_code()

        # Tạo profile và user
        new_profile = Profile(full_name=user_in.full_name)
        db.add(new_profile)
        db.flush()

        new_user = User(
            username=user_in.username,
            email=user_in.email,
            password=hash_password(user_in.password),
            profile_id=new_profile.id,
            is_active=False,
            verification_code=verification_code
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        db.refresh(new_profile)

        # Gửi email xác thực (async sẽ tốt hơn)
        email_sent = send_verification_email(new_user.email, verification_code)
        if not email_sent:
            logger.error(f"Failed to send verification email to {new_user.email}")

        logger.info(f"New user registered: {new_user.email}")

        token = create_access_token(subject=new_user.email)

        return Token(
            access_token=token,
            token_type="bearer",
            isActive=new_user.is_active,
            user=UserResponse.model_validate(new_user)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống, vui lòng thử lại"
        )

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """Đăng nhập - chỉ cho phép user đã xác minh email"""
    try:
        from sqlalchemy.orm import joinedload
        user = db.query(User).options(joinedload(User.profile)).filter(User.email == user_in.email).first()
        
        if not user:
            logger.warning(f"Login attempt with non-existent email: {user_in.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email hoặc mật khẩu không đúng"
            )
        
        if not verify_password(user_in.password, user.password):
            logger.warning(f"Failed login attempt for user: {user_in.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email hoặc mật khẩu không đúng"
            )

        # Kiểm tra email đã xác minh chưa
        if not user.is_active:
            logger.warning(f"Login attempt with unverified email: {user_in.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vui lòng xác minh email trước khi đăng nhập"
            )

        # Update last login time (optional)
        user.last_login = datetime.utcnow()
        db.commit()

        token = create_access_token(subject=user.email)
        logger.info(f"User logged in: {user.email}")

        return Token(
            access_token=token,
            token_type="bearer",
            isActive=user.is_active,
            user=UserResponse.model_validate(user)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống"
        )

@router.post("/verify-email")
def verify_email(payload: VerifyCodeRequest, db: Session = Depends(get_db)):
    """Xác minh email bằng mã được gửi"""
    try:
        user = db.query(User).filter(User.verification_code == payload.verification_code).first()

        if not user:
            logger.warning("Invalid verification code attempt")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã xác minh không hợp lệ"
            )

        # Lưu ý: Mã xác minh sẽ không hết hạn (cần database migration để thêm timestamp)

        # User đã verify trước đó
        if user.is_active:
            logger.info(f"User {user.email} attempted to re-verify")
            return {"message": "Email đã được xác minh trước đó."}

        # Cập nhật user
        user.is_active = True
        user.verification_code = None
        db.commit()
        db.refresh(user)
        
        logger.info(f"Email verified for user: {user.email}")
        return {"message": "Xác minh email thành công"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Email verification error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống"
        )

@router.post("/send-verification")
def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    """Gửi lại mã xác minh"""
    try:
        user = db.query(User).filter(User.email == payload.email).first()
        
        if not user:
            logger.warning(f"Resend verification for non-existent email: {payload.email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email không tồn tại"
            )
        
        if user.is_active:
            logger.info(f"Resend verification for already verified user: {payload.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tài khoản đã được xác minh"
            )
        
        # Kiểm tra số lần gửi lại (ngăn spam)
        if user.verification_attempts and user.verification_attempts >= MAX_VERIFICATION_ATTEMPTS:
            logger.warning(f"Max verification attempts exceeded: {payload.email}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Bạn đã yêu cầu mã quá nhiều lần, vui lòng thử lại sau"
            )
        
        # Tạo mã mới
        verification_code = generate_verification_code()
        user.verification_code = verification_code
        user.verification_attempts = (user.verification_attempts or 0) + 1
        
        db.commit()
        db.refresh(user)
        
        # Gửi email
        email_sent = send_verification_email(user.email, verification_code)
        if not email_sent:
            logger.error(f"Failed to resend verification email to {user.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể gửi email, vui lòng thử lại"
            )
        
        logger.info(f"Verification email resent to: {user.email}")
        return {"message": "Đã gửi lại mã xác thực"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Resend verification error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống"
        )


@router.post("/forgot-password")
def forgot_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    """Yêu cầu đặt lại mật khẩu, gửi token qua email"""
    try:
        user = db.query(User).filter(User.email == payload.email).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email không tồn tại"
            )

        reset_token = secrets.token_urlsafe(32)
        user.password_reset_token = reset_token
        db.commit()

        email_sent = send_password_reset_email(user.email, reset_token)
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể gửi email đặt lại mật khẩu"
            )

        logger.info(f"Password reset token generated for {user.email}")
        return {"message": "Đã gửi token đặt lại mật khẩu qua email"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Forgot password error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống"
        )


@router.post("/reset-password")
def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Đặt lại mật khẩu bằng token"""
    try:
        user = db.query(User).filter(User.password_reset_token == payload.token).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token không hợp lệ"
            )

        validate_password(payload.new_password)
        user.password = hash_password(payload.new_password)
        user.password_reset_token = None
        db.commit()

        logger.info(f"Password reset for {user.email}")
        return {"message": "Đặt lại mật khẩu thành công"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Reset password error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống"
        )

@router.get("/users/me", response_model=ProfileResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user.profile

@router.put("/users/profile", response_model=ProfileResponse)
def update_profile(profile_in: ProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Cập nhật thông tin profile của user hiện tại"""
    try:
        profile = current_user.profile
        
        # Chỉ update các field được gửi lên (không None)
        if profile_in.full_name is not None:
            profile.full_name = profile_in.full_name
        if profile_in.avatar is not None:
            profile.avatar = profile_in.avatar
        if profile_in.phone is not None:
            profile.phone = profile_in.phone
        if profile_in.gender is not None:
            profile.gender = profile_in.gender
        if profile_in.dob is not None:
            profile.dob = profile_in.dob
        
        db.commit()
        db.refresh(profile)
        
        logger.info(f"Profile updated for user: {current_user.email}")
        return profile
    
    except Exception as e:
        db.rollback()
        logger.error(f"Profile update error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống"
        )

@router.get("/google/login")
async def google_login(request: Request):
    """Redirect đến trang đăng nhập Google"""
    from app.core.config import settings
    import secrets
    try:
        # Generate state và lưu vào in-memory store
        state = secrets.token_urlsafe(32)
        save_oauth_state(state, {'redirect_uri': settings.GOOGLE_REDIRECT_URI})
        
        # Pass state qua URL, thêm prompt để buộc chọn tài khoản
        url = await oauth.google.authorize_redirect(
            request, 
            settings.GOOGLE_REDIRECT_URI, 
            state=state,
            prompt="select_account"  # Buộc chọn tài khoản mỗi lần
        )
        return url
    except Exception as e:
        logger.error(f"Google login error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Lỗi đăng nhập Google")

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Xử lý callback từ Google sau khi user đăng nhập"""
    try:
        import httpx
        from app.core.config import settings
        
        # Verify state từ in-memory store
        state = request.query_params.get('state')
        code = request.query_params.get('code')
        
        if not state or not code:
            raise HTTPException(status_code=400, detail="Missing state or code")
        
        if not get_oauth_state(state):
            raise HTTPException(status_code=400, detail="Invalid or expired state")
        
        # Manually exchange code for token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            if token_response.status_code != 200:
                logger.error(f"Token exchange failed: {token_response.text}")
                raise HTTPException(status_code=400, detail="Failed to get token from Google")
            
            token = token_response.json()
        
        # Lấy user info từ token (JWT)
        import jwt as pyjwt
        id_token = token.get('id_token')
        user_info = pyjwt.decode(id_token, options={"verify_signature": False})
        
        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0])
        google_id = user_info.get('sub')
        avatar = user_info.get('picture')
        
        # Kiểm tra user đã tồn tại chưa
        from sqlalchemy.orm import joinedload
        user = db.query(User).options(joinedload(User.profile)).filter(User.email == email).first()
        
        if user:
            # User đã tồn tại - update thông tin nếu cần
            if not user.is_active:
                user.is_active = True
                db.commit()
        else:
            # Tạo user mới
            new_profile = Profile(
                full_name=name,
                avatar=avatar
            )
            db.add(new_profile)
            db.flush()
            
            # Tạo username từ email (hoặc google_id)
            username = email.split('@')[0] + '_' + google_id[:8]
            
            user = User(
                username=username,
                email=email,
                password=hash_password(google_id),  # Password random từ google_id
                profile_id=new_profile.id,
                is_active=True,  # Google OAuth tự động verify
                verification_code=None
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Tạo JWT token cho hệ thống
        access_token = create_access_token(subject=user.email)
        
        # Return token response thay vì redirect
        return Token(
            access_token=access_token,
            token_type="bearer",
            isActive=user.is_active,
            user=UserResponse.model_validate(user)
        )
        
    except Exception as e:
        logger.error(f"Google OAuth error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi đăng nhập Google"
        )

