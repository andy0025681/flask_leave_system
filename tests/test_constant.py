import unittest
from app.models import Permission, Gender, Status

class ConstantTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_permission(self):
        self.assertEqual(1, Permission.ASK_LEAVE)
        self.assertEqual(2, Permission.REVIEW_LEAVE)
        self.assertEqual(4, Permission.EDIT_USER)
        self.assertEqual(8, Permission.ADMIN)

    def test_gender(self):
        self.assertEqual(1, Gender.MALE)
        self.assertEqual(2, Gender.FEMALE)

    def test_status(self):
        self.assertEqual(1, Status.UNDER_REVIEW)
        self.assertEqual(2, Status.TURN_DOWN)
        self.assertEqual(4, Status.AGREE)