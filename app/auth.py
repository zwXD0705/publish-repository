from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from .models import db, User

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        real_name = request.form.get('real_name', '').strip()
        role = request.form.get('role', 'student')
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        if not username or not real_name or not password:
            flash('请填写完整信息', 'warning')
            return render_template('auth/register.html', form=request.form)
        if role not in ('student', 'teacher'):
            role = 'student'
        if len(password) < 6:
            flash('密码长度至少 6 位', 'warning')
            return render_template('auth/register.html', form=request.form)
        if password != confirm:
            flash('两次输入的密码不一致', 'warning')
            return render_template('auth/register.html', form=request.form)
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'warning')
            return render_template('auth/register.html', form=request.form)

        user = User(username=username, real_name=real_name, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('用户名或密码错误', 'warning')
            return render_template('auth/login.html', form=request.form)

        session.clear()
        session['user_id'] = user.id
        session['role'] = user.role
        session['real_name'] = user.real_name
        flash('登录成功', 'success')
        return redirect(url_for('activities.index'))

    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    session.clear()
    flash('已退出登录', 'success')
    return redirect(url_for('auth.login'))
