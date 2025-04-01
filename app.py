import os
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename  
from flask_mysqldb import MySQL
from forms import RegistrationForm, LoginForm, UpdateProfileForm, UploadDocumentForm, ResetPasswordForm
from models import mysql, init_db, User
from config import Config
import MySQLdb
from MySQLdb.cursors import DictCursor

app = Flask(__name__)
app.config.from_object(Config)

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

init_db(app)

# Ensure the upload folder exists
if not os.path.exists(Config.UPLOAD_FOLDER):
    os.makedirs(Config.UPLOAD_FOLDER)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ✅ Modify the User class to include is_admin
class User(UserMixin):
    def __init__(self, id, username, email, is_admin=False):  
        self.id = id
        self.username = username
        self.email = email
        self.is_admin = is_admin  

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT id, username, email, is_admin FROM users WHERE id = %s", (user_id,))
    user_data = cur.fetchone()
    cur.close()

    if user_data:
        return User(
            id=user_data["id"],
            username=user_data["username"],
            email=user_data["email"],
            is_admin=bool(user_data["is_admin"])  # Ensure it's always True/False
        )
    return None

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        cur = mysql.connection.cursor(DictCursor)
        cur.execute("SELECT * FROM users WHERE email = %s", (form.email.data,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.check_password_hash(user["password_hash"], form.password.data):
            login_user(User(user["id"], user["username"], user["email"], user["is_admin"]))
            return redirect(url_for("dashboard"))
        else:
            flash("Login failed. Check your email and password.", "danger")

    return render_template("login.html", form=form)

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    (form.username.data, form.email.data, hashed_password))
        mysql.connection.commit()
        cur.close()
        flash("Account created! You can now log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = UpdateProfileForm()

    if request.method == "GET":
        form.username.data = current_user.username  # Prefill username field

    if form.validate_on_submit():
        cur = mysql.connection.cursor()
        cur.execute("SELECT password_hash FROM users WHERE id=%s", (current_user.id,))
        stored_password = cur.fetchone()["password_hash"]

        if bcrypt.check_password_hash(stored_password, form.password.data):
            cur.execute("UPDATE users SET username=%s WHERE id=%s", (form.username.data, current_user.id))
            mysql.connection.commit()
            cur.close()
            flash("Profile updated successfully!", "success")
            return redirect(url_for("profile"))
        else:
            flash("Incorrect password!", "danger")

    return render_template("update_profile.html", form=form)

@app.route("/reset_password", methods=["GET", "POST"])
@login_required
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.new_password.data).decode("utf-8")
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET password_hash=%s WHERE id=%s", (hashed_password, current_user.id))
        mysql.connection.commit()
        cur.close()

        flash("Password reset successful! Please log in again.", "success")
        logout_user()
        return redirect(url_for("login"))
    
    return render_template("reset_password.html", form=form)


@app.route("/dashboard")
@login_required
def dashboard():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT subject, grade FROM grades WHERE user_id = %s", (current_user.id,))
    grades_data = cur.fetchall()
    grades = {grade['subject']: grade['grade'] for grade in grades_data}
    cur.close()

    return render_template("dashboard.html", username=current_user.username, grades=grades)

@app.route("/update_grades", methods=["GET", "POST"])
@login_required
def update_grades():
    if not current_user.is_admin:
        flash("Unauthorized access!", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        user_id = request.form.get("user_id")
        subject = request.form.get("subject")
        grade = request.form.get("grade")

        # ✅ Debugging: Check if Flask is receiving the form data
        print(f"DEBUG: Received user_id={user_id}, subject={subject}, grade={grade}")

        if not user_id or not subject or not grade:
            flash("All fields are required!", "warning")
            return redirect(url_for("update_grades"))

        try:
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO grades (user_id, subject, grade) VALUES (%s, %s, %s) "
                "ON DUPLICATE KEY UPDATE grade = VALUES(grade)",
                (user_id, subject, grade),
            )
            mysql.connection.commit()
            cur.close()
            flash("Grade updated successfully!", "success")

            # ✅ Verify database update
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM grades WHERE user_id = %s", (user_id,))
            grades_debug = cur.fetchall()
            print(f"DEBUG: Grades after update: {grades_debug}")
            cur.close()

        except Exception as e:
            print(f"ERROR: {e}")
            flash("An error occurred while updating grades.", "danger")

        return redirect(url_for("update_grades"))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT id, username, email FROM users")
    users = cur.fetchall()

    cur.execute("SELECT user_id, subject, grade FROM grades")
    grades_data = cur.fetchall()
    grades_dict = {}
    for grade in grades_data:
        grades_dict.setdefault(grade["user_id"], []).append((grade["subject"], grade["grade"]))

    cur.close()
    
    return render_template("update_grades.html", users=users, grades=grades_dict)



@app.route("/logout")
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
