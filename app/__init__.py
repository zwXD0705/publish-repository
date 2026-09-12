import os

from flask import Flask

from .models import db
from . import auth, activities, registrations


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'campus-hub-v1-dev-key-change-me'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'CAMPUS_DATABASE_URI', 'sqlite:///campus.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(activities.bp)
    app.register_blueprint(registrations.bp)

    with app.app_context():
        db.create_all()

    return app
