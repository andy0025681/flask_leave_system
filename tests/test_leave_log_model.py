import unittest
from datetime import datetime
from app import create_app, db
from app.models import User, LeaveType, LeaveLog, Status

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
        date = "{}-{}-{}".format(datetime.today().year, datetime.today().month, datetime.today().day)
        start = datetime.strptime("{} 09:00:00".format(date), "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime("{} 18:00:00".format(date), "%Y-%m-%d %H:%M:%S")
        l = LeaveLog(start=start, end=end)
        self.assertTrue(l.id is None)
        self.assertTrue(l.start is not None)
        self.assertTrue(l.end is not None)
        self.assertTrue(l.duration is not None)
        self.assertTrue(l.reason is None)
        self.assertTrue(l.status is not None)
        self.assertTrue(l.timestamp is None)
        self.assertTrue(l.department_id is None)
        self.assertTrue(l.type_id is None)
        self.assertTrue(l.staff_id is None)
        self.assertTrue(l.agent_id is None)

    # def test_update_status(self):
    #     u1 = User(password='cat')
    #     u2 = User(password='dog')
    #     u1.officalLeave = 0
    #     u2.officalLeave = 1
    #     db.session.add(u1, u2)
    #     db.session.commit()
    #     date = "{}-{}-{}".format(datetime.today().year, datetime.today().month, datetime.today().day)
    #     start = datetime.strptime("{} 09:00:00".format(date), "%Y-%m-%d %H:%M:%S")
    #     end = datetime.strptime("{} 18:00:00".format(date), "%Y-%m-%d %H:%M:%S")
    #     typeID = LeaveType.query.filter_by(name='特休假').first().id
    #     l1 = LeaveLog(start=start, end=end, staff_id=u1.id, type_id=typeID)
    #     l2 = LeaveLog(start=start, end=end, staff_id=u2.id, type_id=typeID)
    #     l = [
    #         [Status.UNDER_REVIEW, Status.UNDER_REVIEW, False],
    #         [Status.UNDER_REVIEW, Status.TURN_DOWN, True],
    #         [Status.UNDER_REVIEW, Status.AGREE],
    #         [Status.TURN_DOWN, Status.UNDER_REVIEW, False],
    #         [Status.TURN_DOWN, Status.TURN_DOWN, False],
    #         [Status.TURN_DOWN, Status.AGREE],
    #         [Status.AGREE, Status.UNDER_REVIEW, False],
    #         [Status.AGREE, Status.TURN_DOWN, True],
    #         [Status.AGREE, Status.AGREE, False],
    #     ]
    #     for i in l:
    #         l1.Status = l2.Status = i[0]
    #         if len(i) == 3:
    #             self.assertEqual(i[2], l1.update_status(i[1]))
    #             self.assertEqual(i[2], l2.update_status(i[1]))
    #         else:
    #             self.assertEqual(False, l1.update_status(i[1]))
    #             self.assertEqual(True, l1.update_status(i[1]))