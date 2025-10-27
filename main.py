 
from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import db, User, Role, SitterService, ServiceType, Booking, BookingStatus, Payment, init_app
from datetime import datetime, date

# ---- Setting Constants ----

SYDNEY_SUBURBS = [
    "Alexandria", "Ashfield", "Balmain", "Bankstown", "Bondi", "Bondi Beach", "Bondi Junction",
    "Burwood", "Camperdown", "Canterbury", "Chatswood", "Coogee", "Cronulla", "Darlinghurst",
    "Darlington", "Drummoyne", "Dulwich Hill", "Edgecliff", "Enmore", "Erskineville", "Glebe",
    "Hurstville", "Kensington", "Kingsford", "Kirribilli", "Leichhardt", "Maroubra", "Marrickville",
    "Mascot", "Matraville", "Moore Park", "Newtown", "North Sydney", "Paddington", "Parramatta",
    "Potts Point", "Pyrmont", "Randwick", "Redfern", "Rockdale", "Rosebery", "Rozelle", "Rushcutters Bay",
    "Surry Hills", "Sydney CBD", "Ultimo", "Waterloo", "Waverley", "Woollahra", "Zetland"
]

# ---- App and Config ----
app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-change-me"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# Initialize database with app
init_app(app)



# ---- Database Routes ----
@app.route("/init-db")
def init_db():
    db.create_all()
    return "Database initialized!"

@app.route("/")
def home():
    return "SniffSnuff running. Hit /init-db once to create tables."

# ---- Dummy Routes ----

@app.route("/hello")
def hello():
    return "Hello World"

# ---- Login Routes ----

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            
            # STORE USER IN SESSION
            session['user_email'] = user.email
            session['user_id'] = user.id

            if user.role == Role.customer:
                return redirect(url_for("owner_dashboard")) 
            else:  
                return redirect(url_for("sitter_dashboard"))  
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

# ---- Register Routes ----

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        role_str = request.form.get("role")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))

        if not validate_email_format(email):
            flash("Your email does not have the correct format. Please try again.", "danger")
            return redirect(url_for("register"))
        
        if not validate_password_strength(password):
            flash("Your password doesn't comply with our security policy. Please try again.", "danger")
            return redirect(url_for("register"))

        user_role = Role.customer if role_str == "customer" else Role.sitter
        
        new_user = User(email=email, password=password, role=user_role)
        db.session.add(new_user)
        db.session.commit()

        flash(f"User {email} registered successfully!", "success")
        return redirect(url_for("register"))

    return render_template("register.html")


# ---- Helper functions to validate email and password ----

def validate_email_format(email):
    import re
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

def validate_password_strength(password):
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.isupper() for char in password):
        return False
    if not any(char.islower() for char in password):
        return False
    return True
    


# ---- Reset Database Routes ----

@app.route("/reset-db")
def reset_db():
    # Drop all tables
    db.drop_all()
    # Recreate all tables
    db.create_all()
    return "Database reset complete!"

# ---- Owner Dashboard ----


@app.route("/owner-dashboard", methods=["GET", "POST"])
def owner_dashboard():
    user = User.query.filter_by(email=session.get('user_email')).first()
    
    if request.method == "POST":
        # Update user profile
        user.first_name = request.form.get("first_name")
        user.last_name = request.form.get("last_name")
        user.phone = request.form.get("phone")
        user.suburb = request.form.get("suburb")
        user.city = request.form.get("city", "Sydney")  # Default to Sydney
        
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("owner_dashboard"))
    
    return render_template("owner_dashboard.html", user=user, suburbs=SYDNEY_SUBURBS)
    

# ---- Sitter Dashboard ----

@app.route("/sitter-dashboard", methods=["GET", "POST"])  
def sitter_dashboard():
    user = User.query.filter_by(email=session.get('user_email')).first()
    
    if request.method == "POST":
        # Check if it's profile update or service setup
        if "first_name" in request.form:
            # Update user profile
            user.first_name = request.form.get("first_name")
            user.last_name = request.form.get("last_name")
            user.phone = request.form.get("phone")
            user.suburb = request.form.get("suburb")
            user.city = request.form.get("city", "Sydney")
            
            db.session.commit()
            flash("Profile updated successfully!", "success")
        
        elif "boarding_rate" in request.form:
            # Setup sitter services
            setup_sitter_services(user)
            flash("Services setup successfully!", "success")
            
        return redirect(url_for("sitter_dashboard"))

    # Get existing services
    services = SitterService.query.filter_by(sitter_id=user.id).all()
    return render_template("sitter_dashboard.html", user=user, services=services, suburbs=SYDNEY_SUBURBS)

