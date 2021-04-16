import re
import unittest
from app import create_app, db
from app.models import User, Role, LeaveType, Department, Gender, LeaveLog, Status
from datetime import datetime
from flask import url_for
import time

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

    def test_home_page(self):
        # not login
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/auth/login' in response.location)
        
        # login
        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Hello, {}'.format(self.user.username) in response.get_data(as_text=True))

    def test_user_page(self):
        # not login
        response = self.client.get('/user/{}'.format(self.user.username))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/auth/login' in response.location)

        # login
        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/user/{}'.format(self.user.username))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.username in response.get_data(as_text=True))
        self.assertTrue(self.user.department.name in response.get_data(as_text=True))
        self.assertTrue(str(self.user.officalLeave) in response.get_data(as_text=True))
    
    def test_user_list_page(self):
        # not login
        response = self.client.get('/user/list')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/auth/login' in response.location)

        # login
        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/user/list')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('帳號' in response.get_data(as_text=True))
        self.assertTrue('部門' in response.get_data(as_text=True))
        self.assertTrue('電子郵件' in response.get_data(as_text=True))

    def test_edit_profile(self):
        # not login
        response = self.client.get('/edit-profile')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/auth/login' in response.location)

        # login
        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/edit-profile')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Edit Profile' in response.get_data(as_text=True))
        self.assertTrue('Real name' in response.get_data(as_text=True))
        self.assertTrue('Location' in response.get_data(as_text=True))
        self.assertTrue('About me' in response.get_data(as_text=True))

        response = self.client.post('/edit-profile', data={
            'name': 'test',
            'location': 'test',
            'about_me': 'test'
        })
        self.assertEqual(response.status_code, 302)

    def test_edit_profile_admin(self):
        # not login
        response = self.client.get('/edit-profile/{}'.format(self.user.id))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/auth/login' in response.location)

        # staff login
        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/edit-profile/{}'.format(self.user.id))
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

        response = self.client.get('/edit-profile/{}'.format(self.user.id))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Edit Profile' in response.get_data(as_text=True))
        self.assertTrue('Email' in response.get_data(as_text=True))
        self.assertTrue('Username' in response.get_data(as_text=True))
        self.assertTrue('Role' in response.get_data(as_text=True))
        self.assertTrue('Real name' in response.get_data(as_text=True))
        self.assertTrue('Location' in response.get_data(as_text=True))
        self.assertTrue('About me' in response.get_data(as_text=True))

        response = self.client.post('/edit-profile/{}'.format(self.user.id), data={
            'email': 'test@abc.com',
            'username': 'test',
            'role': 1,
            'name': 'test',
            'location': 'test',
            'about_me': 'test'
        })
        self.assertEqual(response.status_code, 302)

    def test_ask_leave(self):
        # not login
        response = self.client.get('/askLeave')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/auth/login' in response.location)

        # staff login
        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/askLeave')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('假別' in response.get_data(as_text=True))
        self.assertTrue('職務代理人' in response.get_data(as_text=True))
        self.assertTrue('起始日期' in response.get_data(as_text=True))
        self.assertTrue('起始時間' in response.get_data(as_text=True))
        self.assertTrue('結束日期' in response.get_data(as_text=True))
        self.assertTrue('結束時間' in response.get_data(as_text=True))
        self.assertTrue('請假原因' in response.get_data(as_text=True))

    def test_review_leave(self):
        log = LeaveLog(start=datetime(2021, 4, 10, 9, 0, 0), end=datetime(2021, 4, 10, 18, 0, 0),
                        duration=8.0, reason='test', type_id=1, staff_id=self.user.id, agent_id=self.admin.id)
        db.session.add(log)
        db.session.commit()
        token = self.admin.generate_review_leave_token(log, Status.AGREE)

        # not login
        response = self.client.get('/reviewLeave/{}'.format(token))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/auth/login' in response.location)
        self.assertTrue(log.status is Status.UNDER_REVIEW)

        # admin login
        response = self.client.post('/auth/login', data={
            'email': self.admin.email,
            'password': 'admin'
        })
        self.assertEqual(response.status_code, 302)
        
        response = self.client.get('/reviewLeave/{}'.format(token))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(log.status is Status.AGREE)

    def test_show_all_log(self):
        # not login
        response = self.client.get('/allLog')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/auth/login' in response.location)

        # staff login
        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/allLog')
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

        response = self.client.get('/allLog')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('log_status=0' in response.headers.get_all('Set-Cookie')[0])

        response = self.client.get('/leaveLog')
        self.assertEqual(response.status_code, 200)

    def test_show_self_log(self):
        # not login
        response = self.client.get('/selfLog')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/auth/login' in response.location)
        
        # staff login
        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)
        
        response = self.client.get('/selfLog')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('log_status=1' in response.headers.get_all('Set-Cookie')[0])

        response = self.client.get('/leaveLog')
        self.assertEqual(response.status_code, 200)

    def test_show_agent_log(self):
        # not login
        response = self.client.get('/agentLog')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/auth/login' in response.location)

        # staff login
        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/agentLog')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('log_status=2' in response.headers.get_all('Set-Cookie')[0])

        response = self.client.get('/leaveLog')
        self.assertEqual(response.status_code, 200)

    def test_show_department_log(self):
        response = self.client.get('/departmentLog')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/auth/login' in response.location)
        
        # staff login
        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/departmentLog')
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

        response = self.client.get('/departmentLog')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('log_status=3' in response.headers.get_all('Set-Cookie')[0])

        response = self.client.get('/leaveLog')
        self.assertEqual(response.status_code, 200)