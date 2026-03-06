from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///keshar_sai.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ==================== DATABASE MODELS ====================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_image = db.Column(db.String(200))
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_code = db.Column(db.String(6))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='available')
    badge = db.Column(db.String(50))
    area = db.Column(db.String(100), nullable=False)
    facing = db.Column(db.String(50), nullable=False)
    price = db.Column(db.String(100), nullable=False)
    price_per = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image1 = db.Column(db.String(200))
    image2 = db.Column(db.String(200))
    image3 = db.Column(db.String(200))
    image4 = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    features = db.relationship('PropertyFeature', backref='property', lazy=True, cascade='all, delete-orphan')

class PropertyFeature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    feature_text = db.Column(db.String(200), nullable=False)

class LikedProperty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== HELPER FUNCTIONS ====================

def generate_code():
    return ''.join(random.choices(string.digits, k=6))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png','jpg','jpeg','gif','webp'}

def save_image(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = str(int(datetime.utcnow().timestamp()))
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filename
    return None

def send_email(to_email, subject, message):
    # ===== EMAIL CONFIGURATION =====
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_EMAIL = "keshar7enterprises@gmail.com"
    SMTP_PASSWORD = "your-app-password-here"
    # ===============================
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.set_debuglevel(0)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        server.quit()
        return True
    except:
        return False

# ==================== ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html', year=datetime.now().year)

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please enter email and password', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        
        if not all([name, email, mobile, password]):
            flash('All fields required', 'error')
            return render_template('signup.html')
        
        if len(mobile) != 10 or not mobile.isdigit():
            flash('Mobile must be exactly 10 digits', 'error')
            return render_template('signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('signup.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('signup.html')
        
        if User.query.filter_by(mobile=mobile).first():
            flash('Mobile already registered', 'error')
            return render_template('signup.html')
        
        # Store in session and generate code
        email_code = generate_code()
        session['pending_user'] = {
            'name': name, 'email': email, 'mobile': mobile, 'password': password
        }
        session['email_code'] = email_code
        
        # Send verification email
        send_email(
            to_email=email,
            subject="Verify Your Email - Keshar Sai Developers",
            message=f"Dear {name},\n\nYour verification code is: {email_code}\n\nBest regards,\nKeshar Sai Developers"
        )
        
        flash('Verification code sent to your email!', 'success')
        return redirect(url_for('verify_signup'))
    
    return render_template('signup.html')

@app.route('/verify-signup', methods=['GET', 'POST'])
def verify_signup():
    if 'pending_user' not in session:
        flash('No pending registration', 'error')
        return redirect(url_for('signup'))
    
    if request.method == 'POST':
        email_code = request.form.get('email_code', '').strip()
        
        if email_code == session.get('email_code'):
            pending = session['pending_user']
            user = User(
                name=pending['name'],
                email=pending['email'],
                mobile=pending['mobile'],
                password=generate_password_hash(pending['password']),
                email_verified=True
            )
            db.session.add(user)
            db.session.commit()
            
            send_email(
                to_email=user.email,
                subject="Welcome to Keshar Sai Developers!",
                message=f"Dear {user.name},\n\nYour account has been created successfully!\n\nEmail: {user.email}\nMobile: {user.mobile}\n\nBest regards,\nKeshar Sai Developers"
            )
            
            session.pop('pending_user', None)
            session.pop('email_code', None)
            
            login_user(user)
            flash('Account created! Welcome.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid verification code', 'error')
    
    return render_template('verify-signup.html', email=session['pending_user']['email'])

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    properties = Property.query.filter(Property.category != 'industrial').order_by(Property.created_at.desc()).all()
    liked_ids = [l.property_id for l in LikedProperty.query.filter_by(user_id=current_user.id).all()]
    return render_template('dashboard.html', properties=properties, is_owner=True, liked_property_ids=liked_ids)

@app.route('/property/<int:id>')
@login_required
def property_detail(id):
    prop = Property.query.get_or_404(id)
    return render_template('property-view.html', property=prop, is_owner=True)

@app.route('/add-property', methods=['GET','POST'])
@login_required
def add_property():
    if request.method == 'POST':
        try:
            p = Property(
                title=request.form.get('title'), category=request.form.get('category'),
                location=request.form.get('location'), status=request.form.get('status', 'available'),
                badge=request.form.get('badge'), area=request.form.get('area'),
                facing=request.form.get('facing'), price=request.form.get('price'),
                price_per=request.form.get('price_per'), description=request.form.get('description')
            )
            
            for i in range(1, 5):
                f = request.files.get(f'image{i}')
                if f and f.filename:
                    fn = save_image(f)
                    if fn: setattr(p, f'image{i}', fn)
            
            db.session.add(p)
            db.session.flush()
            
            for ft in request.form.getlist('features[]'):
                if ft.strip():
                    db.session.add(PropertyFeature(property_id=p.id, feature_text=ft.strip()))
            
            db.session.commit()
            flash('Property added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding property', 'error')
    
    return render_template('add-property.html')

@app.route('/edit-property/<int:id>', methods=['GET','POST'])
@login_required
def edit_property(id):
    p = Property.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            p.title = request.form.get('title')
            p.category = request.form.get('category')
            p.location = request.form.get('location')
            p.status = request.form.get('status')
            p.badge = request.form.get('badge')
            p.area = request.form.get('area')
            p.facing = request.form.get('facing')
            p.price = request.form.get('price')
            p.price_per = request.form.get('price_per')
            p.description = request.form.get('description')
            
            for i in range(1, 5):
                if request.form.get(f'delete_image{i}'):
                    setattr(p, f'image{i}', None)
                else:
                    f = request.files.get(f'image{i}')
                    if f and f.filename:
                        fn = save_image(f)
                        if fn: setattr(p, f'image{i}', fn)
            
            PropertyFeature.query.filter_by(property_id=p.id).delete()
            for ft in request.form.getlist('features[]'):
                if ft.strip():
                    db.session.add(PropertyFeature(property_id=p.id, feature_text=ft.strip()))
            
            p.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Property updated!', 'success')
            return redirect(url_for('property_detail', id=id))
        except:
            db.session.rollback()
            flash('Error updating property', 'error')
    
    return render_template('edit-property.html', property=p)

@app.route('/delete-property/<int:id>', methods=['DELETE'])
@login_required
def delete_property(id):
    try:
        p = Property.query.get_or_404(id)
        for i in range(1, 5):
            img = getattr(p, f'image{i}')
            if img:
                img_path = os.path.join(app.config['UPLOAD_FOLDER'], img)
                if os.path.exists(img_path):
                    os.remove(img_path)
        db.session.delete(p)
        db.session.commit()
        return jsonify({'success': True})
    except:
        return jsonify({'success': False}), 500

@app.route('/about')
@login_required
def about():
    return render_template('about.html', year=datetime.now().year)

@app.route('/contact')
@login_required
def contact():
    return render_template('contact.html', year=datetime.now().year)

@app.route('/contact-submit', methods=['POST'])
@login_required
def contact_submit():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        
        # Send to admin
        send_email(
            to_email="keshar7enterprises@gmail.com",
            subject=f"New Contact: {name}",
            message=f"From: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}"
        )
        
        # Send confirmation to user
        send_email(
            to_email=email,
            subject="Thank you for contacting us",
            message=f"Dear {name},\n\nWe received your message and will respond soon.\n\nBest regards,\nKeshar Sai Developers"
        )
        
        flash('Message sent successfully!', 'success')
    except:
        flash('Error sending message', 'error')
    
    return redirect(url_for('contact'))

@app.route('/liked-properties')
@login_required
def liked_properties():
    liked = LikedProperty.query.filter_by(user_id=current_user.id).all()
    props = [Property.query.get(l.property_id) for l in liked]
    props = [p for p in props if p]
    return render_template('liked-properties.html', properties=props, liked_property_ids=[p.id for p in props])

@app.route('/users')
@login_required
def users_list():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('users.html', users=users)

@app.route('/like-property/<int:property_id>', methods=['POST'])
@login_required
def like_property(property_id):
    try:
        existing = LikedProperty.query.filter_by(user_id=current_user.id, property_id=property_id).first()
        if existing:
            return jsonify({'success': False})
        like = LikedProperty(user_id=current_user.id, property_id=property_id)
        db.session.add(like)
        db.session.commit()
        return jsonify({'success': True})
    except:
        return jsonify({'success': False}), 500

@app.route('/unlike-property/<int:property_id>', methods=['POST'])
@login_required
def unlike_property(property_id):
    try:
        like = LikedProperty.query.filter_by(user_id=current_user.id, property_id=property_id).first()
        if like:
            db.session.delete(like)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False})
    except:
        return jsonify({'success': False}), 500

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
            current_user.name = request.form.get('name')
            current_user.mobile = request.form.get('mobile')
            
            if 'profile_image' in request.files:
                file = request.files['profile_image']
                if file and file.filename:
                    if current_user.profile_image:
                        old = os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_image)
                        if os.path.exists(old): os.remove(old)
                    fn = save_image(file)
                    if fn: current_user.profile_image = fn
            
            db.session.commit()
            flash('Profile updated!', 'success')
            return redirect(url_for('profile'))
        except:
            db.session.rollback()
            flash('Error updating profile', 'error')
    
    return render_template('profile.html', user=current_user)

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html', user=current_user)

@app.template_filter('get_image_url')
def get_image_url(filename):
    if filename:
        return url_for('static', filename=f'uploads/{filename}')
    return url_for('static', filename='images/placeholder.jpg')

def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
