import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

def generate_verification_code(length: int = 6) -> str:
    """Tạo mã xác thực ngẫu nhiên gồm số và chữ"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def send_verification_email(email: str, code: str) -> bool:
    """Gửi email chứa mã xác thực"""
    try:
        # Tạo email
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USER
        msg['To'] = email
        msg['Subject'] = 'Xác thực tài khoản - Mã xác nhận'
        
        # Nội dung email
        body = f"""
        <html>
            <body>
                <h2>Chào mừng bạn đến với hệ thống!</h2>
                <p>Mã xác thực của bạn là:</p>
                <h1 style="color: #4CAF50; font-size: 32px; letter-spacing: 5px;">{code}</h1>
                <p>Mã này có hiệu lực trong 15 phút.</p>
                <p>Nếu bạn không yêu cầu mã này, vui lòng bỏ qua email.</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Kết nối và gửi
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Lỗi gửi email: {e}")
        return False


def send_password_reset_email(email: str, token: str) -> bool:
    """Gửi email chứa link/token đặt lại mật khẩu"""
    try:
        reset_link = f"http://localhost:3000/reset-password?token={token}"

        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USER
        msg['To'] = email
        msg['Subject'] = 'Đặt lại mật khẩu'

        body = f"""
        <html>
            <body>
                <h2>Yêu cầu đặt lại mật khẩu</h2>
                <p>Bạn vừa yêu cầu đặt lại mật khẩu. Nếu đó là bạn, bấm vào link dưới đây:</p>
                <p><a href="{reset_link}">Đặt lại mật khẩu</a></p>
                <p>Hoặc sử dụng token: <b>{token}</b></p>
                <p>Nếu bạn không yêu cầu, hãy bỏ qua email này.</p>
            </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"Lỗi gửi email reset mật khẩu: {e}")
        return False
