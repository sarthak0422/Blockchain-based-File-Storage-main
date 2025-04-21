from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    files = db.relationship('File', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    blockchain_tx = db.Column(db.String(128))  # Stores blockchain transaction reference
    is_mined = db.Column(db.Boolean, default=False)  # Track if file is mined into blockchain