from functools import wraps

from flask import session, redirect, url_for, flash


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            flash('请先登录', 'warning')
            return redirect(url_for('auth.login'))
        return view(*args, **kwargs)
    return wrapped


def teacher_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            flash('请先登录', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'teacher':
            flash('该操作仅教师可用', 'warning')
            return redirect(url_for('activities.index'))
        return view(*args, **kwargs)
    return wrapped


def student_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            flash('请先登录', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'student':
            flash('该操作仅学生可用', 'warning')
            return redirect(url_for('activities.index'))
        return view(*args, **kwargs)
    return wrapped
