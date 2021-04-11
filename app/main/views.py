from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, current_app, make_response
from flask_login import login_required, current_user
from . import main
from .forms import MainForm, EditProfileForm, EditProfileAdminForm, AskLeaveForm
from .. import db
from ..models import Permission, User, Role, LeaveLog, Time
from ..decorators import admin_required, permission_required

@main.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = MainForm()
    if form.validate_on_submit():
        pass
    return render_template('index.html')

@main.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)

@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)

@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)

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