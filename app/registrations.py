from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from sqlalchemy.exc import IntegrityError

from .models import db, Activity, Registration
from .decorators import student_required, teacher_required

bp = Blueprint('registrations', __name__, url_prefix='/registrations')


def active_count(activity_id):
    """当前有效报名数（待审核 + 已通过），用于报名阶段的人数封顶"""
    return Registration.query.filter(
        Registration.activity_id == activity_id,
        Registration.status.in_(['pending', 'approved']),
    ).count()


def approved_count(activity_id):
    """已通过人数，用于审核阶段的人数封顶"""
    return Registration.query.filter(
        Registration.activity_id == activity_id,
        Registration.status == 'approved',
    ).count()


@bp.route('/<int:activity_id>/signup', methods=['POST'])
@student_required
def signup(activity_id):
    activity = Activity.query.get_or_404(activity_id)

    if activity.state != 'open':
        flash('该活动当前不可报名', 'warning')
        return redirect(url_for('activities.detail', activity_id=activity_id))
    if active_count(activity_id) >= activity.capacity:
        flash('该活动人数已满，无法报名', 'warning')
        return redirect(url_for('activities.detail', activity_id=activity_id))

    exists = Registration.query.filter_by(
        activity_id=activity_id, student_id=session['user_id']).first()
    if exists and exists.status != 'cancelled':
        flash('你已报名该活动，请勿重复报名', 'warning')
        return redirect(url_for('activities.detail', activity_id=activity_id))

    reg = Registration(activity_id=activity_id, student_id=session['user_id'])
    db.session.add(reg)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('你已报名该活动，请勿重复报名', 'warning')
        return redirect(url_for('activities.detail', activity_id=activity_id))

    flash('报名成功，等待教师审核', 'success')
    return redirect(url_for('registrations.my'))


@bp.route('/<int:activity_id>/cancel', methods=['POST'])
@student_required
def cancel(activity_id):
    reg = Registration.query.filter_by(
        activity_id=activity_id, student_id=session['user_id']).first()
    if reg and reg.status == 'pending':
        reg.status = 'cancelled'
        db.session.commit()
        flash('已取消报名', 'success')
    else:
        flash('仅待审核状态的报名可以取消', 'warning')
    return redirect(url_for('registrations.my'))


@bp.route('/my')
@student_required
def my():
    registrations = Registration.query.filter_by(
        student_id=session['user_id']).order_by(Registration.created_at.desc()).all()
    return render_template('registrations/my.html', registrations=registrations)


@bp.route('/<int:activity_id>/review', methods=['POST'])
@teacher_required
def review(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    if activity.teacher_id != session['user_id']:
        flash('只能管理自己发布的活动', 'warning')
        return redirect(url_for('activities.index'))

    reg = Registration.query.get(request.form.get('registration_id', type=int))
    action = request.form.get('action', '')
    if reg is None or reg.activity_id != activity_id:
        flash('报名记录不存在', 'warning')
        return redirect(url_for('activities.manage', activity_id=activity_id))

    if action == 'approve':
        if approved_count(activity_id) >= activity.capacity:
            flash('该活动已通过人数已满，无法继续通过', 'warning')
            return redirect(url_for('activities.manage', activity_id=activity_id))
        reg.status = 'approved'
        flash('已通过该学生报名', 'success')
    elif action == 'reject':
        reg.status = 'rejected'
        flash('已驳回该学生报名', 'success')
    else:
        flash('未知操作', 'warning')
        return redirect(url_for('activities.manage', activity_id=activity_id))

    db.session.commit()
    return redirect(url_for('activities.manage', activity_id=activity_id))
