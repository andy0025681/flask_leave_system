import unittest
from app import create_app, db
from app.models import LeaveType, Gender

class LeaveTypeModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        LeaveType.insert_leave_type()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_basic(self):
        l = LeaveType()
        self.assertTrue(l.id is None)
        self.assertTrue(l.name is None)
        self.assertTrue(l.permissions is not None)
        self.assertEqual(0, l.permissions)
        self.assertTrue(l.leave_logs is not None)
    
    def test_insert(self):
        keys = ['事假', '病假', '生理假', '特休假', '婚假', '喪假', '產假/陪產假', '公假']
        for k in keys:
            leaveType = LeaveType.query.filter_by(name=k).first()
            self.assertTrue(leaveType is not None)
            if k == '生理假':
                self.assertTrue(leaveType.has_permission(Gender.FEMALE))
                self.assertFalse(leaveType.has_permission(Gender.MALE))
            else:
                self.assertTrue(leaveType.has_permission(Gender.FEMALE+Gender.MALE))
                

