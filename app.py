from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///keshar_sai.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ==================== DATABASE MODELS ====================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    def is_owner(self):
        """Check if user is the owner (xyz@gmail.com)"""
        return self.email == 'xyz@gmail.com'

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # agricultural, residential, commercial, farmhouse
    location = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='available')  # available, reserved, sold
    badge = db.Column(db.String(50))  # FEATURED, HOT DEAL, NEW, etc.
    
    # Specifications
    area = db.Column(db.String(100), nullable=False)
    facing = db.Column(db.String(50), nullable=False)
    spec1_label = db.Column(db.String(100))  # e.g., Water Source
    spec1_value = db.Column(db.String(100))  # e.g., Borewell
    
    # Pricing
    price = db.Column(db.String(100), nullable=False)
    price_per = db.Column(db.String(100), nullable=False)
    
    # Description
    description = db.Column(db.Text, nullable=False)
    
    # Images (store filenames)
    image1 = db.Column(db.String(200))
    image2 = db.Column(db.String(200))
    image3 = db.Column(db.String(200))
    image4 = db.Column(db.String(200))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LikedProperty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='liked_properties')
    property = db.relationship('Property', backref='liked_by')


with app.app_context():
    db.create_all()
# ==================== LOGIN MANAGER ====================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== HELPER FUNCTIONS ====================

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    """Save uploaded image and return filename"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        filename = f"{datetime.utcnow().timestamp()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filename
    return None

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html',year=datetime.now().year)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([name, email, password, confirm_password]):
            flash('All fields are required', 'error')
        elif password != confirm_password:
            flash('Passwords do not match', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
        else:
            # Create new user
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(name=name, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard - show all properties"""
    # Exclude industrial category
    properties = Property.query.filter(Property.category != 'industrial').order_by(Property.created_at.desc()).all()
    # All authenticated users can add/edit/delete
    is_owner = True
    
    # Get list of property IDs that current user has liked
    liked_property_ids = [like.property_id for like in LikedProperty.query.filter_by(user_id=current_user.id).all()]
    
    return render_template('dashboard.html', properties=properties, is_owner=is_owner, liked_property_ids=liked_property_ids)

@app.route('/property/<int:id>')
@login_required
def property_detail(id):
    """Property detail page"""
    property = Property.query.get_or_404(id)
    # All authenticated users can edit/delete
    is_owner = True
    return render_template('property-view.html', property=property, is_owner=is_owner)

@app.route('/add-property', methods=['GET', 'POST'])
@login_required
def add_property():
    """Add new property (any authenticated user)"""
    if request.method == 'POST':
        try:
            # Create new property
            property = Property(
                title=request.form.get('title'),
                category=request.form.get('category'),
                location=request.form.get('location'),
                status=request.form.get('status', 'available'),
                badge=request.form.get('badge'),
                area=request.form.get('area'),
                facing=request.form.get('facing'),
                spec1_label=request.form.get('spec1_label'),
                spec1_value=request.form.get('spec1_value'),
                price=request.form.get('price'),
                price_per=request.form.get('price_per'),
                description=request.form.get('description')
            )
            
            # Handle image uploads
            for i in range(1, 5):
                file = request.files.get(f'image{i}')
                if file and file.filename:
                    filename = save_image(file)
                    if filename:
                        setattr(property, f'image{i}', filename)
            
            db.session.add(property)
            db.session.commit()
            
            flash('Property added successfully!', 'success')
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding property: {str(e)}', 'error')
    
    return render_template('add-property.html')

