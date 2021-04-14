import unittest
from app import create_app, db
from app.models import Role, Permission

class DepartmentModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_basic(self):
        r = Role()
        self.assertTrue(r.id is None)
        self.assertTrue(r.name is None)
        self.assertTrue(r.default is None)
        self.assertTrue(r.permissions is not None)
        self.assertTrue(r.users is not None)

    def test_insert(self):
        keys = ['Staff', 'Supervisor', 'Administrator']
        for k in keys:
            role = Role.query.filter_by(name=k).first()
            self.assertTrue(role is not None)
            if k == 'Staff':
                self.assertTrue(role.has_permission(Permission.ASK_LEAVE))
                self.assertFalse(role.has_permission(Permission.REVIEW_LEAVE))
                self.assertFalse(role.has_permission(Permission.EDIT_USER))
                self.assertFalse(role.has_permission(Permission.ADMIN))
            elif k == 'Supervisor':
                self.assertTrue(role.has_permission(Permission.ASK_LEAVE))
                self.assertTrue(role.has_permission(Permission.REVIEW_LEAVE))
                self.assertFalse(role.has_permission(Permission.EDIT_USER))
                self.assertFalse(role.has_permission(Permission.ADMIN))
            elif k == 'Administrator':
                self.assertTrue(role.has_permission(Permission.ASK_LEAVE))
                self.assertTrue(role.has_permission(Permission.REVIEW_LEAVE))
                self.assertTrue(role.has_permission(Permission.EDIT_USER))
                self.assertTrue(role.has_permission(Permission.ADMIN))