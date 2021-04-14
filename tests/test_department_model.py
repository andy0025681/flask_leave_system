import unittest
from app import create_app, db
from app.models import Department

class DepartmentModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Department.insert_department()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_basic(self):
        d = Department()
        self.assertTrue(d.id is None)
        self.assertTrue(d.name is None)
        self.assertTrue(d.users is not None)
        self.assertTrue(d.leaveLogs is not None)

    def test_insert(self):
        keys = ['人資部門', '資訊科技部門', '研發部門', '公關部門', '客服部', '行銷部', '培訓部', '銷售部', '行政部門', '會計部門']
        for k in keys:
            department = Department.query.filter_by(name=k).first()
            self.assertTrue(department is not None)