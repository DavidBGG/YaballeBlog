from datetime import datetime
from typing import Optional, Dict

class User:
    def __init__(self, user_id: int, username: str, password_hash: str, role: str = 'user'):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.role = role  # "user" or "moderator"

    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'username': self.username,
            'password_hash': self.password_hash,
            'role': self.role
        }

    @staticmethod
    def from_dict(data: Dict) -> 'User':
        return User(
            user_id=data['user_id'],
            username=data['username'],
            password_hash=data['password_hash'],
            role=data.get('role', 'user')  # Default to 'user' for backward compatibility
        )

    def is_moderator(self) -> bool:
        return self.role == 'moderator'

    def is_moderator(self) -> bool:
        return self.role == "moderator"

class Post:
    def __init__(self, post_id: int, title: str, content: str, author_id: int, publication_date: str, upvotes: int = 0, downvotes: int = 0, comments: Optional[list] = None):
        self.post_id = post_id
        self.title = title
        self.content = content
        self.author_id = author_id
        self.publication_date = publication_date
        self.upvotes = upvotes
        self.downvotes = downvotes
        self.comments = comments or []

    def to_dict(self) -> Dict:
        return {
            'post_id': self.post_id,
            'title': self.title,
            'content': self.content,
            'author_id': self.author_id,
            'publication_date': self.publication_date,
            'upvotes': self.upvotes,
            'downvotes': self.downvotes,
            'comments': self.comments
        }

    @staticmethod
    def from_dict(data: Dict) -> 'Post':
        return Post(
            post_id=data['post_id'],
            title=data['title'],
            content=data['content'],
            author_id=data['author_id'],
            publication_date=data['publication_date'],
            upvotes=data.get('upvotes', 0),
            downvotes=data.get('downvotes', 0),
            comments=data.get('comments', [])
        )

    @staticmethod
    def validate(data: Dict) -> Optional[str]:
        if not data.get('title') or not isinstance(data['title'], str):
            return 'Title is required and must be a string.'
        if not data.get('content') or not isinstance(data['content'], str):
            return 'Content is required and must be a string.'
        if not data.get('author_id') or not isinstance(data['author_id'], int):
            return 'Author ID is required and must be an integer.'
        return None
