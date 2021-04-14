from datetime import datetime
from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response
from flask_login import login_required, current_user
from . import main
from .forms import MainForm, EditProfileForm, EditProfileAdminForm, AskLeaveForm
from .. import db
from ..models import Permission, User, Role, LeaveLog, Time, Status
from ..email import send_email
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
        for i in LeaveLog.query.filter_by(staff_id=current_user.id):
            if Time.dateOverlap(start, end, i.start, i.end):
                flash('Your leave date is overlap.')
                return redirect(url_for('.askLeave'))
        log = LeaveLog( start=start, end=end, reason=form.reason.data, 
                        department_id=current_user.department_id, type_id=form.leave_type.data, 
                        staff_id=current_user.id, agent_id=form.agents.data)
        db.session.add(log)
        db.session.commit()
        reviewer = current_user.department.supervisor() \
            if not current_user.can(Permission.REVIEW_LEAVE) and current_user.department.supervisor() \
                else User.query.filter_by(email=current_app.config['FLASKY_ADMIN']).first_or_404()
        agree_token = reviewer.generate_review_leave_token(log, Status.AGREE)
        turn_down_token = reviewer.generate_review_leave_token(log, Status.TURN_DOWN)
        send_email(reviewer.email, '請假申請函',
                   'email/askLeave', user=reviewer, applicant=current_user, leaveLog=log, agree_token=agree_token, turn_down_token=turn_down_token)
        flash('Your leave request has been under review.')
        return redirect(url_for('.askLeave'))
    return render_template('askLeave.html', form=form)

@main.route('/reviewLeave/<token>')
@login_required
def reviewLeave(token):
    if current_user.review_leave(token):
        db.session.commit()
        flash('You have updated the vacation log. Thanks!')
    return redirect(url_for('main.index'))

@main.route('/leaveLog', methods=['GET', 'POST'])
@login_required
def leaveLog():
    page = request.args.get('page', 1, type=int)
    log_status = request.cookies.get('log_status', '')
    if log_status == '0':
        query = LeaveLog.query
    elif log_status == '1':
        query = current_user.ask_leave
    elif log_status == '2':
        query = current_user.agent
    else:
        query = current_user.department.leaveLogs
    pagination = query.order_by(LeaveLog.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_LEAVE_LOG_PER_PAGE'],
        error_out=False)
    leaveLogs = pagination.items
    return render_template('leaveLog.html', leaveLogs=leaveLogs, log_status=log_status, pagination=pagination)

@main.route('/allLog')
@login_required
@admin_required
def show_all_log():
    resp = make_response(redirect(url_for('.leaveLog')))
    resp.set_cookie('log_status', '0', max_age=30*24*60*60)
    return resp

@main.route('/selfLog')
@login_required
def show_self_log():
    resp = make_response(redirect(url_for('.leaveLog')))
    resp.set_cookie('log_status', '1', max_age=30*24*60*60)
    return resp

@main.route('/agentLog')
@login_required
def show_agent_log():
    resp = make_response(redirect(url_for('.leaveLog')))
    resp.set_cookie('log_status', '2', max_age=30*24*60*60)
    return resp

@main.route('/departmentLog')
@login_required
def show_department_log():
    if not current_user.can(Permission.REVIEW_LEAVE):
        abort(403)
    resp = make_response(redirect(url_for('.leaveLog')))
    resp.set_cookie('log_status', '3', max_age=30*24*60*60)
    return resp