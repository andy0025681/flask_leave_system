from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField
from wtforms.fields.html5 import DateField, TimeField
from wtforms.validators import DataRequired, Length, Email, Regexp
from wtforms import ValidationError
from flask_pagedown.fields import PageDownField
from ..models import LeaveType, Department, User, Role

class EditProfileForm(FlaskForm):
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Usernames must have only letters, numbers, dots or '
               'underscores')])
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')

class AskLeaveForm(FlaskForm):
    leave_type = SelectField('假別:', coerce=int, validators=[DataRequired()])
    agents = SelectField('職務代理人:', coerce=int, validators=[DataRequired()])
    startDate = DateField('起始日期:', default=datetime.today(), validators=[DataRequired()])
    startTime = TimeField('起始時間:', default=datetime.strptime('09:00:00', '%H:%M:%S'), validators=[DataRequired()])
    endDate = DateField('結束日期:', default=datetime.today(), validators=[DataRequired()])
    endTime = TimeField('結束時間:', default=datetime.strptime('18:00:00', '%H:%M:%S'), validators=[DataRequired()])
    reason = TextAreaField('請假原因:', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(AskLeaveForm, self).__init__(*args, **kwargs)
        self.leave_type.choices = [(t.id, t.name)
                                    for t in LeaveType.query.order_by(LeaveType.id).all()
                                    if t.has_permission(user.gender)]
        self.agents.choices = [(u.id, u.username)
                                for u in User.query.filter_by(department_id=user.department_id).all()
                                if u.id != user.id]
        self.user = user

class WorkHolidayForm(FlaskForm):
    workday = SelectField('事件', coerce=int, choices=[(0, '放假'), (1, '上班')])
    startDate = DateField('起始日期:', default=datetime.today(), validators=[DataRequired()])
    endDate = DateField('結束日期:', default=datetime.today(), validators=[DataRequired()])
    reason = TextAreaField('原因:', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def validate_startDate(self, field):
        if datetime.strptime("{}".format(self.startDate.data), "%Y-%m-%d") > datetime.strptime("{}".format(self.endDate.data), "%Y-%m-%d"):
            raise ValidationError('日期順序錯誤')

class PostForm(FlaskForm):
    body = PageDownField("有什麼想說的嗎?", validators=[DataRequired()])
    submit = SubmitField('Submit')

class CommentForm(FlaskForm):
    body = StringField('輸入你的評論', validators=[DataRequired()])
    submit = SubmitField('Submit')
