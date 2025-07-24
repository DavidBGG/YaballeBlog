from flask import Flask, request, g
from flask_restx import Api, Resource, fields, Namespace
from data_store import get_all_posts, save_all_posts, get_all_users, save_all_users
from models import Post, User
from datetime import datetime, timezone
import hashlib
import secrets
from functools import wraps

app = Flask(__name__)
api = Api(app, 
    title='Blog Platform API',
    description='A simple blog platform backend with user authentication, posts, voting, and comments',
    version='1.0.0',
    doc='/docs/'
)

# Namespaces
auth_ns = Namespace('auth', description='Authentication operations')
posts_ns = Namespace('posts', description='Blog posts operations')
search_ns = Namespace('search', description='Search operations')
mod_ns = Namespace('moderator', description='Moderator operations')

api.add_namespace(auth_ns, path='/auth')
api.add_namespace(posts_ns, path='/posts')
api.add_namespace(search_ns, path='/search')
api.add_namespace(mod_ns, path='/moderator')

# Models for Swagger documentation
user_model = api.model('User', {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password')
})

user_register_model = api.model('UserRegister', {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password'),
    'role': fields.String(description='User role (user/moderator)', default='user')
})

user_response = api.model('UserResponse', {
    'user_id': fields.Integer(description='User ID'),
    'username': fields.String(description='Username')
})

post_model = api.model('Post', {
    'title': fields.String(required=True, description='Post title'),
    'content': fields.String(required=True, description='Post content')
})

post_response = api.model('PostResponse', {
    'post_id': fields.Integer(description='Post ID'),
    'title': fields.String(description='Post title'),
    'content': fields.String(description='Post content'),
    'author_id': fields.Integer(description='Author ID'),
    'publication_date': fields.String(description='Publication date'),
    'upvotes': fields.Integer(description='Number of upvotes'),
    'downvotes': fields.Integer(description='Number of downvotes'),
    'comments': fields.List(fields.Raw, description='Comments')
})

comment_model = api.model('Comment', {
    'content': fields.String(required=True, description='Comment content')
})

login_response = api.model('LoginResponse', {
    'token': fields.String(description='Authentication token')
})

vote_response = api.model('VoteResponse', {
    'upvotes': fields.Integer(description='Total upvotes'),
    'downvotes': fields.Integer(description='Total downvotes')
})

# Authentication
tokens = {}

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_hex(16)

def authenticate(token: str):
    return tokens.get(token)  # Returns {'user_id': int, 'role': str} or None

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        auth_data = authenticate(token)
        if not auth_data:
            api.abort(401, 'Unauthorized')
        g.user_id = auth_data['user_id']
        g.user_role = auth_data['role']
        return f(*args, **kwargs)
    return wrapper

