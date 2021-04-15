from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User, Gender, Department

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    password = PasswordField('New password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm new password',
                              validators=[DataRequired()])
    submit = SubmitField('Update Password')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    submit = SubmitField('Reset Password')

class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

class ChangeEmailForm(FlaskForm):
    email = StringField('New Email', validators=[DataRequired(), Length(1, 64),
                                                 Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Update Email Address')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered.')

class RegistrationForm(FlaskForm):
    email = StringField('電子郵件', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    username = StringField('帳號', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               '用戶名只能包含字母、數字、點或底線')])
    password = PasswordField('密碼', validators=[
        DataRequired(), EqualTo('password2', message='密碼必須匹配')])
    password2 = PasswordField('確認密碼', validators=[DataRequired()])
    department = SelectField('部門', coerce=int, validators=[DataRequired()])
    gender = SelectField('性別', choices=[(Gender.MALE, '男'),(Gender.FEMALE,'女')], coerce=int, validators=[DataRequired()])
    submit = SubmitField('新增用戶')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.department.choices = [(d.id, d.name)
                                    for d in Department.query.order_by(Department.id).all()]
    
    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('電子郵件已註冊')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('帳號已註冊')