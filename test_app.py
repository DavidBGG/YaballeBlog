import unittest
from app import app, tokens
import json
import hashlib

class BlogApiTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        # Clear tokens before each test
        tokens.clear()

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def test_health(self):
        """Test health check endpoint"""
        resp = self.client.get('/health')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('status', resp.get_json())

    def test_register_and_login(self):
        """Test user registration and login"""
        username = 'testuser'
        password = 'testpass'
        # Register
        resp = self.client.post('/auth/register', json={'username': username, 'password': password})
        self.assertIn(resp.status_code, (201, 400))  # 400 if already exists
        # Login
        resp = self.client.post('/auth/login', json={'username': username, 'password': password})
        self.assertEqual(resp.status_code, 200)
        token = resp.get_json().get('token')
        self.assertIsNotNone(token)
        return token

    def test_create_post(self):
        """Test creating a blog post"""
        token = self.test_register_and_login()
        resp = self.client.post('/posts/',
            headers={'Authorization': token},
            json={'title': 'Test Post', 'content': 'Test Content'})
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data['title'], 'Test Post')
        return data['post_id'], token

    def test_upvote_post(self):
        """Test upvoting a post"""
        post_id, token = self.test_create_post()
        # Upvote
        resp = self.client.post(f'/posts/{post_id}/upvote')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('upvotes', resp.get_json())
        self.assertEqual(resp.get_json()['upvotes'], 1)

    def test_moderator_login(self):
        """Test moderator can login and access moderator endpoints"""
        # Login as admin moderator
        resp = self.client.post('/auth/login', json={'username': 'admin', 'password': 'admin123'})
        self.assertEqual(resp.status_code, 200)
        token = resp.get_json().get('token')
        self.assertIsNotNone(token)
        
        # Test moderator endpoint access
        resp = self.client.get('/moderator/users', headers={'Authorization': token})
        self.assertEqual(resp.status_code, 200)
        users = resp.get_json()
        self.assertIsInstance(users, list)
        return token

    def test_moderator_create_moderator(self):
        """Test that moderators can create other moderators"""
        admin_token = self.test_moderator_login()
        
        # Create new moderator with unique username
        import time
        unique_username = f'newmod_{int(time.time())}'
        resp = self.client.post('/auth/register',
            headers={'Authorization': admin_token},
            json={'username': unique_username, 'password': 'modpass', 'role': 'moderator'})
        # Accept both 201 (created) and 400 (already exists) as valid
        self.assertIn(resp.status_code, (201, 400))
        if resp.status_code == 201:
            self.assertIn('moderator', resp.get_json()['message'])

    def test_regular_user_cannot_create_moderator(self):
        """Test that regular users cannot create moderator accounts"""
        # Create regular user
        resp = self.client.post('/auth/register', json={'username': 'regularuser', 'password': 'pass123'})
        self.assertIn(resp.status_code, (201, 400))
        
        # Try to create moderator without proper authorization
        resp = self.client.post('/auth/register',
            json={'username': 'fakemoderator', 'password': 'pass123', 'role': 'moderator'})
        self.assertEqual(resp.status_code, 403)
        self.assertIn('Only moderators can create moderator accounts', resp.get_json()['message'])

    def test_moderator_can_delete_any_post(self):
        """Test that moderators can delete posts from other users"""
        # Create a regular user and post
        user_token = self.test_register_and_login()
        resp = self.client.post('/posts/',
            headers={'Authorization': user_token},
            json={'title': 'User Post', 'content': 'This will be deleted by moderator'})
        self.assertEqual(resp.status_code, 201)
        post_id = resp.get_json()['post_id']
        
        # Login as moderator and delete the post
        admin_token = self.test_moderator_login()
        resp = self.client.delete(f'/posts/{post_id}', headers={'Authorization': admin_token})
        self.assertEqual(resp.status_code, 204)
        
        # Verify post is deleted
        resp = self.client.get(f'/posts/{post_id}')
        self.assertEqual(resp.status_code, 404)

    def test_moderator_can_edit_any_post(self):
        """Test that moderators can edit posts from other users while preserving authorship"""
        # Create a regular user and post
        user_token = self.test_register_and_login()
        resp = self.client.post('/posts/',
            headers={'Authorization': user_token},
            json={'title': 'Original Title', 'content': 'Original Content'})
        self.assertEqual(resp.status_code, 201)
        post_data = resp.get_json()
        post_id = post_data['post_id']
        original_author_id = post_data['author_id']
        
        # Login as moderator and edit the post
        admin_token = self.test_moderator_login()
        resp = self.client.put(f'/posts/{post_id}',
            headers={'Authorization': admin_token},
            json={'title': 'Moderated Title', 'content': 'Moderated Content'})
        self.assertEqual(resp.status_code, 200)
        
        # Verify post was edited but author preserved
        updated_post = resp.get_json()
        self.assertEqual(updated_post['title'], 'Moderated Title')
        self.assertEqual(updated_post['content'], 'Moderated Content')
        self.assertEqual(updated_post['author_id'], original_author_id)  # Author preserved

    def test_search_functionality(self):
        """Test search functionality works correctly"""
        # Create a post to search for
        post_id, token = self.test_create_post()
        
        # Search for the post
        resp = self.client.get('/search/?q=Test')
        self.assertEqual(resp.status_code, 200)
        results = resp.get_json()
        self.assertIsInstance(results, list)
        self.assertTrue(any(post['title'] == 'Test Post' for post in results))

if __name__ == '__main__':
    unittest.main()
