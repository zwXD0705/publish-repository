from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from .models import db, Activity, Registration
from .decorators import login_required, teacher_required

bp = Blueprint('activities', __name__)


@bp.route('/')
@login_required
def index():
    activities = Activity.query.order_by(Activity.start_time).all()
    return render_template('activities/index.html', activities=activities)


@bp.route('/activities/<int:activity_id>')
@login_required
def detail(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    reg = None
    if session.get('role') == 'student':
        reg = Registration.query.filter_by(
            activity_id=activity_id, student_id=session['user_id']).first()
    return render_template('activities/detail.html', activity=activity, reg=reg)


@bp.route('/activities/publish', methods=['GET', 'POST'])
@teacher_required
def publish():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        location = request.form.get('location', '').strip()
        detail = request.form.get('detail', '').strip()
        capacity = request.form.get('capacity', type=int)

        try:
            start_time = datetime.fromisoformat(request.form.get('start_time'))
            end_time = datetime.fromisoformat(request.form.get('end_time'))
            signup_deadline = datetime.fromisoformat(request.form.get('signup_deadline'))
        except (TypeError, ValueError):
            start_time = end_time = signup_deadline = None

        if not title or not location or start_time is None:
            flash('请填写活动名称、地点和开始时间', 'warning')
            return render_template('activities/publish.html', form=request.form)
        if capacity is None or capacity < 1:
            flash('人数上限至少为 1', 'warning')
            return render_template('activities/publish.html', form=request.form)
        if end_time <= start_time:
            flash('结束时间必须晚于开始时间', 'warning')
            return render_template('activities/publish.html', form=request.form)
        if signup_deadline >= start_time:
            flash('报名截止时间必须早于活动开始时间', 'warning')
            return render_template('activities/publish.html', form=request.form)
        if signup_deadline <= datetime.now():
            flash('报名截止时间必须晚于当前时间', 'warning')
            return render_template('activities/publish.html', form=request.form)

        activity = Activity(
            title=title, category=category, location=location, detail=detail,
            capacity=capacity, start_time=start_time, end_time=end_time,
            signup_deadline=signup_deadline, teacher_id=session['user_id'],
        )
        db.session.add(activity)
        db.session.commit()
        flash('活动发布成功', 'success')
        return redirect(url_for('activities.detail', activity_id=activity.id))

    return render_template('activities/publish.html')


@bp.route('/activities/<int:activity_id>/manage')
@teacher_required
def manage(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    if activity.teacher_id != session['user_id']:
        flash('只能管理自己发布的活动', 'warning')
        return redirect(url_for('activities.index'))
    registrations = Registration.query.filter_by(activity_id=activity_id).order_by(
        Registration.created_at).all()
    return render_template('activities/manage.html', activity=activity,
                           registrations=registrations)
