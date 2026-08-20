from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for job seekers"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    profile_picture = db.Column(db.String(255))
    bio = db.Column(db.Text)
    skills = db.Column(db.Text)  # JSON or comma-separated
    experience = db.Column(db.Text)
    education = db.Column(db.Text)
    location = db.Column(db.String(120))
    resume_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    applications = db.relationship('Application', backref='user', lazy=True, cascade='all, delete-orphan')
    saved_jobs = db.relationship('SavedJob', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'location': self.location,
            'bio': self.bio,
            'skills': self.skills,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Job(db.Model):
    """Job listing model"""
    __tablename__ = 'job'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    company = db.Column(db.String(120), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    location = db.Column(db.String(120), nullable=False, index=True)
    job_type = db.Column(db.String(50))  # Full-time, Part-time, Contract, Remote
    experience_level = db.Column(db.String(50))  # Entry, Mid, Senior
    category = db.Column(db.String(100))  # IT, Finance, Marketing, etc.
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    company_logo = db.Column(db.String(255))
    company_description = db.Column(db.Text)
    posted_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    deadline = db.Column(db.DateTime)
    views = db.Column(db.Integer, default=0)
    applications_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    applications = db.relationship('Application', backref='job', lazy=True, cascade='all, delete-orphan')
    saved_by = db.relationship('SavedJob', backref='job', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Job {self.title}>'
    
    def to_dict(self):
        """Convert job to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'job_type': self.job_type,
            'experience_level': self.experience_level,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'posted_date': self.posted_date.isoformat() if self.posted_date else None,
            'applications_count': self.applications_count,
            'views': self.views
        }


class Application(db.Model):
    """Job application model"""
    __tablename__ = 'application'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False, index=True)
    cover_letter = db.Column(db.Text)
    resume_url = db.Column(db.String(255))
    status = db.Column(db.String(50), default='Applied', index=True)  # Applied, Shortlisted, Interview, Rejected, Offered, Accepted
    interview_date = db.Column(db.DateTime)
    interview_notes = db.Column(db.Text)
    rating = db.Column(db.Integer)  # 1-5 stars
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Application {self.user_id} - {self.job_id}>'
    
    def to_dict(self):
        """Convert application to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'job_id': self.job_id,
            'status': self.status,
            'interview_date': self.interview_date.isoformat() if self.interview_date else None,
            'applied_date': self.applied_date.isoformat() if self.applied_date else None
        }


class SavedJob(db.Model):
    """Saved/Bookmarked jobs model"""
    __tablename__ = 'saved_job'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False, index=True)
    notes = db.Column(db.Text)  # User notes about the job
    saved_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint - can't save same job twice
    __table_args__ = (db.UniqueConstraint('user_id', 'job_id', name='unique_saved_job'),)
    
    def __repr__(self):
        return f'<SavedJob {self.user_id} - {self.job_id}>'
    
    def to_dict(self):
        """Convert saved job to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'job_id': self.job_id,
            'saved_date': self.saved_date.isoformat() if self.saved_date else None
        }


class Company(db.Model):
    """Company/Employer model"""
    __tablename__ = 'company'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    logo = db.Column(db.String(255))
    description = db.Column(db.Text)
    website = db.Column(db.String(255))
    location = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    industry = db.Column(db.String(100))
    company_size = db.Column(db.String(50))  # Startup, Small, Medium, Large
    founded_year = db.Column(db.Integer)
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Company {self.name}>'


class Review(db.Model):
    """Company review model"""
    __tablename__ = 'review'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    title = db.Column(db.String(200))
    comment = db.Column(db.Text)
    salary = db.Column(db.String(100))
    position = db.Column(db.String(100))
    work_life_balance = db.Column(db.Integer)  # 1-5
    culture = db.Column(db.Integer)  # 1-5
    growth = db.Column(db.Integer)  # 1-5
    benefits = db.Column(db.Integer)  # 1-5
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='reviews')
    company = db.relationship('Company', backref='reviews')
    
    def __repr__(self):
        return f'<Review {self.user_id} - {self.company_id}>'


class Notification(db.Model):
    """Notification model"""
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))  # application, message, job_alert, etc.
    related_id = db.Column(db.Integer)  # Job ID, Application ID, etc.
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.id}>'


class SearchHistory(db.Model):
    """User search history"""
    __tablename__ = 'search_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    search_query = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(120))
    job_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='search_history')
    
    def __repr__(self):
        return f'<SearchHistory {self.search_query}>'


class Skill(db.Model):
    """Skills/Tags model"""
    __tablename__ = 'skill'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Skill {self.name}>'


class Message(db.Model):
    """Direct messages between users"""
    __tablename__ = 'message'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
    
    def __repr__(self):
        return f'<Message {self.sender_id} -> {self.receiver_id}>'
