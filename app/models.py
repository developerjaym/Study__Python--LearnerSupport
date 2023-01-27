from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    auth_system_id = db.Column(db.Integer, unique=True)
    username = db.Column(db.String, unique=True)
    img = db.Column(db.String)
    email = db.Column(db.String)
