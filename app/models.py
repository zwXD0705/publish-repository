from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # student / teacher
    real_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Activity(db.Model):
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), default='')
    location = db.Column(db.String(100), nullable=False)
    detail = db.Column(db.Text, default='')
    capacity = db.Column(db.Integer, nullable=False, default=50)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    signup_deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='open')
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    teacher = db.relationship('User', backref='activities')
    registrations = db.relationship(
        'Registration', backref='activity', cascade='all, delete-orphan')

    @property
    def state(self):
        """活动状态由时间自动驱动：报名中 -> 已截止 -> 已结束"""
        now = datetime.now()
        if self.end_time < now:
            return 'finished'
        if self.signup_deadline < now:
            return 'closed'
        return self.status

    @property
    def registered_count(self):
        return sum(1 for r in self.registrations if r.status in ('pending', 'approved'))


class Registration(db.Model):
    __tablename__ = 'registrations'
    __table_args__ = (
        db.UniqueConstraint('activity_id', 'student_id', name='uq_activity_student'),
    )

    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    # pending 待审核 / approved 已通过 / rejected 已驳回 / cancelled 已取消
    created_at = db.Column(db.DateTime, default=datetime.now)

    student = db.relationship('User', backref='registrations')