@app.route('/edit-property/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_property(id):
    """Edit property (any authenticated user)"""
    property = Property.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Update property fields
            property.title = request.form.get('title')
            property.category = request.form.get('category')
            property.location = request.form.get('location')
            property.status = request.form.get('status')
            property.badge = request.form.get('badge')
            property.area = request.form.get('area')
            property.facing = request.form.get('facing')
            property.spec1_label = request.form.get('spec1_label')
            property.spec1_value = request.form.get('spec1_value')
            property.price = request.form.get('price')
            property.price_per = request.form.get('price_per')
            property.description = request.form.get('description')
            
            # Handle image updates
            for i in range(1, 5):
                # Check if image should be deleted
                if request.form.get(f'delete_image{i}'):
                    setattr(property, f'image{i}', None)
                else:
                    # Check for new image upload
                    file = request.files.get(f'image{i}')
                    if file and file.filename:
                        filename = save_image(file)
                        if filename:
                            setattr(property, f'image{i}', filename)
            
            property.updated_at = datetime.utcnow()
            db.session.commit()
            
            flash('Property updated successfully!', 'success')
            return redirect(url_for('property_detail', id=id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating property: {str(e)}', 'error')
    
    return render_template('edit-property.html', property=property)

@app.route('/delete-property/<int:id>', methods=['DELETE'])
@login_required
def delete_property(id):
    """Delete property (any authenticated user)"""
    try:
        property = Property.query.get_or_404(id)
        
        # Delete associated images from filesystem
        for i in range(1, 5):
            image_filename = getattr(property, f'image{i}')
            if image_filename:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
                if os.path.exists(image_path):
                    os.remove(image_path)
        
        db.session.delete(property)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Property deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/about')
def about():
    """About Us page"""
    return render_template('about.html',year=datetime.now().year)

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html',year=datetime.now().year)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
            current_user.name = request.form.get('name')
            current_user.mobile = request.form.get('mobile')
            
            # Handle profile image upload
            if 'profile_image' in request.files:
                file = request.files['profile_image']
                if file and file.filename:
                    # Delete old profile image if exists
                    if current_user.profile_image:
                        old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_image)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    
                    filename = save_image(file)
                    if filename:
                        current_user.profile_image = filename
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
    
    return render_template('profile.html', user=current_user)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    return render_template('settings.html', user=current_user)

@app.route('/liked-properties')
@login_required
def liked_properties():
    """Show user's liked properties"""
    liked = LikedProperty.query.filter_by(user_id=current_user.id).all()
    properties = [like.property for like in liked]
    
    # All properties on this page are liked
    liked_property_ids = [prop.id for prop in properties]
    
    return render_template('liked-properties.html', properties=properties, liked_property_ids=liked_property_ids)

@app.route('/users')
@login_required
def users_list():
    """Show all users"""
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('users.html', users=all_users)

@app.route('/like-property/<int:property_id>', methods=['POST'])
@login_required
def like_property(property_id):
    """Like a property"""
    try:
        # Check if already liked
        existing = LikedProperty.query.filter_by(
            user_id=current_user.id, 
            property_id=property_id
        ).first()
        
        if existing:
            return jsonify({'success': False, 'message': 'Already liked'})
        
        # Add like
        like = LikedProperty(user_id=current_user.id, property_id=property_id)
        db.session.add(like)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Property liked'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/unlike-property/<int:property_id>', methods=['POST'])
@login_required
def unlike_property(property_id):
    """Unlike a property"""
    try:
        like = LikedProperty.query.filter_by(
            user_id=current_user.id, 
            property_id=property_id
        ).first()
        
        if not like:
            return jsonify({'success': False, 'message': 'Not liked'})
        
        db.session.delete(like)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Property unliked'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
    

@app.route('/verify', methods=['GET','POST'])
@login_required
def verify():
    if request.method == 'POST':
        if request.form.get('email_code') == current_user.email_verification_code:
            current_user.email_verified = True
        if request.form.get('mobile_code') == current_user.mobile_verification_code:
            current_user.mobile_verified = True
        db.session.commit()
        if current_user.email_verified and current_user.mobile_verified:
            flash('Verified!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid code', 'error')
    return render_template('verify.html')

@app.route('/verify-signup', methods=['GET', 'POST'])
def verify_signup():
    if 'pending_user' not in session:
        flash('No pending registration', 'error')
        return redirect(url_for('signup'))
    
    if request.method == 'POST':
        if (request.form.get('email_code') == session.get('email_code') and 
            request.form.get('mobile_code') == session.get('mobile_code')):
            
            pending = session['pending_user']
            user = User(
                name=pending['name'], email=pending['email'], mobile=pending['mobile'],
                password=generate_password_hash(pending['password']),
                email_verified=True, mobile_verified=True
            )
            db.session.add(user)
            db.session.commit()
            
            session.pop('pending_user', None)
            session.pop('email_code', None)
            session.pop('mobile_code', None)
            
            login_user(user)
            flash('Account created! Welcome.', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid codes', 'error')
    
    return render_template('verify-signup.html', 
                         email=session['pending_user']['email'],
                         mobile=session['pending_user']['mobile'])

@app.route('/resend-verification', methods=['POST'])
@login_required
def resend_verification():
    vtype = request.json.get('type')
    if vtype == 'email':
        current_user.email_verification_code = generate_code()
        print(f"New email code: {current_user.email_verification_code}")
    elif vtype == 'mobile':
        current_user.mobile_verification_code = generate_code()
        print(f"New SMS code: {current_user.mobile_verification_code}")
    db.session.commit()
    return jsonify({'success': True})


# ==================== TEMPLATE FILTERS ====================

@app.template_filter('get_image_url')
def get_image_url(filename):
    """Get full URL for image"""
    if filename:
        return url_for('static', filename=f'uploads/{filename}')
    return url_for('static', filename='images/placeholder.jpg')

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# ==================== INITIALIZE DATABASE ====================

def init_db():
    """Initialize database with test user"""
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if test user exists
        test_user = User.query.filter_by(email='test@gmail.com').first()
        if not test_user:
            # Create test user account
            test_user = User(
                name='Test User',
                email='test@gmail.com',
                password=generate_password_hash('password123', method='pbkdf2:sha256')
            )
            db.session.add(test_user)
            db.session.commit()
            print('Test user account created: test@gmail.com / password123')
        
        print('Database initialized successfully!')
        print('Any authenticated user can add/edit/delete properties.')
        print('Dashboard will start empty - users can add properties.')

# ==================== RUN APPLICATION ====================

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run Flask app
    app.run(debug=True)
