from datetime import datetime, timedelta
import calendar
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, flash
from flask_login import UserMixin
from . import db, login_manager

class Permission:
    ASK_LEAVE = 1
    REVIEW_LEAVE = 2
    EDIT_USER = 4
    ADMIN = 8

class Gender:
    MALE = 1
    FEMALE = 2

class Status:
    UNDER_REVIEW = 1
    TURN_DOWN = 2
    AGREE = 4

class Time():
    # 日期間格。
    @staticmethod
    def dateInterval(start, end):
        if(start > end):
            return False
        year = end.year - start.year
        month = day = 0
        if(start.month > end.month):
            year -= 1
            month = (12 - start.month) + end.month
        else:
            month = end.month - start.month
        if(start.day > end.day):
            if(month > 0):
                month -= 1
            else:
                year -= 1
                month = 11
            if(end.month <= 1):
                day = (calendar.monthrange(end.year-1, 12)[1] - start.day) + end.day
            else:
                day = (calendar.monthrange(end.year, end.month-1)[1] - start.day) + end.day
        else:
            day = end.day - start.day
        # print("{}-{}-{}".format(year, month, day))
        return [year, month, day]

    # 日期重疊
    @staticmethod
    def dateOverlap(s1, e1, s2, e2):
        if s1 > e1 or s2 > e2:
            raise AttributeError('Dates are in wrong order.')
        if (s1 >= s2 and s1 <= e2) or (s1 <= s2 and e1 >= s2):
            return True
        return False

    # 是否為工作日。
    @staticmethod
    def workday():
        return True

    # 當日工時。
    @staticmethod
    def workingHours_day(start, end):
        fmt = '%H:%M:%S'
        st = datetime.strptime(start, fmt)
        et = datetime.strptime(end, fmt)
        noon = datetime.strptime('12:00:00', fmt)
        afterNoon = datetime.strptime('13:00:00', fmt)
        evening = datetime.strptime('18:00:00', fmt)
        if(st >= et or st > evening):
            raise AttributeError('Wrong time range.')
        elif(st < datetime.strptime('09:00:00', fmt)):
            st = datetime.strptime('09:00:00', fmt)
        if(st < noon):
            if(et < noon):
                return (et-st).seconds
            elif(et <= afterNoon):
                return (noon-st).seconds
            elif(et < evening):
                return (noon-st).seconds + (et-afterNoon).seconds
            else:
                return (noon-st).seconds + (evening-afterNoon).seconds
        else:
            if(st > afterNoon):
                if(et < evening):
                    return (et-st).seconds
                else:
                    return (evening-st).seconds
            else:
                if(et < evening):
                    return (et-afterNoon).seconds
                else:
                    return (evening-afterNoon).seconds
    
    # 期間工時。
    @staticmethod
    def workingHours_days(start, end):
        seconds = 0
        if(start >= end):
            raise AttributeError('Dates are in wrong order.')
        sd = date = datetime.strptime(start.strftime('%Y-%m-%d'), '%Y-%m-%d')
        ed = datetime.strptime(end.strftime('%Y-%m-%d'), '%Y-%m-%d')
        while(date <= ed):
            # if(not Time.workday() and (date.weekday() >= 5 and not Time.workday())):
            if(date.weekday() >= 5):
                date += timedelta(days=1)
                continue
            if(date == sd):
                if(sd == ed):
                    seconds += Time.workingHours_day(start.strftime('%H:%M:%S'), end.strftime('%H:%M:%S'))
                else:
                    seconds += Time.workingHours_day(start.strftime('%H:%M:%S'), '18:00:00')
            elif(date == ed):
                seconds += Time.workingHours_day('09:00:00', end.strftime('%H:%M:%S'))
            else:
                seconds += 8*60*60
            date += timedelta(days=1)
        return seconds

