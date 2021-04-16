from flask import render_template, redirect, request, url_for, flash, make_response, current_app
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .. import db
from ..models import User
from ..email import send_email
from .forms import LoginForm, ChangePasswordForm, PasswordResetRequestForm, PasswordResetForm, ChangeEmailForm, RegistrationForm
from ..decorators import hr_required

@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        flash('無效的電子郵件或密碼。')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('你已登出。')
    return redirect(url_for('.login'))

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash('你的密碼已更新。')
            return redirect(url_for('main.index'))
        else:
            flash('無效的密碼。')
    return render_template("auth/change_password.html", form=form)

@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, 'Reset Your Password',
                       'auth/email/reset_password',
                       user=user, token=token)
        flash('已發送重置密碼電子郵件。')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)

@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        if User.reset_password(token, form.password.data):
            db.session.commit()
            flash('你的密碼已更新。')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)

@auth.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data.lower()
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, 'Confirm your email address',
                       'auth/email/change_email',
                       user=current_user, token=token)
            flash('已發送重置email地址的電子郵件。')
            return redirect(url_for('main.index'))
        else:
            flash('無效的電子郵件或密碼。')
    return render_template("auth/change_email.html", form=form)

@auth.route('/change_email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        db.session.commit()
        flash('你的電子郵件地址已更新。')
    else:
        flash('無效的請求。')
    return redirect(url_for('main.index'))

@auth.route('/edit-user', methods=['GET', 'POST'])
@login_required
@hr_required
def edit_user():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data.lower(),
                    username=form.username.data,
                    password=form.password.data,
                    department_id=form.department.data,
                    gender=form.gender.data)
        db.session.add(user)
        db.session.commit()
        send_email(user.email, '請假系統帳號',
                   'auth/email/new_user_email', form=form)
        flash('已新增帳號並發送通知郵件。')
        return redirect(url_for('auth.edit_user'))
    edit_user_status = request.cookies.get('edit_user_status', '')
    if edit_user_status == '1':
        page = request.args.get('page', 1, type=int)
        query=User.query
        pagination = query.order_by(User.id).paginate(
                    page, per_page=current_app.config['FLASKY_USER_PER_PAGE'],
                    error_out=False)
        users = pagination.items
        return render_template('auth/edit_user.html', edit_user_status=edit_user_status, users=users, pagination=pagination)
    return render_template('auth/edit_user.html', edit_user_status=edit_user_status, form=form)

@auth.route('/register')
@login_required
@hr_required
def show_register():
    resp = make_response(redirect(url_for('auth.edit_user')))
    resp.set_cookie('edit_user_status', '0', max_age=30*24*60*60)
    return resp

@auth.route('/allUser')
@login_required
@hr_required
def show_all_user():
    resp = make_response(redirect(url_for('auth.edit_user')))
    resp.set_cookie('edit_user_status', '1', max_age=30*24*60*60)
    return resp