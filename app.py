import os, sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, g, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-deployment")
DATABASE = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "requests.db"))

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'citizen'
        );
        CREATE TABLE IF NOT EXISTS service_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            service TEXT NOT NULL,
            subject TEXT NOT NULL,
            details TEXT NOT NULL,
            location TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Submitted',
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """)
        # Demo administrator. Change password after first login in a real deployment.
        conn.execute("INSERT OR IGNORE INTO users(name,email,password,role) VALUES(?,?,?,?)",
                     ("System Administrator", "admin@example.com", generate_password_hash("Admin123!"), "admin"))

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Administrator access is required.", "warning")
            return redirect(url_for("dashboard"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name and email, and use a password of at least 8 characters.", "danger")
            return render_template("register.html")
        try:
            cur = db().execute("INSERT INTO users(name,email,password) VALUES(?,?,?)",
                               (name, email, generate_password_hash(password)))
            db().commit()
            session.update(user_id=cur.lastrowid, name=name, email=email, role="citizen")
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            flash("That email is already registered. Please sign in.", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session.update(user_id=user["id"], name=user["name"], email=user["email"], role=user["role"])
            return redirect(url_for("admin_dashboard") if user["role"] == "admin" else url_for("dashboard"))
        flash("Incorrect email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have signed out.", "success")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    rows = db().execute("SELECT * FROM service_requests WHERE user_id=? ORDER BY id DESC",
                        (session["user_id"],)).fetchall()
    return render_template("dashboard.html", requests=rows)

@app.route("/requests/new", methods=["GET", "POST"])
@login_required
def new_request():
    if request.method == "POST":
        service = request.form.get("service", "").strip()
        subject = request.form.get("subject", "").strip()
        details = request.form.get("details", "").strip()
        location = request.form.get("location", "").strip()
        if not all([service, subject, details, location]):
            flash("Please complete every field.", "danger")
            return render_template("new_request.html")
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        reference = f"PSR-{stamp}-{session['user_id']}"
        db().execute("""INSERT INTO service_requests
            (reference,user_id,service,subject,details,location,status,created_at)
            VALUES(?,?,?,?,?,?,?,?)""",
            (reference, session["user_id"], service, subject, details, location,
             "Submitted", datetime.now().strftime("%d %b %Y, %H:%M")))
        db().commit()
        flash(f"Request submitted successfully. Your reference is {reference}.", "success")
        return redirect(url_for("dashboard"))
    return render_template("new_request.html")

@app.route("/track", methods=["GET", "POST"])
def track():
    result = None
    if request.method == "POST":
        ref = request.form.get("reference", "").strip().upper()
        result = db().execute("""SELECT service_requests.*, users.name AS applicant
            FROM service_requests JOIN users ON users.id=service_requests.user_id
            WHERE reference=?""", (ref,)).fetchone()
        if result is None:
            flash("No request found for that reference number.", "warning")
    return render_template("track.html", result=result)

@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    rows = db().execute("""SELECT service_requests.*, users.name AS applicant, users.email
        FROM service_requests JOIN users ON users.id=service_requests.user_id
        ORDER BY service_requests.id DESC""").fetchall()
    counts = {s: db().execute("SELECT COUNT(*) FROM service_requests WHERE status=?", (s,)).fetchone()[0]
              for s in ["Submitted", "In Progress", "Resolved", "Rejected"]}
    return render_template("admin.html", requests=rows, counts=counts)

@app.route("/admin/request/<int:request_id>", methods=["POST"])
@login_required
@admin_required
def update_request(request_id):
    status = request.form.get("status", "")
    allowed = {"Submitted", "In Progress", "Resolved", "Rejected"}
    if status in allowed:
        db().execute("UPDATE service_requests SET status=? WHERE id=?", (status, request_id))
        db().commit()
        flash("Request status updated.", "success")
    return redirect(url_for("admin_dashboard"))

@app.context_processor
def inject_user():
    return {"current_user": session}

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
