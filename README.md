# Simple Blog Platform Backend

A simple, modular, and well-documented blog platform backend built with Python and Flask. Data is stored in JSON files for easy setup and demonstration.

## Features
- User registration and login (token-based authentication)
- CRUD operations for blog posts
- Upvote/downvote posts
- Comment on posts
- Search posts by title/content
- Data validation and HTTP conventions
- JSON file storage (no external DB required)
- Containerized with Docker

## Requirements
- Python 3.11+
- Flask

## Setup & Run Locally
1. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```
2. Start the Flask app:
   ```bash
   python3 app.py
   ```
3. The API will be available at `http://localhost:8000`
4. **Interactive API Documentation**: Visit `http://localhost:8000/docs/` for Swagger UI

## Run with Docker

### Prerequisites
- Docker Desktop must be installed and running

### Steps
1. **Build the Docker image:**
   ```bash
   docker build -t blog-api .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 blog-api
   ```

3. **Access the API:**
   - API Base URL: `http://localhost:8000`
   - Swagger Documentation: `http://localhost:8000/docs/`
   - Health Check: `http://localhost:8000/health`

### Docker Container Features
- ✅ **Full API functionality** - All endpoints work in containerized environment
- ✅ **Persistent data** - JSON files stored inside container
- ✅ **Swagger UI** - Interactive documentation available
- ✅ **Moderator system** - Default admin account: `admin`/`admin123`
- ✅ **All tests pass** - Complete functionality verified

### Docker Management Commands
```bash
# View running containers
docker ps

# Stop the container
docker stop <container_id>

# View container logs
docker logs <container_id>

# Remove the image (if needed)
docker rmi blog-api
```

## API Endpoints
- `POST   /auth/register` — Register a new user
- `POST   /auth/login` — Login and receive a token
- `POST   /posts/` — Create a post (auth required)
- `GET    /posts/` — List all posts
- `GET    /posts/<post_id>` — Get a single post
- `PUT    /posts/<post_id>` — Update a post (auth, author only)
- `DELETE /posts/<post_id>` — Delete a post (auth, author only)
- `POST   /posts/<post_id>/upvote` — Upvote a post
- `POST   /posts/<post_id>/downvote` — Downvote a post
- `POST   /posts/<post_id>/comments` — Add a comment (auth required)
- `GET    /search/?q=term` — Search posts by title/content
- `GET    /docs/` — **Interactive Swagger API Documentation**
## Moderator Role System

### User Roles
- **user** (default): Can create, edit, and delete their own posts
- **moderator**: Can edit and delete ANY post, plus access moderator-only endpoints

### Moderator Endpoints
- `GET /moderator/users` — View all users (moderator only)
- `GET /moderator/posts` — View all posts with moderation info (moderator only)

### Creating Moderators
- Only existing moderators can create new moderator accounts
- Use the registration endpoint with `"role": "moderator"`
- A default moderator account is created: **username:** `admin`, **password:** `admin123`

### Moderator Permissions
- ✅ Edit any post (preserves original author)
- ✅ Delete any post
- ✅ View all users and posts
- ✅ Create new moderator accounts
- ❌ Cannot change post ownership



### Authentication
- Register and login to receive a token.
- Pass the token in the `Authorization` header for protected endpoints.

### Example Usage
```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypass"}'

# Login  
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypass"}'

# Create post (use token from login)
curl -X POST http://localhost:8000/posts/ \
  -H "Authorization: <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Post", "content": "Hello world!"}'
```

## Testing
Comprehensive test suite with 10 tests covering:
- ✅ Health check endpoint
- ✅ User registration and login
- ✅ Post creation and management
- ✅ Post voting system
- ✅ Search functionality
- ✅ Moderator authentication
- ✅ Moderator permissions (edit/delete any post)
- ✅ Moderator account creation
- ✅ Security (regular users cannot create moderators)

Run the test suite:
```bash
python3 -m unittest test_app.py -v
```

## License
MIT 