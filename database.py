from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import enum

db = SQLAlchemy()

class Role(enum.Enum):
    customer = "customer"
    sitter = "sitter"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False, default=Role.customer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, email, password, role=Role.customer):
        self.email = email
        self.password = password
        self.role = role

def init_app(app):
    db.init_app(app)