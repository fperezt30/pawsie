from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import enum
from flask_bcrypt import Bcrypt

#--Initialize the Bcrypt instance--#

bcrypt = Bcrypt()

#--Initialize the SQLAlchemy instance--#

db = SQLAlchemy()

#--Enum working with Flask-SQLAlchemy as CHECK CONSTRAINTS in the DB--#

class Role(enum.Enum):
    customer = "customer"
    sitter = "sitter"

class ServiceType(enum.Enum):
    walking = "walking"
    boarding = "boarding"
    daycare = "daycare"
    home_visit = "home_visit"
    grooming = "grooming"

class BookingStatus(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"
    completed = "completed"

#--User table is created with Class based model--#

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False, default=Role.customer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Personal details (to be filled later in dashboard)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    city = db.Column(db.String(100))
    suburb = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationships
    sitter_services = db.relationship('SitterService', backref='sitter', lazy=True)
    owner_bookings = db.relationship('Booking', foreign_keys='Booking.owner_id', backref='owner', lazy=True)
    sitter_bookings = db.relationship('Booking', foreign_keys='Booking.sitter_id', backref='sitter', lazy=True)

    def __init__(self, email, password, role=Role.customer):
        self.email = email
        self.password = password
        self.role = role


#--Sitter Services table is created with Class based model--#

class SitterService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sitter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_type = db.Column(db.Enum(ServiceType), nullable=False)
    # Fixed rates 
    fixed_rate = db.Column(db.Float, nullable=False)  # Fixed price for this service
    # Service description
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships
    bookings = db.relationship('Booking', backref='service', lazy=True)


#--Bookings table is created with Class based model--#

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sitter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('sitter_service.id'), nullable=False)
    status = db.Column(db.Enum(BookingStatus), default=BookingStatus.pending)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_days = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    pet_type = db.Column(db.String(100), nullable=False)
    pet_name = db.Column(db.String(100), nullable=False)
    special_instructions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)


#--Payments table is created with Class based model--#

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), default="credit_card")
    payment_status = db.Column(db.String(50), default="completed")
    transaction_id = db.Column(db.String(100))
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)

#--Function to initialize the database with the Flask app--#

def init_app(app):
    db.init_app(app)
    bcrypt.init_app(app)  