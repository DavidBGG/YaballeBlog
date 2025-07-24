import json
import threading
from typing import Any, Dict, List

USERS_FILE = 'users.json'
POSTS_FILE = 'posts.json'

_data_locks = {
    USERS_FILE: threading.Lock(),
    POSTS_FILE: threading.Lock(),
}

def _read_json_file(filename: str) -> Any:
    with _data_locks[filename]:
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

def _write_json_file(filename: str, data: Any) -> None:
    with _data_locks[filename]:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

def get_all_users() -> List[Dict]:
    return _read_json_file(USERS_FILE)

def save_all_users(users: List[Dict]) -> None:
    _write_json_file(USERS_FILE, users)

def get_all_posts() -> List[Dict]:
    return _read_json_file(POSTS_FILE)

def save_all_posts(posts: List[Dict]) -> None:
    _write_json_file(POSTS_FILE, posts) 