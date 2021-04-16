import unittest
from app import create_app, db
from app.models import User, Role, LeaveType, Department, Gender

class MainClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        LeaveType.insert_leave_type()
        Department.insert_department()
        self.client = self.app.test_client(use_cookies=True)
        self.pw = 'cat'
        self.user = User(email='john@example.com', username='john', password=self.pw, gender=Gender.MALE, department_id=1)
        self.admin = User(email='admin@example.com', username='admin', password='admin', gender=Gender.MALE, department_id=1)
        self.admin.role = Role.query.filter_by(name='Administrator').first()
        db.session.add(self.user, self.admin)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_login_logout(self):
        # login
        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': 'wrong password'
        })
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Hello, {}'.format(self.user.username) in response.get_data(as_text=True))

        # log out
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('你已登出。' in response.get_data(as_text=True))

    def test_change_password(self):
        # not login
        response = self.client.get('/auth/change-password')
        self.assertEqual(response.status_code, 302)

        # login
        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/auth/change-password')
        self.assertEqual(response.status_code, 200)

        self.assertTrue(self.user.verify_password(self.pw))
        response = self.client.post('/auth/change-password', data={
            'old_password': 'wrong password',
            'password': 'dog',
            'password2': 'dog'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.verify_password(self.pw))

        self.assertTrue(self.user.verify_password(self.pw))
        response = self.client.post('/auth/change-password', data={
            'old_password': self.pw,
            'password': 'dog',
            'password2': 'dog'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.user.verify_password('dog'))

    def test_password_reset_request(self):
        # not login
        response = self.client.get('/auth/reset')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/auth/reset', data={
            'email': self.user.email
        })
        self.assertEqual(response.status_code, 302)
        
        # login
        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/auth/reset')
        self.assertEqual(response.status_code, 302)

    def test_password_reset(self):
        token = self.user.generate_reset_token()
        response = self.client.get('/auth/reset/{}'.format(token))
        self.assertEqual(response.status_code, 200)

        self.assertTrue(self.user.verify_password(self.pw))
        response = self.client.post('/auth/reset/{}'.format(token), data={
            'password': 'dog',
            'password2': 'dog'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.user.verify_password('dog'))

        response = self.client.post('/auth/reset/{}wrongToken'.format(token), data={
            'password': 'car',
            'password2': 'car'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.user.verify_password('dog'))

        # login
        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': 'dog'
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/auth/reset/{}'.format(token))
        self.assertEqual(response.status_code, 302)

    def test_change_email_request(self):
        # not login
        response = self.client.get('/auth/change_email')
        self.assertEqual(response.status_code, 302)

        # login
        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/auth/change_email')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/auth/change_email', data={
            'email': '123@abc.com',
            'password': 'wrong password'
        })
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/auth/change_email', data={
            'email': '123@abc.com',
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)

    def test_change_email(self):
        token = self.user.generate_email_change_token('123@abc.com')
        # not login
        response = self.client.get('/auth/change_email/{}'.format(token), data={
            'email': '123@abc.com',
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)

        # login
        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/auth/change_email/{}wrongToken'.format(token), data={
            'email': '123@abc.com',
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.user.email != '123@abc.com')

        response = self.client.get('/auth/change_email/{}'.format(token), data={
            'email': '123@abc.com',
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.user.email, '123@abc.com')

    def test_edit_user(self):
        # staff login
        response = self.client.post('/auth/login', data={
            'email': self.admin.email,
            'password': 'admin'
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.post('/auth/edit-user', data={
            'email': 'newUser@abc.com',
            'username': 'newUser',
            'password': 'newUser',
            'password2': 'newUser',
            'department': 1,
            'gender': Gender.FEMALE
        })
        self.assertEqual(response.status_code, 302)

    def test_show_register(self):
        # not login
        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/auth/login' in response.location)

        # staff login
        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 403)
        
        # log out
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('你已登出。' in response.get_data(as_text=True))

        # admin login
        response = self.client.post('/auth/login', data={
            'email': self.admin.email,
            'password': 'admin'
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('edit_user_status=0' in response.headers.get_all('Set-Cookie')[0])

        response = self.client.get('/auth/edit-user')
        self.assertEqual(response.status_code, 200)

    def test_show_self_log(self):
        # not login
        response = self.client.get('/auth/allUser')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/auth/login' in response.location)

        # staff login
        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/auth/allUser')
        self.assertEqual(response.status_code, 403)
        
        # log out
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('你已登出。' in response.get_data(as_text=True))

        # admin login
        response = self.client.post('/auth/login', data={
            'email': self.admin.email,
            'password': 'admin'
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/auth/allUser')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('edit_user_status=1' in response.headers.get_all('Set-Cookie')[0])

        response = self.client.get('/auth/edit-user')
        self.assertEqual(response.status_code, 200)