import os
import json
import razorpay
from datetime import datetime, timedelta
from io import BytesIO
from functools import wraps

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import types
from PIL import Image

# --- Config & Setup ---
load_dotenv()
app = Flask(__name__)

# Security & DB Config
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dev-secret-key")
# Defaults to SQLite. Change to your MySQL URL for production.
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///nutriscan_saas.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize APIs
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Robust Model Selection
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
    except:
        model = genai.GenerativeModel("gemini-2.5-flash")
    
    # Text model for diet plans
    text_model = genai.GenerativeModel("gemini-2.5-flash")

# Initialize Razorpay
razorpay_client = None
if os.getenv("RAZORPAY_KEY_ID"):
    razorpay_client = razorpay.Client(auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET")))

# Initialize DB & Login
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- Custom Admin Decorator ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- JSON SCHEMAS ---
NUTRIENT_SCHEMA = {
    "type": "object",
    "properties": {
        "protein_g": {"type": "integer"},
        "carbs_g": {"type": "integer"},
        "fat_g": {"type": "integer"},
        "cholesterol_mg": {"type": "integer"},
        "sodium_mg": {"type": "integer"},
        "vitamin_c_mg": {"type": "integer"}
    },
    "required": ["protein_g", "carbs_g", "fat_g"]
}

CALORIE_SCHEMA = {
    "type": "object",
    "properties": {
        "total_calories": {"type": "integer"},
        "total_nutrients": NUTRIENT_SCHEMA,
        "analysis_notes": {"type": "string"}
    },
    "required": ["total_calories", "total_nutrients", "analysis_notes"]
}

# --- Database Models ---

# 1. Site Configuration (NEW MODEL - Was Missing)
class SiteConfig(db.Model):
    __tablename__ = 'site_config'
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), default="NutriScan AI")
    support_email = db.Column(db.String(150), default="support@nutriscan.com")
    allow_registrations = db.Column(db.Boolean, default=True)
    maintenance_mode = db.Column(db.Boolean, default=False)
    default_trial_days = db.Column(db.Integer, default=7)

# 2. User Model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Access Control
    is_admin = db.Column(db.Boolean, default=False)
    is_active_account = db.Column(db.Boolean, default=True)

    # Subscription
    trial_start = db.Column(db.DateTime, default=datetime.utcnow)
    is_premium = db.Column(db.Boolean, default=False)
    premium_expiry = db.Column(db.DateTime, nullable=True)

    # Health Profile
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    current_weight = db.Column(db.Float, nullable=True)
    height = db.Column(db.Float, nullable=True)
    activity_level = db.Column(db.String(20), default="sedentary")
    goal = db.Column(db.String(50), default="maintain")
    
    # Calculated Data
    daily_calorie_limit = db.Column(db.Integer, default=2000)
    saved_diet_plan = db.Column(db.Text, nullable=True)

    def get_status(self):
        if self.is_premium: return "Premium"
        days_left = 7 - (datetime.utcnow() - self.trial_start).days
        return f"Trial ({max(0, days_left)} days)" if days_left > 0 else "Expired"

    def can_access_ai(self):
        if self.is_premium: return True
        return (datetime.utcnow() - self.trial_start).days < 7

# 3. Food Log Model
class FoodLog(db.Model):
    __tablename__ = 'food_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    food_name = db.Column(db.String(255)) 
    calories = db.Column(db.Integer) 
    protein = db.Column(db.Integer)
    carbs = db.Column(db.Integer)
    fat = db.Column(db.Integer)
    
    user = db.relationship('User', backref=db.backref('logs', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Helper Functions ---
def convert_image_to_part(image_file):
    image_data = image_file.read()
    image_file.seek(0)
    return {"mime_type": "image/jpeg", "data": image_data}

def get_calorie_estimation(image_part):
    prompt = "Analyze this food image. Return JSON with total_calories, analysis_notes (summary), and total_nutrients (protein_g, carbs_g, fat_g)."
    try:
        response = model.generate_content(
            contents=[image_part, prompt],
            generation_config=types.GenerationConfig(
                response_mime_type="application/json",
                response_schema=CALORIE_SCHEMA,
                temperature=0.1
            )
        )
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e)}

# --- Routes ---

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Check if registration is allowed (from settings)
        config = SiteConfig.query.first()
        if config and not config.allow_registrations:
            flash("New registrations are currently disabled by the administrator.", "error")
            return render_template("register.html")

        if User.query.filter_by(email=request.form.get("email")).first():
            flash("Email taken", "error")
        else:
            hashed_pw = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256')
            new_user = User(username=request.form.get("username"), email=request.form.get("email"), password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('dashboard'))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form.get("email")).first()
        if user and check_password_hash(user.password, request.form.get("password")):
            
            # Check if active
            if not user.is_active_account:
                flash("Your account has been deactivated. Contact Admin.", "error")
                return redirect(url_for('login'))

            login_user(user)
            
            # Check for Maintenance Mode (Allow Admins only)
            config = SiteConfig.query.first()
            if config and config.maintenance_mode and not user.is_admin:
                logout_user()
                flash("System is currently in Maintenance Mode. Please try again later.", "error")
                return redirect(url_for('login'))

            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        flash("Invalid credentials", "error")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/dashboard")
