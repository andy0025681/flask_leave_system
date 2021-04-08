from datetime import datetime
from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from . import main
from .forms import MainForm, AskLeaveForm
from .. import db
from ..models import Permission, User, LeaveLogs

@main.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = MainForm()
    if form.validate_on_submit():
        pass
    return render_template('index.html')

@main.route('/askLeave/<username>', methods=['GET', 'POST'])
@login_required
def askLeave(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = AskLeaveForm(user)
    if current_user.can(Permission.ASK_LEAVE) and form.validate_on_submit():
        log = LeaveLogs(
                start=datetime.strptime("{} {}".format(form.startDate.data, form.startTime.data), "%Y-%m-%d %H:%M:%S"),
				end=datetime.strptime("{} {}".format(form.endDate.data, form.endTime.data), "%Y-%m-%d %H:%M:%S"),
				duration=8.0, reason=form.reason.data, type_id=form.leave_type.data, staff_id=user.id, agent_id=form.agents.data)
        db.session.add(log)
        db.session.commit()
        flash('Your leave request has been under review.')
        return redirect(url_for('.index'))
    return render_template('askLeave.html', form=form)