class OfficalLeave:
    # 計算年資，並轉為特休天數。
    @staticmethod
    def seniorityToLeave(start, end):
        seniority = Time.dateInterval(start, end)
        if(not seniority):
            return -1
        buf = [ False, 7, 10, 14, 14, # 0~4年
                15, 15, 15, 15, 15, # 5~9年
                16, 17, 18, 19, 20, # 10~14年
                21, 22, 23, 24, 25, # 15~19年
                26, 27, 28, 29, 30 ] # 20~24年以上
        if(seniority[0] >= 1):
            return buf[seniority[0]]
        else:
            return 3 if(seniority[1] > 0 or seniority[2] > 0) else 0

    # 年資比例: 用來計算特休比例。年資比例依照到職日劃分為上半年與下半年。
    @staticmethod
    def yearProportion(firstDay, seniorityRange):
        res = ((firstDay.month - 1) + (firstDay.day - 1) / calendar.monthrange(firstDay.year, firstDay.month)[1]) / seniorityRange
        return 1 if res > 1 else res
    
    # 以到職日計算某年特休開放日期。
    @staticmethod
    def startDate(firstDay, thatYear):
        if(firstDay >= datetime.strptime('{}-1-1'.format(thatYear+1), '%Y-%m-%d')):
            return False
        thatYear = datetime.strptime('{}-1-1'.format(thatYear), '%Y-%m-%d')
        month = firstDay.month+6
        year = firstDay.year
        if(month > 12):
            month -= 12
            year += 1
        firstOffStartDate = datetime.strptime('{}-{}-{}'.format(year, month, firstDay.day), '%Y-%m-%d')
        return thatYear if(firstOffStartDate < thatYear) else firstOffStartDate

    # 以到職日計算某年特休天數 (新年限定)
    @staticmethod
    def newYear(firstDay, thatYear):
        result = 0
        firstYear = datetime.strptime('{}-01-01'.format(thatYear), '%Y-%m-%d')
        if(firstDay > firstYear):
            return False
        nextYear = thatYear + 1
        # 去年開始的年資的下半部分
        offLeave = OfficalLeave.seniorityToLeave(firstDay, firstYear)
        seniorityRange = 6 if offLeave <= 3 else 12
        lastOffLeave = OfficalLeave.yearProportion(firstDay, seniorityRange) * offLeave
        result += lastOffLeave
        # 今年開始的年資的上半部分
        offLeave = OfficalLeave.seniorityToLeave(firstDay, firstYear) \
            if(firstDay.month == 1 and firstDay.day == 1) \
                else OfficalLeave.seniorityToLeave(firstDay, datetime.strptime('{}-01-01'.format(nextYear), '%Y-%m-%d'))
        seniorityRange = 6 if offLeave <= 3 else 12
        thisOffLeave = offLeave - (OfficalLeave.yearProportion(firstDay, seniorityRange) * offLeave)
        result += thisOffLeave
        result = round(round(round(result, 3), 2), 1)
        return [datetime.strptime('{}-01-01'.format(thatYear), '%Y-%m-%d'), datetime.strptime('{}-12-31'.format(thatYear), '%Y-%m-%d'), result]

    # 以到職日計算當年計算特休天數 (新員工限定)
    @staticmethod
    def newStaff(firstDay):
        start = OfficalLeave.startDate(firstDay, firstDay.year)
        end = datetime.strptime('{}-12-31'.format(firstDay.year), '%Y-%m-%d')
        if(start > end):
            return [False, False, 0]
        thisYear = datetime.strptime('{}-12-31'.format(firstDay.year), '%Y-%m-%d')
        # 今年開始的年資的上半部分
        offLeave = OfficalLeave.seniorityToLeave(firstDay, thisYear)
        seniorityRange = 6 if offLeave <= 3 else 12
        result = offLeave - (OfficalLeave.yearProportion(firstDay, seniorityRange) * offLeave)
        result = round(round(round(result, 3), 2), 1)
        return [start, end, result]

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
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('leave_types.id'))
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    agent_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def update_status(self, status):
        if status != Status.TURN_DOWN and status != Status.AGREE:
            flash('The review leave link is invalid or has expired.')
            return False
        elif self.status == status:
            flash('Leave status unchanged.')
            return False
        else:
            if self.status == Status.UNDER_REVIEW or self.status == Status.TURN_DOWN:
                if status == Status.AGREE:
                    if self.type.name == '特休假':
                        if (self.duration/8.0) > self.staff.officalLeave:
                            flash('Insufficient vacation.')
                            return False
                        self.staff.officalLeave = round(self.staff.officalLeave - self.duration/8, 1)
            elif self.status == Status.AGREE and status == Status.TURN_DOWN:
                if self.type.name == '特休假':
                    self.staff.officalLeave = round(self.staff.officalLeave + self.duration/8, 1)
            self.status = status
        return True

    def __init__(self, **kwargs):
        super(LeaveLog, self).__init__(**kwargs)
        if self.status is None:
            self.status = Status.UNDER_REVIEW

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    password_hash = db.Column(db.String(128))
    firstDay = db.Column(db.DateTime)
    off_leave_start = db.Column(db.DateTime)
    off_leave_end = db.Column(db.DateTime)
    officalLeave = db.Column(db.Float)
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
        self.firstDay = datetime.strptime(datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d')
        self.off_leave_start, self.off_leave_end, self.officalLeave = OfficalLeave.newStaff(self.firstDay)
    
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

    def generate_review_leave_token(self, leaveLog, status, expiration=3600*8):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'admin_id': self.id, 'leaveLog': leaveLog.id, 'status': status}).decode('utf-8')
    
    def review_leave(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            flash('The review leave link is invalid or has expired.')
            return False
        if data.get('admin_id') != self.id:
            flash('The review leave link is invalid or has expired.')
            return False
        leaveLog = LeaveLog.query.filter_by(id=data.get('leaveLog')).first()
        if leaveLog is None:
            flash('The review leave link is invalid or has expired.')
            return False
        if not leaveLog.update_status(data.get('status')):
            return False
        db.session.add(leaveLog)
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
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='department', lazy='dynamic')
    leaveLogs = db.relationship('LeaveLog', backref='department', lazy='dynamic')
                
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

    def supervisor(self):
        for user in self.users:
            if user.can(Permission.REVIEW_LEAVE):
                return user
        return False

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
            'Supervisor': [Permission.ASK_LEAVE, Permission.REVIEW_LEAVE],
            'Administrator': [Permission.ASK_LEAVE, Permission.REVIEW_LEAVE,
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