@login_required
def dashboard():
    logs = FoodLog.query.filter_by(user_id=current_user.id).order_by(FoodLog.date.desc()).all()
    today_cals = sum(l.calories for l in logs if l.date.date() == datetime.utcnow().date())
    rzp_key = os.getenv("RAZORPAY_KEY_ID", "")
    return render_template("dashboard.html", user=current_user, logs=logs, today_cals=today_cals, rzp_key=rzp_key)

# --- ADMIN ROUTES ---
@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    premium_users = User.query.filter_by(is_premium=True).count()
    total_scans = FoodLog.query.count()
    total_revenue = premium_users * 99 
    
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_users_count = db.session.query(FoodLog.user_id).filter(FoodLog.date >= thirty_days_ago).distinct().count()
    
    avg_scans = round(total_scans / total_users, 1) if total_users > 0 else 0
    conversion_rate = round((premium_users / total_users * 100), 1) if total_users > 0 else 0

    all_users = User.query.order_by(User.created_at.desc()).all()
    recent_logs = FoodLog.query.order_by(FoodLog.date.desc()).limit(20).all()

    return render_template(
        "admin.html", 
        user=current_user,
        total_users=total_users,
        premium_users=premium_users,
        total_scans=total_scans,
        total_revenue=total_revenue,
        active_users=active_users_count,
        avg_scans=avg_scans,
        conversion_rate=conversion_rate,
        all_users=all_users,
        recent_logs=recent_logs
    )

@app.route("/admin/toggle_status/<int:user_id>")
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get(user_id)
    if user:
        if user.id == current_user.id:
            flash("You cannot deactivate yourself!", "error")
        else:
            user.is_active_account = not user.is_active_account
            db.session.commit()
            status = "Activated" if user.is_active_account else "Deactivated"
            flash(f"User {user.username} has been {status}.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/profile", methods=["GET", "POST"])
@login_required
@admin_required
def admin_profile():
    if "update_info" in request.form:
        username = request.form.get("username")
        email = request.form.get("email")
        if not username or not email:
            flash("Username and Email are required.", "error")
        else:
            existing = User.query.filter_by(email=email).first()
            if existing and existing.id != current_user.id:
                flash("Email already in use.", "error")
            else:
                current_user.username = username
                current_user.email = email
                db.session.commit()
                flash("Profile details updated successfully!", "success")

    elif "update_password" in request.form:
        current_pw = request.form.get("current_password")
        new_pw = request.form.get("new_password")
        confirm_pw = request.form.get("confirm_password")

        if not current_pw or not new_pw or not confirm_pw:
            flash("All password fields are required.", "error")
        elif not check_password_hash(current_user.password, current_pw):
            flash("Incorrect current password.", "error")
        elif new_pw != confirm_pw:
            flash("New passwords do not match.", "error")
        else:
            current_user.password = generate_password_hash(new_pw, method='pbkdf2:sha256')
            db.session.commit()
            flash("Password changed successfully!", "success")

    return render_template("admin_profile.html", user=current_user)

