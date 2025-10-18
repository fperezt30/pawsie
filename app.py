from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import enum

# ---- App and Config ----
app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-change-me"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---- Models ----
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

        user_role = Role.customer if role_str == "customer" else Role.sitter
        
        new_user = User(email=email, password=password, role=user_role)
        db.session.add(new_user)
        db.session.commit()

        flash(f"User {email} registered successfully!", "success")
        return redirect(url_for("register"))

    return render_template("register.html")


# ---- Run app ----
if __name__ == "__main__":
    app.run(debug=True)