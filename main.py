 
from flask import Flask, render_template, request, redirect, url_for, flash
from database import db, User, Role, init_app

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
            return render_template("customer_dash.html", user_email=user.email)
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

# ---- Run app ----
if __name__ == "__main__":
    app.run(debug=True)