#---- Config Service per Sitter ----

def setup_sitter_services(user):
    """Create or update the 3 fixed services for a sitter"""
    services_data = [
        (ServiceType.boarding, float(request.form.get("boarding_rate"))),
        (ServiceType.daycare, float(request.form.get("daycare_rate"))),
        (ServiceType.walking, float(request.form.get("walking_rate")))
    ]
    
    for service_type, rate in services_data:
        # Check if service already exists
        existing_service = SitterService.query.filter_by(
            sitter_id=user.id, 
            service_type=service_type
        ).first()
        
        if existing_service:
            # Update existing service
            existing_service.fixed_rate = rate
        else:
            # Create new service
            new_service = SitterService(
                sitter_id=user.id,
                service_type=service_type,
                fixed_rate=rate,
                description=f"{service_type.value.title()} service"
            )
            db.session.add(new_service)
    
    db.session.commit()

#---- Sitter Inbox ----

@app.route("/sitter-inbox")
def sitter_inbox():
    # Get current user (sitter)
    sitter = User.query.filter_by(email=session.get('user_email')).first()
    
    # Get all bookings for this sitter
    bookings = Booking.query.filter_by(sitter_id=sitter.id).order_by(Booking.created_at.desc()).all()
    
    return render_template("sitter_inbox.html", bookings=bookings)

#---- Owner Bookings ----

@app.route("/owner-bookings")
def owner_bookings():
    # Get current user (owner)
    owner = User.query.filter_by(email=session.get('user_email')).first()
    
    # Get all bookings for this owner
    bookings = Booking.query.filter_by(owner_id=owner.id).order_by(Booking.created_at.desc()).all()
    
    return render_template("owner_bookings.html", bookings=bookings)

#---- Search Route ----

@app.route("/search")
def search():
    # Get search filters from URL parameters
    suburb = request.args.get("suburb", "")
    service_type = request.args.get("service_type", "")
    
    # Build the query
    query = SitterService.query.join(User).filter(
        SitterService.is_active == True,
        User.first_name.isnot(None)  # Only show sitters who completed profile
    )
    
    # Apply filters
    if suburb:
        query = query.filter(User.suburb == suburb)
    
    if service_type:
        query = query.filter(SitterService.service_type == ServiceType(service_type))
    
    # Get results
    sitter_services = query.all()
    
    return render_template("search.html", 
                         sitter_services=sitter_services, 
                         suburb=suburb, 
                         service_type=service_type,
                         suburbs=SYDNEY_SUBURBS)

#---- Booking Route ----

@app.route("/book-service/<int:sitter_id>", methods=["GET", "POST"])
def book_service(sitter_id):
    sitter = User.query.get_or_404(sitter_id)
    service_type = request.args.get("service_type")
    
    # Get the specific service
    service = SitterService.query.filter_by(
        sitter_id=sitter_id, 
        service_type=ServiceType(service_type)
    ).first_or_404()
    
    if request.method == "POST":
        # Get current user (owner)
        owner = User.query.filter_by(email=session.get('user_email')).first()
        
        # Create booking
        new_booking = Booking(
            owner_id=owner.id,
            sitter_id=sitter_id,
            service_id=service.id,
            start_date=datetime.strptime(request.form.get("start_date"), '%Y-%m-%d'),
            end_date=datetime.strptime(request.form.get("end_date"), '%Y-%m-%d'),
            fixed_amount=service.fixed_rate,
            pet_type=request.form.get("pet_type"),
            pet_name=request.form.get("pet_name"),
            special_instructions=request.form.get("special_instructions", "")
        )
        
        db.session.add(new_booking)
        db.session.commit()
        
        flash(f"Booking request sent to {sitter.first_name}!", "success")
        return redirect(url_for("owner_bookings"))
    
    return render_template("book_service.html", 
                         sitter=sitter, 
                         service=service, 
                         service_type=service_type,
                         now=datetime.now)

# ---- Update Booking Status ----

@app.route("/update-booking-status/<int:booking_id>", methods=["POST"])
def update_booking_status(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    new_status = request.form.get("status")
    
    booking.status = BookingStatus(new_status)
    booking.updated_at = datetime.utcnow()
    
    if new_status == 'confirmed':
        booking.confirmed_at = datetime.utcnow()
    
    db.session.commit()
    
    flash(f"Booking {new_status} successfully!", "success")
    return redirect(url_for("sitter_inbox"))


# ---- Run app ----
if __name__ == "__main__":
    app.run(debug=True)
