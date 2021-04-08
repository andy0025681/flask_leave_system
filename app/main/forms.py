from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField
from wtforms.fields.html5 import DateField, TimeField
from wtforms.validators import DataRequired, Length, Email, Regexp
from ..models import LeaveTypes, Department, User

class MainForm(FlaskForm):
    pass

class AskLeaveForm(FlaskForm):
    leave_type = SelectField('假別:', coerce=int, validators=[DataRequired()])
    agents = SelectField('職務代理人:', coerce=int, validators=[DataRequired()])
    startDate = DateField('起始日期:', default=datetime.today(), validators=[DataRequired()])
    startTime = TimeField('結束時間:', default=datetime.now(), validators=[DataRequired()])
    endDate = DateField('結束日期:', default=datetime.today(), validators=[DataRequired()])
    endTime = TimeField('結束時間:', default=datetime.now(), validators=[DataRequired()])
    reason = TextAreaField('請假原因:', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(AskLeaveForm, self).__init__(*args, **kwargs)
        self.leave_type.choices = [(t.id, t.name)
                                    for t in LeaveTypes.query.order_by(LeaveTypes.id).all()
                                    if t.has_permission(user.gender)]
        self.agents.choices = [(u.id, u.username)
                                for u in User.query.filter_by(department_id=user.department_id).all()
                                if u.id != user.id]
        self.user = user