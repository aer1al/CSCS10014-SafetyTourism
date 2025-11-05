import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Tên file CSDL
DB_FILE = 'users.json'

def load_users():
    """Tải tất cả người dùng từ file JSON."""
    if not os.path.exists(DB_FILE):
        # Nếu file không tồn tại, tạo file với mảng rỗng
        save_users([])
        return []
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Nếu file bị lỗi, ghi đè bằng mảng rỗng
        save_users([])
        return []

def save_users(users_list):
    """Lưu danh sách người dùng vào file JSON."""
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_list, f, indent=4, ensure_ascii=False)

def find_user_by_username(username):
    """Tìm người dùng bằng username."""
    users = load_users()
    for user in users:
        if user['username'] == username:
            return user
    return None

def find_user_by_id(user_id):
    """Tìm người dùng bằng ID."""
    users = load_users()
    for user in users:
        if user['id'] == user_id:
            return user
    return None

def register_user(username, password, email, address=None):
    """Đăng ký người dùng mới."""
    users = load_users()
    
    # 1. Kiểm tra tồn tại
    if find_user_by_username(username):
        return None # Trả về None nếu username đã tồn tại

    # 2. Tạo ID mới (đơn giản)
    new_id = 1
    if users:
        # Tìm ID lớn nhất và + 1
        new_id = max(user.get('id', 0) for user in users) + 1

    # 3. Băm mật khẩu (QUAN TRỌNG)
    hashed_password = generate_password_hash(password)

    # 4. Tạo user object
    new_user = {
        "id": new_id,
        "username": username,
        "password": hashed_password, # Chỉ lưu mật khẩu đã băm
        "email": email,
        "address": address or "",
        "favorite_locations": [] # Chuẩn bị cho tương lai
    }

    # 5. Lưu lại
    users.append(new_user)
    save_users(users)
    
    return new_user