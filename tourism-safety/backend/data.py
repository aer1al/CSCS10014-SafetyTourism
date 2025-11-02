import json
import os

# Absolute path to JSON file
DATA_FILE = os.path.join(os.path.dirname(__file__), "users.json")



#  JSON File Operations


def load_users():
    """Load all users from the JSON file."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except json.JSONDecodeError:
        print(" Users.json corrupted — recreating a new one.")
        return []


def save_users(users):
    """Save the list of users to the JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)



#  User Management Functions

def find_user(username):
    """Return a user dictionary if found, otherwise None."""
    users = load_users()
    for u in users:
        if u["username"] == username:
            return u
    return None


def add_user(username, password, email, phone):
    """Register a new user if the username does not already exist."""
    users = load_users()
    if any(u["username"] == username for u in users):
        return False  # Username already exists

    new_user = {
        "username": username,
        "password": password,
        "email": email,
        "phone": phone,
        "search_history": []
    }

    users.append(new_user)
    save_users(users)
    return True


def check_login(username, password):
    """Validate user login credentials."""
    users = load_users()
    for u in users:
        if u["username"] == username and u["password"] == password:
            return True
    return False


def update_user_info(username, **kwargs):
    """Update user information such as email, phone, or password."""
    users = load_users()
    for u in users:
        if u["username"] == username:
            u.update(kwargs)
            save_users(users)
            return True
    return False


def add_search_history(username, query):
    """Add a new search query to the user's history (keep only last 3)."""
    users = load_users()
    for u in users:
        if u["username"] == username:
            u.setdefault("search_history", [])
            u["search_history"].insert(0, query)
            u["search_history"] = u["search_history"][:3]
            save_users(users)
            return True
    return False


def delete_user(username):
    """Delete a user from the JSON file."""
    users = load_users()
    new_users = [u for u in users if u["username"] != username]
    if len(new_users) == len(users):
        return False  # No user deleted
    save_users(new_users)
    return True

def check_login_by_email(email, password):
    """Validate login credentials using email instead of username."""
    users = load_users()
    for u in users:
        if u["email"] == email and u["password"] == password:
            return True
    return False