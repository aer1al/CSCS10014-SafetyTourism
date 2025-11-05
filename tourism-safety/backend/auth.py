import os
from functools import wraps
from flask import request, jsonify, g
from jose import jwt, JWTError
from dotenv import load_dotenv

# Import hàm tìm user từ file management
from user_management import find_user_by_id 

# Tải biến môi trường (để lấy SECRET_KEY)
load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = "HS256"

if not SECRET_KEY:
    raise EnvironmentError("SECRET_KEY không được thiết lập trong file .env")

def create_access_token(user_id):
    """Tạo một JWT access token mới cho user."""
    to_encode = {"sub": user_id} # 'sub' (subject) là ID của user
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def jwt_required(f):
    """
    Một decorator để bảo vệ các endpoint.
    Nó sẽ kiểm tra header 'Authorization: Bearer <token>'
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        # Kiểm tra xem 'Authorization' header có tồn tại không
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            parts = auth_header.split()
            
            # Đảm bảo header có dạng 'Bearer <token>'
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
        
        if not token:
            return jsonify({"error": "Token is missing"}), 401
            
        try:
            # Giải mã token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            
            if user_id is None:
                 return jsonify({"error": "Invalid token payload"}), 401
            
            # Tìm user trong "DB" và gán vào 'g' (global context)
            user = find_user_by_id(user_id)
            if not user:
                return jsonify({"error": "User not found"}), 401
                
            g.current_user = user # Giờ đây endpoint có thể truy cập g.current_user
            
        except JWTError as e:
            return jsonify({"error": f"Token is invalid: {str(e)}"}), 401
        except Exception as e:
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500

        return f(*args, **kwargs)
    return decorated_function