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

    def test_403_error(self):
        response = self.client.post('/auth/login', data={
            'email': self.user.email,
            'password': self.pw
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/auth/edit-user')
        self.assertEqual(response.status_code, 403)

    def test_404_error(self):
        response = self.client.get('/no_page')
        self.assertEqual(response.status_code, 404)

    def test_500_error(self):
        response = self.client.get('/bad')
        self.assertEqual(response.status_code, 500)

