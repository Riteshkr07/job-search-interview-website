from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///job_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== DATABASE MODELS ====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    profile_picture = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    applications = db.relationship('Application', backref='user', lazy=True, cascade='all, delete-orphan')
    saved_jobs = db.relationship('SavedJob', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    location = db.Column(db.String(120), nullable=False)
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    job_type = db.Column(db.String(50))  # Full-time, Part-time, Contract
    experience_level = db.Column(db.String(50))  # Entry, Mid, Senior
    posted_date = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime)
    company_logo = db.Column(db.String(200))
    
    applications = db.relationship('Application', backref='job', lazy=True, cascade='all, delete-orphan')
    saved_by = db.relationship('SavedJob', backref='job', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Job {self.title}>'


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    status = db.Column(db.String(50), default='Applied')  # Applied, Reviewed, Interview, Rejected, Offered
    cover_letter = db.Column(db.Text)
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Application {self.id}>'


class SavedJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    saved_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SavedJob {self.id}>'


class InterviewTip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))  # Technical, Behavioral, HR
    difficulty = db.Column(db.String(50))  # Easy, Medium, Hard
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<InterviewTip {self.title}>'


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Home page"""
    jobs = Job.query.limit(6).all()
    total_jobs = Job.query.count()
    total_companies = db.session.query(db.func.count(db.func.distinct(Job.company))).scalar()
    
    return render_template('index.html', jobs=jobs, total_jobs=total_jobs, total_companies=total_companies)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password:
            flash('All fields are required!', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    applications = Application.query.filter_by(user_id=user.id).all()
    saved_jobs = SavedJob.query.filter_by(user_id=user.id).all()
    
    return render_template('dashboard.html', user=user, applications=applications, saved_jobs=saved_jobs)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    """User profile"""
    if 'user_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.phone = request.form.get('phone')
        user.bio = request.form.get('bio')
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('profile.html', user=user)


@app.route('/jobs')
def jobs():
    """Job listings"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    location = request.args.get('location', '')
    job_type = request.args.get('job_type', '')
    
    query = Job.query
    
    if search:
        query = query.filter(
            db.or_(
                Job.title.ilike(f'%{search}%'),
                Job.company.ilike(f'%{search}%'),
                Job.description.ilike(f'%{search}%')
            )
        )
    
    if location:
        query = query.filter(Job.location.ilike(f'%{location}%'))
    
    if job_type:
        query = query.filter(Job.job_type == job_type)
    
    jobs_paginated = query.paginate(page=page, per_page=12)
    
    return render_template('jobs.html', jobs=jobs_paginated.items, pagination=jobs_paginated)


@app.route('/job/<int:job_id>')
def job_detail(job_id):
    """Job detail page"""
    job = Job.query.get_or_404(job_id)
    applied = False
    saved = False
    
    if 'user_id' in session:
        applied = Application.query.filter_by(user_id=session['user_id'], job_id=job_id).first() is not None
        saved = SavedJob.query.filter_by(user_id=session['user_id'], job_id=job_id).first() is not None
    
    return render_template('job_detail.html', job=job, applied=applied, saved=saved)


@app.route('/apply/<int:job_id>', methods=['POST'])
def apply_job(job_id):
    """Apply for a job"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first!'}), 401
    
    job = Job.query.get_or_404(job_id)
    user_id = session['user_id']
    
    # Check if already applied
    existing_application = Application.query.filter_by(user_id=user_id, job_id=job_id).first()
    if existing_application:
        return jsonify({'success': False, 'message': 'You have already applied for this job!'}), 400
    
    cover_letter = request.form.get('cover_letter', '')
    
    application = Application(user_id=user_id, job_id=job_id, cover_letter=cover_letter)
    
    try:
        db.session.add(application)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Application submitted successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/save-job/<int:job_id>', methods=['POST'])
def save_job(job_id):
    """Save a job"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first!'}), 401
    
    job = Job.query.get_or_404(job_id)
    user_id = session['user_id']
    
    # Check if already saved
    existing_saved = SavedJob.query.filter_by(user_id=user_id, job_id=job_id).first()
    if existing_saved:
        db.session.delete(existing_saved)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Job removed from saved!', 'saved': False})
    
    saved_job = SavedJob(user_id=user_id, job_id=job_id)
    
    try:
        db.session.add(saved_job)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Job saved successfully!', 'saved': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/saved-jobs')
def saved_jobs():
    """View saved jobs"""
    if 'user_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))
    
    page = request.args.get('page', 1, type=int)
    saved_jobs_paginated = SavedJob.query.filter_by(user_id=session['user_id']).paginate(page=page, per_page=12)
    
    return render_template('saved_jobs.html', saved_jobs=saved_jobs_paginated.items, pagination=saved_jobs_paginated)


@app.route('/applications')
def applications():
    """View user applications"""
    if 'user_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))
    
    page = request.args.get('page', 1, type=int)
    applications_paginated = Application.query.filter_by(user_id=session['user_id']).paginate(page=page, per_page=12)
    
    return render_template('applications.html', applications=applications_paginated.items, pagination=applications_paginated)


@app.route('/interview-tips')
def interview_tips():
    """Interview tips and resources"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    
    query = InterviewTip.query
    
    if category:
        query = query.filter(InterviewTip.category == category)
    
    tips_paginated = query.paginate(page=page, per_page=12)
    
    return render_template('interview_tips.html', tips=tips_paginated.items, pagination=tips_paginated)


@app.route('/interview-tip/<int:tip_id>')
def interview_tip_detail(tip_id):
    """Interview tip detail page"""
    tip = InterviewTip.query.get_or_404(tip_id)
    return render_template('interview_tip_detail.html', tip=tip)


@app.route('/search')
def search():
    """Search jobs"""
    return redirect(url_for('jobs', search=request.args.get('q', '')))


@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    if request.method == 'POST':
        flash('Thank you for contacting us! We will get back to you soon.', 'success')
        return redirect(url_for('index'))
    
    return render_template('contact.html')


@app.errorhandler(404)
def not_found_error(error):
    """404 error handler"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    db.session.rollback()
    return render_template('500.html'), 500


# ==================== CONTEXT PROCESSORS ====================

@app.context_processor
def inject_user():
    """Inject user into all templates"""
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return {'current_user': user}


# ==================== DATABASE INITIALIZATION ====================

def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        print("Database initialized!")
        
        # Add sample data if not exists
        if Job.query.first() is None:
            sample_jobs = [
                Job(
                    title='Python Developer',
                    company='Tech Corp',
                    description='Looking for an experienced Python developer with 3+ years of experience.',
                    requirements='Python, Django, REST APIs, PostgreSQL',
                    location='New York, NY',
                    salary_min=80000,
                    salary_max=120000,
                    job_type='Full-time',
                    experience_level='Mid'
                ),
                Job(
                    title='Full Stack Developer',
                    company='StartUp Inc',
                    description='Join our team as a Full Stack Developer.',
                    requirements='React, Node.js, MongoDB, AWS',
                    location='San Francisco, CA',
                    salary_min=90000,
                    salary_max=130000,
                    job_type='Full-time',
                    experience_level='Senior'
                ),
                Job(
                    title='Frontend Engineer',
                    company='Design Studio',
                    description='Create beautiful and responsive UIs with React.',
                    requirements='React, JavaScript, CSS, HTML',
                    location='Los Angeles, CA',
                    salary_min=70000,
                    salary_max=100000,
                    job_type='Full-time',
                    experience_level='Entry'
                ),
            ]
            
            db.session.add_all(sample_jobs)
            db.session.commit()
            print("Sample jobs added!")


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
