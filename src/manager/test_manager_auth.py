import os
import unittest
from unittest.mock import patch

os.environ.setdefault('SECRET_KEY', 'test-only-secret-key')
os.environ.setdefault('AUTH_USERNAME', 'test-user')
os.environ.setdefault('AUTH_PASSWORD_HASH', 'scrypt:32768:8:1$test$invalid')

from werkzeug.security import check_password_hash, generate_password_hash
import docker
with patch.object(docker, 'from_env', return_value=object()):
    import manager


class ManagerAuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.password = 'correct horse battery staple'
        manager.AUTH_PASSWORD_HASH = generate_password_hash(self.password, method='pbkdf2:sha256:600000')
        manager.app.config.update(TESTING=True, SECRET_KEY='test-only-secret-key')
        self.client = manager.app.test_client()

    def csrf_from_login(self):
        response = self.client.get('/login')
        with self.client.session_transaction() as sess:
            return sess['csrf_token']

    def login(self):
        token = self.csrf_from_login()
        return self.client.post('/login', data={
            'csrf_token': token,
            'username': manager.AUTH_USERNAME,
            'password': self.password,
        })

    def test_manager_pages_and_api_require_login(self):
        response = self.client.get('/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers['Location'])
        self.assertEqual(self.client.get('/api/streams').status_code, 401)

    def test_stack_password_is_hashed_at_startup(self):
        with patch.dict(os.environ, {'AUTH_PASSWORD': self.password, 'AUTH_PASSWORD_HASH': 'ignored'}, clear=False):
            password_hash = manager.get_auth_password_hash()
            self.assertNotIn('AUTH_PASSWORD', os.environ)
        self.assertTrue(check_password_hash(password_hash, self.password))

    def test_settings_versions_match_build_and_shared_runner_pin(self):
        with patch.object(manager, 'APP_VERSION', '1.0.3'), patch.object(manager, 'APP_REVISION', 'unknown'):
            self.assertEqual(manager.get_manager_version(), 'v1.0.3')
        with patch.object(manager, 'APP_VERSION', 'main'), patch.object(manager, 'APP_REVISION', 'abcdef012345'):
            self.assertEqual(manager.get_manager_version(), 'main (abcdef0)')
        self.assertEqual(manager.get_streamlink_version(), '8.6.3')

    def test_login_and_cookie_attributes(self):
        response = self.login()
        self.assertEqual(response.status_code, 302)
        cookie = response.headers['Set-Cookie']
        self.assertIn('HttpOnly', cookie)
        self.assertIn('SameSite=Lax', cookie)
        self.assertNotIn('Secure', cookie)  # LAN HTTP mode; HTTPS deployments set it.

    def test_failed_login_does_not_authenticate(self):
        token = self.csrf_from_login()
        response = self.client.post('/login', data={
            'csrf_token': token, 'username': manager.AUTH_USERNAME, 'password': 'wrong'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get('/api/streams').status_code, 401)

    def test_every_manager_post_requires_csrf(self):
        self.login()
        response = self.client.post('/save-setting', json={'key': 'x', 'value': 'y'})
        self.assertEqual(response.status_code, 400)
        with self.client.session_transaction() as sess:
            csrf = sess['csrf_token']
        with patch.object(manager, 'save_setting'):
            response = self.client.post('/save-setting', json={'key': 'x', 'value': 'y'},
                                        headers={'X-CSRF-Token': csrf})
        self.assertEqual(response.status_code, 200)

    def test_logout_requires_csrf_and_clears_session(self):
        self.login()
        self.assertEqual(self.client.post('/logout').status_code, 400)
        with self.client.session_transaction() as sess:
            csrf = sess['csrf_token']
        response = self.client.post('/logout', data={'csrf_token': csrf})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get('/api/streams').status_code, 401)


if __name__ == '__main__':
    unittest.main()