@app.route("/admin/settings", methods=["GET", "POST"])
@login_required
@admin_required
def admin_settings():
    # Fetch config, create if not exists
    config = SiteConfig.query.first()
    if not config:
        config = SiteConfig()
        db.session.add(config)
        db.session.commit()

    if request.method == "POST":
        try:
            config.site_name = request.form.get("site_name")
            config.support_email = request.form.get("support_email")
            config.default_trial_days = int(request.form.get("default_trial_days"))
            config.allow_registrations = True if request.form.get("allow_registrations") else False
            config.maintenance_mode = True if request.form.get("maintenance_mode") else False
            db.session.commit()
            flash("System settings updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "error")
        return redirect(url_for('admin_settings'))

    return render_template("admin_settings.html", user=current_user, config=config)

# --- Features ---

@app.route("/calculate_calories", methods=["POST"])
@login_required
def calculate_calories():
    if not current_user.can_access_ai():
        return jsonify({"error": "Trial Expired. Upgrade to Premium."}), 403
    
    file = request.files.get('food_image')
    if not file: return jsonify({"error": "No file uploaded"}), 400
    
    try:
        image_part = convert_image_to_part(file)
        result = get_calorie_estimation(image_part)
        
        if "error" in result: return jsonify(result), 500
        
        nutrients = result.get('total_nutrients', {})
        new_log = FoodLog(
            user_id=current_user.id,
            food_name=result.get('analysis_notes', 'Unknown'),
            calories=result.get('total_calories', 0),
            protein=nutrients.get('protein_g', 0),
            carbs=nutrients.get('carbs_g', 0),
            fat=nutrients.get('fat_g', 0)
        )
        db.session.add(new_log)
        db.session.commit()

        today_date = datetime.utcnow().date()
        logs_today = FoodLog.query.filter_by(user_id=current_user.id).all()
        total_today = sum(l.calories for l in logs_today if l.date.date() == today_date)
        
        limit_alert = False
        limit_msg = ""
        if current_user.daily_calorie_limit and total_today > current_user.daily_calorie_limit:
            limit_alert = True
            limit_msg = f"WARNING: Limit exceeded by {total_today - current_user.daily_calorie_limit} kcal!"

        response_data = result
        response_data['limit_alert'] = limit_alert
        response_data['limit_message'] = limit_msg
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/demo_analyze", methods=["POST"])
def demo_analyze():
    file = request.files.get('food_image')
    if not file: return jsonify({"error": "No file uploaded"}), 400
    try:
        image_part = convert_image_to_part(file)
        result = get_calorie_estimation(image_part)
        return jsonify(result) if "error" not in result else (jsonify(result), 500)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/generate_diet_plan", methods=["POST"])
@login_required
def generate_diet_plan():
    if not current_user.can_access_ai():
        return jsonify({"error": "Trial Expired"}), 403
    data = request.json
    try:
        weight = float(data.get('weight'))
        height = float(data.get('height'))
        age = int(data.get('age'))
        gender = data.get('gender')
        goal = data.get('goal')
        activity = data.get('activity')

        if gender == 'male':
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

        multipliers = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725}
        tdee = bmr * multipliers.get(activity, 1.2)

        if goal == 'lose': daily_limit = int(tdee - 500)
        elif goal == 'gain': daily_limit = int(tdee + 500)
        else: daily_limit = int(tdee)

        current_user.age = age
        current_user.gender = gender
        current_user.current_weight = weight
        current_user.height = height
        current_user.activity_level = activity
        current_user.goal = goal
        current_user.daily_calorie_limit = daily_limit
        db.session.commit()

        prompt = f"Create a 1-day diet plan for {age}yr old {gender}, {weight}kg. Goal: {goal}. Daily Limit: {daily_limit} kcal. Use HTML tags (<h3>, <ul>, <li>) only. No markdown."
        response = text_model.generate_content(prompt)
        current_user.saved_diet_plan = response.text
        db.session.commit()
        return jsonify({"plan": response.text, "limit": daily_limit})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/export_data")
@login_required
def export_data():
    logs = FoodLog.query.filter_by(user_id=current_user.id).all()
    csv = "Date,Food,Calories\n"
    for l in logs:
        csv += f"{l.date},{l.food_name},{l.calories}\n"
    return Response(csv, mimetype="text/csv", headers={"Content-disposition": "attachment; filename=history.csv"})

@app.route("/bmi_calculator", methods=["POST"])
@login_required
def bmi_calculator():
    try:
        data = request.json
        bmi = round(float(data['weight']) / ((float(data['height'])/100) ** 2), 1)
        cat = "Normal" if 18.5 <= bmi <= 24.9 else "Overweight" if bmi > 24.9 else "Underweight"
        return jsonify({"bmi": bmi, "category": cat})
    except:
        return jsonify({"error": "Invalid Input"}), 400

@app.route("/get_calendar_data")
@login_required
def get_calendar_data():
    logs = FoodLog.query.filter_by(user_id=current_user.id).all()
    calendar_data = {}
    for log in logs:
        date_str = log.date.strftime('%Y-%m-%d')
        if date_str not in calendar_data: calendar_data[date_str] = {"total": 0, "foods": []}
        calendar_data[date_str]["total"] += log.calories
        calendar_data[date_str]["foods"].append(f"{log.food_name} ({log.calories})")

    limit = current_user.daily_calorie_limit or 2000
    final_data = []
    for date, data in calendar_data.items():
        status = "success" if data["total"] <= limit else "danger"
        final_data.append({
            "title": f"{data['total']} kcal", "start": date,
            "color": "#10b981" if status == "success" else "#ef4444",
            "extendedProps": { "foods": data["foods"], "total": data["total"], "limit": limit }
        })
    return jsonify(final_data)

@app.route("/create_order", methods=["POST"])
@login_required
def create_order():
    if not razorpay_client: return jsonify({"error": "Payment config missing"}), 500
    order = razorpay_client.order.create({"amount": 9900, "currency": "INR", "receipt": f"u_{current_user.id}"})
    return jsonify(order)

@app.route("/verify_payment", methods=["POST"])
@login_required
def verify_payment():
    data = request.json
    try:
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        })
        current_user.is_premium = True
        current_user.premium_expiry = datetime.utcnow() + timedelta(days=365)
        db.session.commit()
        return jsonify({"status": "success"})
    except:
        return jsonify({"status": "failed"}), 400

@app.route("/pricing")
@login_required
def pricing():
    rzp_key = os.getenv("RAZORPAY_KEY_ID")
    return render_template("pricing.html", user=current_user, rzp_key=rzp_key)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)