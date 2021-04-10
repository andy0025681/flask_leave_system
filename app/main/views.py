from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, current_app, make_response
from flask_login import login_required, current_user
from . import main
from .forms import MainForm, AskLeaveForm
from .. import db
from ..models import Permission, User, LeaveLog, Time

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
        start = datetime.strptime("{} {}".format(form.startDate.data, form.startTime.data), "%Y-%m-%d %H:%M:%S")
        end=datetime.strptime("{} {}".format(form.endDate.data, form.endTime.data), "%Y-%m-%d %H:%M:%S")
        log = LeaveLog( start=start, end=end, duration=round(Time.workingHours_days(start, end)/3600, 2), 
                        reason=form.reason.data, type_id=form.leave_type.data, staff_id=current_user.id, agent_id=form.agents.data)
        db.session.add(log)
        db.session.commit()
        flash('Your leave request has been under review.')
        return redirect(url_for('.askLeave'))
    return render_template('askLeave.html', form=form)

@main.route('/leaveLog', methods=['GET', 'POST'])
@login_required
def leaveLog():
    page = request.args.get('page', 1, type=int)
    agent_record = False
    agent_record = bool(request.cookies.get('agent_record', ''))
    if agent_record:
        query = current_user.agent
    else:
        query = current_user.ask_leave
    pagination = query.order_by(LeaveLog.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_LEAVE_LOG_PER_PAGE'],
        error_out=False)
    leaveLogs = pagination.items
    return render_template('leaveLog.html', leaveLogs=leaveLogs, agent_record=agent_record, pagination=pagination)

@main.route('/agent')
@login_required
def show_agent_record():
    resp = make_response(redirect(url_for('.leaveLog')))
    resp.set_cookie('agent_record', '', max_age=30*24*60*60)
    return resp

@main.route('/leave')
@login_required
def show_leave_log():
    resp = make_response(redirect(url_for('.leaveLog')))
    resp.set_cookie('agent_record', '1', max_age=30*24*60*60)
    return resp