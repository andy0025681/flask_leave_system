from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from . import main
from .forms import MainForm, AskLeaveForm
from .. import db
from ..models import Permission, User, LeaveLog

@main.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = MainForm()
    if form.validate_on_submit():
        pass
    return render_template('index.html')

@main.route('/askLeave', methods=['GET', 'POST'])
@login_required
def askLeave():
    form = AskLeaveForm(current_user._get_current_object())
    if current_user.can(Permission.ASK_LEAVE) and form.validate_on_submit():
        log = LeaveLog(
                start=datetime.strptime("{} {}".format(form.startDate.data, form.startTime.data), "%Y-%m-%d %H:%M:%S"),
				end=datetime.strptime("{} {}".format(form.endDate.data, form.endTime.data), "%Y-%m-%d %H:%M:%S"),
				duration=8.0, reason=form.reason.data, type_id=form.leave_type.data, staff_id=current_user.id, agent_id=form.agents.data)
        db.session.add(log)
        db.session.commit()
        flash('Your leave request has been under review.')
        return redirect(url_for('.askLeave'))
    return render_template('askLeave.html', form=form)

@main.route('/leaveLog', methods=['GET', 'POST'])
@login_required
def leaveLog():
    page = request.args.get('page', 1, type=int)
    pagination = current_user.ask_leave.order_by(LeaveLog.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_LEAVE_LOG_PER_PAGE'],
        error_out=False)
    leaveLogs = pagination.items
    return render_template('leaveLog.html', leaveLogs=leaveLogs, pagination=pagination)