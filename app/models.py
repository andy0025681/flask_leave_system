from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_login import UserMixin
from . import db, login_manager

class Permission:
    ASK_LEAVE = 1
    PASS_LEAVE = 2
    EDIT_USER = 4
    ADMIN = 8

class Gender:
    MALE = 1
    FEMALE = 2

class Status:
    UNDER_REVIEW = 1
    TURN_DOWN = 2
    AGREE = 4

class LeaveType(db.Model):
    __tablename__ = 'leave_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    permissions = db.Column(db.Integer)
    leave_logs = db.relationship('LeaveLog', backref='type', lazy='dynamic')

    def __init__(self, **kwargs):
        super(LeaveType, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_leave_type():
        leaveTypes = {
            '事假': [Gender.MALE, Gender.FEMALE],
            '病假': [Gender.MALE, Gender.FEMALE],
            '生理假': [Gender.FEMALE],
            '特休假': [Gender.MALE, Gender.FEMALE],
            '婚假': [Gender.MALE, Gender.FEMALE],
            '喪假': [Gender.MALE, Gender.FEMALE],
            '產假/陪產假': [Gender.MALE, Gender.FEMALE],
            '公假': [Gender.MALE, Gender.FEMALE],
        }
        for t in leaveTypes:
            leaveType = LeaveType.query.filter_by(name=t).first()
            if leaveType is None:
                leaveType = LeaveType(name=t)
            leaveType.reset_permissions()
            for perm in leaveTypes[t]:
                leaveType.add_permission(perm)
            db.session.add(leaveType)
        db.session.commit()
    
    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self):
        return '<LeaveType %r>' % self.name

class LeaveLog(db.Model):
    __tablename__ = 'leave_logs'
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    duration = db.Column(db.Float)
    reason = db.Column(db.Text)
    status = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    type_id = db.Column(db.Integer, db.ForeignKey('leave_types.id'))
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    agent_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, **kwargs):
        super(LeaveLog, self).__init__(**kwargs)
        if self.status is None:
            self.status = Status.UNDER_REVIEW

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    department_id = db.Column(db.Integer, db.ForeignKey('deparements.id'))
    password_hash = db.Column(db.String(128))
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    gender = db.Column(db.Integer)
    ask_leave = db.relationship('LeaveLog',
                foreign_keys=[LeaveLog.staff_id],
                backref=db.backref('staff', lazy='joined'),
                lazy='dynamic',
                cascade='all, delete-orphan')
    agent = db.relationship('LeaveLog',
            foreign_keys=[LeaveLog.agent_id],
            backref=db.backref('agent', lazy='joined'),
            lazy='dynamic',
            cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True
    
    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email}).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)
        return True

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()
    
    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()
    
    def gravatar(self, size=100, default='identicon', rating='g'):
        url = 'https://secure.gravatar.com/avatar'
        hash = self.avatar_hash or self.gravatar_hash()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def __repr__(self):
        return '<User %r>' % self.username

class Department(db.Model):
    __tablename__ = 'deparements'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='deparement', lazy='dynamic')
                
    def __init__(self, **kwargs):
        super(Department, self).__init__(**kwargs)

    @staticmethod
    def insert_department():
        departments = {
            'HR 人資部門': [],
            'IT 資訊科技部門': [],
            'RD 研發部門': [],
            'PR 公關部門': [],
            '客服部': [],
            '行銷部': [],
            '培訓部': [],
            '銷售部': [],
            '行政部門': [],
            '會計部門': [],
        }
        for d in departments:
            department = Department.query.filter_by(name=d).first()
            if department is None:
                department = Department(name=d)
            db.session.add(department)
        db.session.commit()

    def __repr__(self):
        return '<LeaveType %r>' % self.name

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            'Staff': [Permission.ASK_LEAVE],
            'Supervisor': [Permission.ASK_LEAVE, Permission.PASS_LEAVE],
            'Administrator': [Permission.ASK_LEAVE, Permission.PASS_LEAVE,
                              Permission.EDIT_USER, Permission.ADMIN],
        }
        default_role = 'Staff'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self):
        return '<Role %r>' % self.name

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))