def require_moderator(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        auth_data = authenticate(token)
        if not auth_data:
            api.abort(401, 'Unauthorized')
        if auth_data['role'] != 'moderator':
            api.abort(403, 'Moderator access required')
        g.user_id = auth_data['user_id']
        g.user_role = auth_data['role']
        return f(*args, **kwargs)
    return wrapper

def is_author_or_moderator(post_author_id: int) -> bool:
    return g.user_id == post_author_id or g.user_role == 'moderator' 

# Health check
@api.route('/health')
class Health(Resource):
    def get(self):
        """Health check endpoint"""
        return {'status': 'ok'}

# Authentication endpoints
@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.expect(user_register_model)
    @auth_ns.marshal_with(api.model('Message', {'message': fields.String()}))
    def post(self):
        """Register a new user"""
        data = request.get_json()
        if not data.get('username') or not data.get('password'):
            api.abort(400, 'Username and password required.')
        
        # Handle role assignment
        role = data.get('role', 'user')
        if role == 'moderator':
            # Require existing moderator to create new moderators
            token = request.headers.get('Authorization')
            auth_data = authenticate(token)
            if not auth_data or auth_data['role'] != 'moderator':
                api.abort(403, 'Only moderators can create moderator accounts')
        
        users = get_all_users()
        if any(u['username'] == data['username'] for u in users):
            api.abort(400, 'Username already exists.')
        
        user_id = (max([u['user_id'] for u in users]) + 1) if users else 1
        password_hash = hash_password(data['password'])
        user = User(user_id, data['username'], password_hash, role)
        users.append(user.to_dict())
        save_all_users(users)
        return {'message': f'User registered successfully with role: {role}.'}, 201

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(user_model)
    @auth_ns.marshal_with(login_response)
    def post(self):
        """Login and receive authentication token"""
        data = request.get_json()
        if not data.get('username') or not data.get('password'):
            api.abort(400, 'Username and password required.')
        
        users = get_all_users()
        user = next((u for u in users if u['username'] == data['username']), None)
        if not user or user['password_hash'] != hash_password(data['password']):
            api.abort(401, 'Invalid credentials.')
        
        token = generate_token()
        tokens[token] = {
            'user_id': user['user_id'],
            'role': user.get('role', 'user')  # Default to 'user' for existing users
        }
        return {'token': token}

# Posts endpoints
@posts_ns.route('/')
class PostsList(Resource):
    @posts_ns.marshal_list_with(post_response)
    def get(self):
        """Get all blog posts"""
        posts = get_all_posts()
        return posts

    @posts_ns.expect(post_model)
    @posts_ns.marshal_with(post_response, code=201)
    @posts_ns.doc(security='apikey')
    @require_auth
    def post(self):
        """Create a new blog post (authentication required)"""
        data = request.get_json()
        error = Post.validate({**data, 'author_id': g.user_id})
        if error:
            api.abort(400, error)
        
        posts = get_all_posts()
        post_id = (max([p['post_id'] for p in posts]) + 1) if posts else 1
        publication_date = datetime.now(timezone.utc).isoformat()
        post = Post(
            post_id=post_id,
            title=data['title'],
            content=data['content'],
            author_id=g.user_id,
            publication_date=publication_date
        )
        posts.append(post.to_dict())
        save_all_posts(posts)
        return post.to_dict(), 201

@posts_ns.route('/<int:post_id>')
class PostDetail(Resource):
    @posts_ns.marshal_with(post_response)
    def get(self, post_id):
        """Get a specific blog post"""
        posts = get_all_posts()
        post = next((p for p in posts if p['post_id'] == post_id), None)
        if not post:
            api.abort(404, 'Post not found')
        return post

    @posts_ns.expect(post_model)
    @posts_ns.marshal_with(post_response)
    @posts_ns.doc(security='apikey')
    @require_auth
    def put(self, post_id):
        """Update a blog post (authentication required, author only)"""
        data = request.get_json()
        posts = get_all_posts()
        idx = next((i for i, p in enumerate(posts) if p['post_id'] == post_id), None)
        if idx is None:
            api.abort(404, 'Post not found')
        # Allow author or moderator to update
        if not is_author_or_moderator(posts[idx]['author_id']):
            api.abort(403, 'Forbidden')
        
        error = Post.validate({**data, 'author_id': g.user_id})
        if error:
            api.abort(400, error)
        
        posts[idx].update({
            'title': data['title'],
            'content': data['content']
            # Keep original author_id - don't change ownership
        })
        save_all_posts(posts)
        return posts[idx]

    @posts_ns.doc(security='apikey')
    @require_auth
    def delete(self, post_id):
        """Delete a blog post (authentication required, author only)"""
        posts = get_all_posts()
        idx = next((i for i, p in enumerate(posts) if p['post_id'] == post_id), None)
        if idx is None:
            api.abort(404, 'Post not found')
        # Allow author or moderator to update
        if not is_author_or_moderator(posts[idx]['author_id']):
            api.abort(403, 'Forbidden')
        
        new_posts = [p for p in posts if p['post_id'] != post_id]
        save_all_posts(new_posts)
        return '', 204

@posts_ns.route('/<int:post_id>/upvote')
class UpvotePost(Resource):
    @posts_ns.marshal_with(api.model('UpvoteResponse', {'upvotes': fields.Integer()}))
    def post(self, post_id):
        """Upvote a blog post"""
        posts = get_all_posts()
        post = next((p for p in posts if p['post_id'] == post_id), None)
        if not post:
            api.abort(404, 'Post not found')
        
        post['upvotes'] = post.get('upvotes', 0) + 1
        save_all_posts(posts)
        return {'upvotes': post['upvotes']}

@posts_ns.route('/<int:post_id>/downvote')
class DownvotePost(Resource):
    @posts_ns.marshal_with(api.model('DownvoteResponse', {'downvotes': fields.Integer()}))
    def post(self, post_id):
        """Downvote a blog post"""
        posts = get_all_posts()
        post = next((p for p in posts if p['post_id'] == post_id), None)
        if not post:
            api.abort(404, 'Post not found')
        
        post['downvotes'] = post.get('downvotes', 0) + 1
        save_all_posts(posts)
        return {'downvotes': post['downvotes']}

@posts_ns.route('/<int:post_id>/comments')
class PostComments(Resource):
    @posts_ns.expect(comment_model)
    @posts_ns.marshal_with(api.model('CommentResponse', {'message': fields.String()}), code=201)
    @posts_ns.doc(security='apikey')
    @require_auth
    def post(self, post_id):
        """Add a comment to a blog post (authentication required)"""
        data = request.get_json()
        if not data.get('content') or not isinstance(data['content'], str):
            api.abort(400, 'Content is required and must be a string.')
        
        posts = get_all_posts()
        post = next((p for p in posts if p['post_id'] == post_id), None)
        if not post:
            api.abort(404, 'Post not found')
        
        comment = {
            'user_id': g.user_id,
            'content': data['content'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        post.setdefault('comments', []).append(comment)
        save_all_posts(posts)
        return {'message': 'Comment added.'}, 201

# Search endpoint
@search_ns.route('/')
class SearchPosts(Resource):
    @search_ns.marshal_list_with(post_response)
    @search_ns.doc(params={'q': 'Search query'})
    def get(self):
        """Search blog posts by title or content"""
        query = request.args.get('q', '').lower()
        if not query:
            api.abort(400, 'Query parameter q is required.')
        
        posts = get_all_posts()
        results = [p for p in posts if query in p['title'].lower() or query in p['content'].lower()]
        return results


# Moderator endpoints
@mod_ns.route('/users')
class ModeratorUsers(Resource):
    @mod_ns.doc(security='apikey')
    @require_moderator
    def get(self):
        """Get all users (moderator only)"""
        users = get_all_users()
        # Remove password hashes from response
        safe_users = [{k: v for k, v in user.items() if k != 'password_hash'} 
                      for user in users]
        return safe_users

@mod_ns.route('/posts')
class ModeratorPosts(Resource):
    @mod_ns.doc(security='apikey')
    @require_moderator
    def get(self):
        """Get all posts with moderation info (moderator only)"""
        posts = get_all_posts()
        return posts

# Add security definitions
api.authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000) 