import os
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import IntegerField, StringField, TextAreaField, BooleanField, SelectField, PasswordField
from wtforms.validators import DataRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_socketio import SocketIO, emit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
import markdown
from PIL import Image
import secrets
from datetime import datetime

# Import configuration
from config import get_config

app = Flask(__name__)
app.config.from_object(get_config())

# Get the base directory
basedir = os.getcwd()

# Ensure instance directory exists for database
instance_path = os.path.join(basedir, 'instance')
os.makedirs(instance_path, exist_ok=True)

# Ensure upload directory exists
upload_folder = os.path.join(basedir, 'static', 'uploads')
os.makedirs(upload_folder, exist_ok=True)
app.config['UPLOAD_FOLDER'] = upload_folder

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
mail = Mail(app)
jwt = JWTManager(app)
socketio = SocketIO(app)

# Rate limiting configuration
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri=app.config.get('RATELIMIT_STORAGE_URI', 'memory://'),
    default_limits=app.config.get('RATELIMIT_DEFAULT', ["200 per day", "50 per hour"]),
    strategy=app.config.get('RATELIMIT_STRATEGY', 'fixed-window')
)

# ========== MODELS ==========
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    technologies = db.Column(db.String(500))
    github_url = db.Column(db.String(500))
    live_url = db.Column(db.String(500))
    featured = db.Column(db.Boolean, default=False)
    image_url = db.Column(db.String(500))
    category = db.Column(db.String(100))
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    published = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref=db.backref('posts', lazy=True))

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45))
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100))
    proficiency = db.Column(db.Integer, default=50)
    featured = db.Column(db.Boolean, default=False)

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5)
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SiteSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)

# ========== FORMS ==========
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[
        DataRequired(), 
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(), 
        Email(), 
        Length(max=120)
    ])
    subject = StringField('Subject', validators=[
        DataRequired(), 
        Length(min=5, max=200, message='Subject must be between 5 and 200 characters')
    ])
    message = TextAreaField('Message', validators=[
        DataRequired(), 
        Length(min=10, max=2000, message='Message must be between 10 and 2000 characters')
    ])

class ProjectForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    technologies = StringField('Technologies')
    github_url = StringField('GitHub URL')
    live_url = StringField('Live URL')
    featured = BooleanField('Featured')
    category = StringField('Category')
    image = FileField('Project Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])

class BlogPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    slug = StringField('Slug', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    excerpt = TextAreaField('Excerpt')
    published = BooleanField('Published')
    tags = StringField('Tags')

class SettingsForm(FlaskForm):
    site_name = StringField('Site Name', validators=[DataRequired()])
    admin_email = StringField('Admin Email', validators=[DataRequired(), Email()])
    mail_server = StringField('Mail Server')
    mail_port = IntegerField('Mail Port', default=587)
    mail_username = StringField('Mail Username')
    mail_password = PasswordField('Mail Password')
    mail_use_tls = BooleanField('Use TLS', default=True)
    email_notifications = BooleanField('Email Notifications', default=True)
    ai_chat_enabled = BooleanField('AI Chat Enabled', default=True)

# ========== UTILITY FUNCTIONS ==========
def ensure_directory_exists(path):
    """Ensure directory exists, create if it doesn't"""
    os.makedirs(path, exist_ok=True)

def save_image(image_file, folder='projects'):
    """Save uploaded image with proper directory creation"""
    try:
        # Ensure upload directory exists
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        ensure_directory_exists(upload_dir)
        
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(image_file.filename)
        if not f_ext:
            f_ext = '.png'
        filename = random_hex + f_ext
        file_path = os.path.join(upload_dir, filename)
        
        # Resize and save image
        output_size = (800, 600)
        image = Image.open(image_file)
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
            
        image.thumbnail(output_size, Image.Resampling.LANCZOS)
        image.save(file_path, optimize=True, quality=85)
        
        return f'uploads/{folder}/{filename}'
    except Exception as e:
        app.logger.error(f"Error saving image: {str(e)}")
        return None

def send_email_notification(contact_message):
    """Send email notification for contact form submissions"""
    try:
        app.logger.info("📧 Starting email notification process...")
        app.logger.info(f"📧 Message ID: {contact_message.id}")
        app.logger.info(f"📧 From: {contact_message.name} <{contact_message.email}>")
        app.logger.info(f"📧 Subject: {contact_message.subject}")
        
        # Check email configuration
        if not app.config.get('MAIL_USERNAME'):
            app.logger.error("❌ MAIL_USERNAME is not set")
            return False
            
        if not app.config.get('MAIL_PASSWORD'):
            app.logger.error("❌ MAIL_PASSWORD is not set")
            return False
            
        app.logger.info("✅ Email credentials are configured")
        
        # Check if email sending is suppressed
        if app.config.get('MAIL_SUPPRESS_SEND', False):
            app.logger.info("⏸️ Email sending suppressed (development mode)")
            return True
            
        # Verify template exists and can be rendered
        app.logger.info("📧 Attempting to render email template...")
        try:
            html_content = render_template('email/contact_notification.html', message=contact_message)
            app.logger.info("✅ Email template rendered successfully")
        except Exception as template_error:
            app.logger.error(f"❌ Failed to render email template: {str(template_error)}")
            app.logger.error(f"❌ Template error details: {type(template_error).__name__}")
            return False
        
        # Create message
        subject = f"Portfolio Contact: {contact_message.subject}"
        
        # FIX: Send to a DIFFERENT email than the sender
        # Option A: Use environment variable
        admin_email = os.environ.get('ADMIN_EMAIL', 'devil160907@gmail.com')
        # Option B: Hardcode a different email
        # admin_email = "your-personal-email@gmail.com"
        
        recipients = [admin_email]  # Send to different email address
        
        app.logger.info(f"📧 Preparing to send to: {recipients}")
        
        msg = Message(
            subject=subject,
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=recipients,
            html=html_content
        )
        
        # Add plain text version as fallback
        msg.body = f"""
        New Contact Form Submission - Portfolio Website
        
        Name: {contact_message.name}
        Email: {contact_message.email}
        Subject: {contact_message.subject}
        
        Message:
        {contact_message.message}
        
        ---
        Received: {contact_message.created_at.strftime('%Y-%m-%d at %H:%M')}
        IP Address: {contact_message.ip_address}
        Message ID: {contact_message.id}
        """
        
        app.logger.info("📧 Attempting to send email via SMTP...")
        
        # Actually send the email
        mail.send(msg)
        
        app.logger.info(f"✅ Email notification sent successfully for message #{contact_message.id}")
        app.logger.info(f"✅ Sent to: {admin_email}")
        return True
        
    except Exception as e:
        app.logger.error(f"❌ Failed to send email: {str(e)}")
        app.logger.error(f"❌ Error type: {type(e).__name__}")
        
        # More detailed error logging
        import traceback
        app.logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        return False

def send_user_confirmation_email(contact_message):
    """Send confirmation email to the user who submitted the contact form"""
    try:
        app.logger.info(f"📧 Sending confirmation email to: {contact_message.email}")
        
        # Check email configuration
        if not app.config.get('MAIL_USERNAME'):
            app.logger.error("❌ MAIL_USERNAME is not set")
            return False
            
        if not app.config.get('MAIL_PASSWORD'):
            app.logger.error("❌ MAIL_PASSWORD is not set")
            return False
        
        # Check if email sending is suppressed
        if app.config.get('MAIL_SUPPRESS_SEND', False):
            app.logger.info("⏸️ Email sending suppressed (development mode)")
            return True
            
        # Render user confirmation template
        try:
            html_content = render_template('email/user_confirmation.html', message=contact_message)
            app.logger.info("✅ User confirmation template rendered successfully")
        except Exception as template_error:
            app.logger.error(f"❌ Failed to render user confirmation template: {str(template_error)}")
            return False
        
        # Create message for the user
        site_name = "Portfolio"
        subject = f"Thank you for contacting {site_name}"
        recipients = [contact_message.email]  

        app.logger.info(f"📧 Sending confirmation to user: {recipients}")
        
        msg = Message(
            subject=subject,
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=recipients,
            html=html_content
        )
        
        # Add plain text version
        msg.body = f"""
        Thank You for Contacting {site_name}
        
        Dear {contact_message.name},
        
        Thank you for reaching out! I've received your message and will get back to you as soon as possible.
        
        Here's a copy of your message:
        Subject: {contact_message.subject}
        Message: {contact_message.message}
        
        I typically respond within 24 hours. If you have any urgent inquiries, please feel free to reach out directly.
        
        Best regards,
        {site_name} Owner
        
        ---
        This is an automated confirmation. Please do not reply to this email.
        """
        
        app.logger.info("📧 Attempting to send user confirmation email...")
        mail.send(msg)
        
        app.logger.info(f"✅ User confirmation email sent successfully to {contact_message.email}")
        return True
        
    except Exception as e:
        app.logger.error(f"❌ Failed to send user confirmation email: {str(e)}")
        import traceback
        app.logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

def get_setting(key, default=None):
    """Get a site setting by key"""
    try:
        setting = SiteSetting.query.filter_by(key=key).first()
        return setting.value if setting else default
    except Exception as e:
        app.logger.error(f"Error getting setting {key}: {str(e)}")
        return default

# Make get_setting available to all templates
@app.context_processor
def utility_processor():
    return dict(get_setting=get_setting)

# Make current datetime available to all templates as 'now'
@app.context_processor
def utility_processor():
    def now(format=None):
        if format:
            return datetime.utcnow().strftime(format)
        return datetime.utcnow()
    
    return dict(now=now, get_setting=get_setting)

# ========== TEMPLATE UTILITIES ==========
@app.context_processor
def utility_processor():
    """Make common utilities and data available to all templates"""
    
    def get_setting(key, default=None):
        """Get a site setting by key"""
        try:
            setting = SiteSetting.query.filter_by(key=key).first()
            return setting.value if setting else default
        except Exception as e:
            app.logger.error(f"Error getting setting {key}: {str(e)}")
            return default
    
    def now(format=None):
        """Get current datetime, optionally formatted"""
        current_time = datetime.utcnow()
        if format:
            return current_time.strftime(format)
        return current_time
    
    def current_year():
        """Get current year for copyright notices"""
        return datetime.utcnow().year
    
    # Get skills for global template access
    def get_all_skills():
        try:
            return Skill.query.filter_by(featured=True).all()
        except Exception as e:
            app.logger.error(f"Error loading skills: {str(e)}")
            return []
    
    return dict(
        get_setting=get_setting,
        now=now,
        current_year=current_year,
        skills=get_all_skills()  
    )

# Initialize database on first request
@app.before_request
def initialize_database():
    """Initialize database on first request"""
    if not hasattr(app, 'db_initialized'):
        init_db()
        app.db_initialized = True

# ========== ROUTES ==========
@app.route('/')
def index():
    try:
        projects = Project.query.filter_by(featured=True).limit(6).all()
        testimonials = Testimonial.query.filter_by(featured=True).all()
        skills = Skill.query.filter_by(featured=True).all()
        latest_posts = BlogPost.query.filter_by(published=True).limit(3).all()
        return render_template('index.html', 
                             projects=projects, 
                             testimonials=testimonials, 
                             skills=skills, 
                             blog_posts=latest_posts)
    except Exception as e:
        app.logger.error(f"Error loading index: {str(e)}")
        return render_template('index.html', 
                             projects=[], 
                             testimonials=[], 
                             skills=[], 
                             blog_posts=[])

@app.route('/projects')
def projects():
    try:
        category = request.args.get('category', 'all')
        query = Project.query
        if category != 'all':
            query = query.filter(Project.category == category)
        projects = query.order_by(Project.created_at.desc()).all()
        categories = db.session.query(Project.category).distinct().all()
        return render_template('projects.html', 
                             projects=projects, 
                             categories=categories, 
                             selected_category=category)
    except Exception as e:
        app.logger.error(f"Error loading projects: {str(e)}")
        return render_template('projects.html', projects=[], categories=[], selected_category='all')

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        project.views += 1
        db.session.commit()
        return render_template('project_detail.html', project=project)
    except Exception as e:
        app.logger.error(f"Error loading project {project_id}: {str(e)}")
        flash('Project not found', 'error')
        return redirect(url_for('projects'))

@app.route('/blog')
def blog():
    try:
        posts = BlogPost.query.filter_by(published=True).order_by(BlogPost.created_at.desc()).all()
        return render_template('blog/list.html', posts=posts)
    except Exception as e:
        app.logger.error(f"Error loading blog: {str(e)}")
        return render_template('blog/list.html', posts=[])

@app.route('/blog/<slug>')
def blog_post(slug):
    try:
        post = BlogPost.query.filter_by(slug=slug, published=True).first_or_404()
        post.views += 1
        db.session.commit()
        html_content = markdown.markdown(post.content)
        return render_template('blog/single.html', post=post, content=html_content)
    except Exception as e:
        app.logger.error(f"Error loading blog post {slug}: {str(e)}")
        flash('Blog post not found', 'error')
        return redirect(url_for('blog'))

@app.route('/contact', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        try:
            app.logger.info("📝 Contact form submitted and validated")
            app.logger.info(f"📝 Form data - Name: {form.name.data}, Email: {form.email.data}")
            
            message = ContactMessage(
                name=form.name.data,
                email=form.email.data,
                subject=form.subject.data,
                message=form.message.data,
                ip_address=request.remote_addr
            )
            
            db.session.add(message)
            db.session.commit()
            app.logger.info(f"💾 Message saved to database with ID: {message.id}")
            
            # Send notification to admin (you)
            app.logger.info("📧 Attempting to send admin notification...")
            admin_notification_sent = send_email_notification(message)
            
            # Send confirmation to user
            app.logger.info("📧 Attempting to send user confirmation...")
            user_confirmation_sent = send_user_confirmation_email(message)
            
            # Detailed success reporting
            if admin_notification_sent and user_confirmation_sent:
                app.logger.info("✅ Both emails sent successfully")
                flash('Your message has been sent successfully! A confirmation email has been sent to your inbox.', 'success')
            elif admin_notification_sent:
                app.logger.warning("⚠️ Admin notification sent but user confirmation failed")
                flash('Your message has been received! However, there was an issue sending the confirmation email.', 'warning')
            elif user_confirmation_sent:
                app.logger.warning("⚠️ User confirmation sent but admin notification failed")
                flash('Your message has been received! However, there was an issue with our notification system.', 'warning')
            else:
                app.logger.error("❌ Both emails failed to send")
                flash('Your message has been saved! However, there was an issue with our email system. We will contact you soon.', 'warning')
                
            return redirect(url_for('contact'))
            
        except Exception as e:
            app.logger.error(f"❌ Error in contact form: {str(e)}")
            import traceback
            app.logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            flash('Sorry, there was an error sending your message. Please try again.', 'error')
    
    elif request.method == 'POST':
        # Form didn't validate
        app.logger.warning("⚠️ Form validation failed")
        app.logger.warning(f"⚠️ Form errors: {form.errors}")
    
    return render_template('contact.html', form=form)

@app.route('/debug/messages')
def debug_messages():
    """Temporary route to check saved contact messages"""
    try:
        messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
        result = []
        for msg in messages:
            result.append({
                'id': msg.id,
                'name': msg.name,
                'email': msg.email,
                'subject': msg.subject,
                'created_at': msg.created_at.isoformat(),
                'read': msg.read
            })
        return jsonify({'messages': result, 'count': len(result)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/test-simple-email')
def test_simple_email():
    """Test with simplest possible email"""
    try:
        msg = Message(
            subject="Simple Test from Contact Form",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=['devil160907@gmail.com'],  # Send to yourself
            body="This is a simple test email from your contact form system."
        )
        mail.send(msg)
        return jsonify({'status': 'success', 'message': 'Simple email sent!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/test-email-config')
def test_email_config():
    """Test email configuration"""
    try:
        # Test configuration
        config_status = {
            'MAIL_SERVER': app.config.get('MAIL_SERVER'),
            'MAIL_PORT': app.config.get('MAIL_PORT'),
            'MAIL_USE_TLS': app.config.get('MAIL_USE_TLS'),
            'MAIL_USE_SSL': app.config.get('MAIL_USE_SSL'),
            'MAIL_USERNAME': bool(app.config.get('MAIL_USERNAME')),
            'MAIL_PASSWORD': bool(app.config.get('MAIL_PASSWORD')),
            'MAIL_DEFAULT_SENDER': app.config.get('MAIL_DEFAULT_SENDER'),
            'MAIL_SUPPRESS_SEND': app.config.get('MAIL_SUPPRESS_SEND', False)
        }
        
        return jsonify({
            'status': 'configuration_checked',
            'config': config_status,
            'message': 'Check the server logs for email sending status'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/test-email-send')
def test_email_send():
    """Test actual email sending"""
    try:
        app.logger.info("🧪 Starting email send test...")
        
        # Check if we should even attempt to send emails
        if app.config.get('MAIL_SUPPRESS_SEND', False):
            return jsonify({
                'status': 'suppressed', 
                'message': 'Email sending is suppressed in development'
            })
        
        # Validate essential configuration
        required_config = ['MAIL_SERVER', 'MAIL_USERNAME', 'MAIL_PASSWORD']
        for config_key in required_config:
            if not app.config.get(config_key):
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required email configuration: {config_key}'
                }), 500
        
        # Try to send the email directly
        try:
            msg = Message(
                subject="Portfolio Test Email",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[app.config['MAIL_DEFAULT_SENDER']],
                body="This is a test email from your portfolio application. If you're reading this, your email configuration is working correctly!"
            )
            
            # SIMPLIFIED HTML - No complex CSS that could cause parsing issues
            msg.html = """
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd;">
                    <h2 style="color: #333;">✅ Portfolio Email Test</h2>
                    <p style="color: #666;">If you're reading this, your email configuration is working correctly!</p>
                    <p style="color: #666;"><strong>Test Time:</strong> {}</p>
                    <hr style="border: none; border-top: 1px solid #eee;">
                    <p style="color: #999; font-size: 12px;">This is a test email from your portfolio application.</p>
                </div>
            </body>
            </html>
            """.format(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
            
            app.logger.info("📧 Attempting to send test email...")
            mail.send(msg)
            app.logger.info("✅ Test email sent successfully!")
            
            return jsonify({
                'status': 'success',
                'message': 'Test email sent successfully! Check your inbox and server logs.'
            })
            
        except Exception as email_error:
            app.logger.error(f"❌ Email sending error: {str(email_error)}")
            app.logger.error(f"❌ Error type: {type(email_error).__name__}")
            
            # More detailed error information
            error_details = str(email_error)
            return jsonify({
                'status': 'error',
                'message': f'Failed to send email: {error_details}',
                'error_type': type(email_error).__name__
            }), 500
            
    except Exception as e:
        app.logger.error(f"❌ Test email error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Test failed: {str(e)}'
        }), 500

@app.route('/test-contact-email')
def test_contact_email():
    """Test the actual contact form email function"""
    try:
        # Create a mock contact message
        class MockMessage:
            def __init__(self):
                self.id = 999
                self.name = "Test User"
                self.email = "test@example.com"
                self.subject = "Test Contact Form"
                self.message = "This is a test message from the contact form."
                self.ip_address = "127.0.0.1"
                self.created_at = datetime.utcnow()
        
        mock_message = MockMessage()
        
        # Test the actual function
        success = send_email_notification(mock_message)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Contact form email sent successfully!'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Contact form email failed (check logs)'
            }), 500
            
    except Exception as e:
        app.logger.error(f"❌ Contact email test failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Contact email test failed: {str(e)}'
        }), 500

@app.route('/test-user-confirmation-email')
def test_user_confirmation_email():
    """Test the user confirmation email function"""
    try:
        # Create a mock contact message
        class MockMessage:
            def __init__(self):
                self.id = 999
                self.name = "Test User"
                self.email = "fiscalflow.service@gmail.com"  # Send to yourself for testing
                self.subject = "Test User Confirmation"
                self.message = "This is a test of the user confirmation email."
                self.ip_address = "127.0.0.1"
                self.created_at = datetime.utcnow()
        
        mock_message = MockMessage()
        
        # Test the user confirmation function
        success = send_user_confirmation_email(mock_message)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'User confirmation email sent successfully!'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'User confirmation email failed (check logs)'
            }), 500
            
    except Exception as e:
        app.logger.error(f"❌ User confirmation email test failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'User confirmation email test failed: {str(e)}'
        }), 500
    
@app.route('/resume')
def resume():
    return render_template('resume.html')

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.username.data, is_admin=True).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                flash('Logged in successfully!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid username or password', 'error')
        except Exception as e:
            app.logger.error(f"Login error: {str(e)}")
            flash('Login error. Please try again.', 'error')
    return render_template('admin/login.html', form=form)

@app.route('/download/resume')
def download_resume():
    """Serve resume file in requested format with Burhan Ahmed's name"""
    try:
        format_type = request.args.get('format', 'pdf').lower()
        name = request.args.get('name', 'Burhan_Ahmed')
        
        app.logger.info(f"📥 Resume download requested - Format: {format_type}, Name: {name}")
        
        # For PDF, generate from the actual resume template data
        if format_type == 'pdf':
            return generate_resume_from_template_pdf(name)
        else:
            # For other formats, you might want to implement differently
            flash(f'Currently only PDF format is available.', 'info')
            return generate_resume_from_template_pdf(name)
        
    except Exception as e:
        app.logger.error(f"❌ Error downloading resume: {str(e)}")
        flash('Error downloading resume. Please try again.', 'error')
        return redirect(url_for('resume'))

def generate_resume_from_template_pdf(filename="templates/resume.pdf"):
    """Generate PDF from the actual resume template data"""
    try:
        # Import necessary libraries
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib.units import inch, cm
            from reportlab.lib import colors
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            import io
        except ImportError as e:
            app.logger.error(f"❌ ReportLab not installed: {str(e)}")
            flash('PDF generation requires ReportLab library. Please install it.', 'error')
            return redirect(url_for('resume'))

        # Create PDF in memory
        buffer = io.BytesIO()
        
        # Use A4 for better international compatibility
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            topMargin=1*cm,
            bottomMargin=1*cm,
            leftMargin=1.5*cm,
            rightMargin=1.5*cm
        )
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2E86AB'),
            alignment=1,  # Center
            spaceAfter=12
        )
        
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#666666'),
            alignment=1,
            spaceAfter=24
        )
        
        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2E86AB'),
            spaceBefore=12,
            spaceAfter=6
        )
        
        story = []
        
        # ===== HEADER SECTION =====
        story.append(Paragraph("BURHAN AHMED", title_style))
        story.append(Paragraph("Full Stack Developer & Python Expert", subtitle_style))
        
        # Contact Information - Matching resume.html
        contact_info = [
            ["Email:", "devil160907@gmail.com"],
            ["Phone:", "+92 312 2626262"],
            ["Location:", "Karachi, Pakistan"],
            ["LinkedIn:", "linkedin.com/in/burhan-ahmed"],
            ["GitHub:", "github.com/burhan-ahmed"],
            ["Portfolio:", "burhanahmed.dev"]
        ]
        
        # Create contact table
        contact_rows = []
        for label, value in contact_info:
            contact_rows.append([
                Paragraph(f"<b>{label}</b>", styles['Normal']),
                Paragraph(value, styles['Normal'])
            ])
        
        contact_table = Table(contact_rows, colWidths=[2.5*cm, 12*cm])
        contact_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(contact_table)
        story.append(Spacer(1, 0.4*cm))
        
        # ===== PROFESSIONAL SUMMARY =====
        story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
        
        summary_text = """
        Passionate Full Stack Developer with 3+ years of experience building scalable web applications 
        using modern technologies. Strong expertise in Python, Flask, Django, React, and cloud technologies. 
        Proven track record of delivering high-quality software solutions that drive business growth and 
        improve user experience.
        """
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 0.2*cm))
        
        # Summary highlights from resume.html
        highlights = [
            "3+ years professional development experience",
            "25+ successful projects delivered",
            "Expert in Python & JavaScript ecosystems",
            "Strong problem-solving and analytical skills",
            "Experience with Agile methodologies"
        ]
        
        for highlight in highlights:
            story.append(Paragraph(f"• {highlight}", styles['Normal']))
        
        story.append(Spacer(1, 0.4*cm))
        
        # ===== TECHNICAL SKILLS =====
        story.append(Paragraph("TECHNICAL SKILLS", section_style))
        
        # Backend Skills
        story.append(Paragraph("Backend", styles['Heading3']))
        backend_skills = "Python, Flask, Django, FastAPI, Node.js, PostgreSQL, MySQL, MongoDB, REST APIs, GraphQL"
        story.append(Paragraph(backend_skills, styles['Normal']))
        story.append(Spacer(1, 0.2*cm))
        
        # Frontend Skills
        story.append(Paragraph("Frontend", styles['Heading3']))
        frontend_skills = "JavaScript, React, Vue.js, HTML5, CSS3, SASS, TypeScript, Tailwind CSS, Bootstrap"
        story.append(Paragraph(frontend_skills, styles['Normal']))
        story.append(Spacer(1, 0.2*cm))
        
        # DevOps Skills
        story.append(Paragraph("DevOps & Tools", styles['Heading3']))
        devops_skills = "Docker, AWS, Git, GitHub, CI/CD, Linux, Nginx, Jenkins, Redis, Celery"
        story.append(Paragraph(devops_skills, styles['Normal']))
        story.append(Spacer(1, 0.4*cm))
        
        # ===== WORK EXPERIENCE =====
        story.append(Paragraph("WORK EXPERIENCE", section_style))
        
        # Experience 1 - Senior Full Stack Developer
        story.append(Paragraph("Senior Full Stack Developer", styles['Heading3']))
        
        exp1_meta = Table([
            [Paragraph("Tech Innovations Pakistan", styles['Normal']), 
             Paragraph("2022 - Present", ParagraphStyle('DateStyle', parent=styles['Normal'], alignment=2))]
        ], colWidths=[12*cm, 3*cm])
        story.append(exp1_meta)
        
        exp1_points = [
            "Developed and maintained 12+ web applications serving 100,000+ monthly users",
            "Reduced application load time by 45% through performance optimization and caching strategies",
            "Implemented CI/CD pipelines reducing deployment time by 70% and improving deployment reliability",
            "Led a team of 4 junior developers, conducting code reviews and mentoring sessions",
            "Integrated third-party APIs including payment gateways, SMS services, and cloud storage"
        ]
        
        for point in exp1_points:
            story.append(Paragraph(f"• {point}", styles['Normal']))
        
        story.append(Spacer(1, 0.3*cm))
        
        # Technologies used
        tech_used1 = "Technologies: Python, Flask, React, PostgreSQL, AWS, Docker, Redis, Celery"
        story.append(Paragraph(tech_used1, ParagraphStyle('TechStyle', parent=styles['Italic'], fontSize=9, textColor=colors.grey)))
        
        story.append(Spacer(1, 0.3*cm))
        
        # Experience 2 - Full Stack Developer
        story.append(Paragraph("Full Stack Developer", styles['Heading3']))
        
        exp2_meta = Table([
            [Paragraph("Digital Solutions Co.", styles['Normal']), 
             Paragraph("2021 - 2022", ParagraphStyle('DateStyle', parent=styles['Normal'], alignment=2))]
        ], colWidths=[12*cm, 3*cm])
        story.append(exp2_meta)
        
        exp2_points = [
            "Built 18+ responsive web applications from concept to deployment using modern frameworks",
            "Integrated third-party APIs including Stripe, Twilio, and Google Maps",
            "Improved code quality by 40% through implementing testing standards and code review processes",
            "Collaborated with UI/UX designers to create pixel-perfect, user-friendly interfaces",
            "Optimized database queries reducing page load times by 30%"
        ]
        
        for point in exp2_points:
            story.append(Paragraph(f"• {point}", styles['Normal']))
        
        story.append(Spacer(1, 0.3*cm))
        
        # Technologies used
        tech_used2 = "Technologies: JavaScript, Vue.js, Node.js, MongoDB, Express, MySQL, REST APIs"
        story.append(Paragraph(tech_used2, ParagraphStyle('TechStyle', parent=styles['Italic'], fontSize=9, textColor=colors.grey)))
        
        story.append(Spacer(1, 0.3*cm))
        
        # Experience 3 - Junior Web Developer
        story.append(Paragraph("Junior Web Developer", styles['Heading3']))
        
        exp3_meta = Table([
            [Paragraph("Startup Ventures PK", styles['Normal']), 
             Paragraph("2020 - 2021", ParagraphStyle('DateStyle', parent=styles['Normal'], alignment=2))]
        ], colWidths=[12*cm, 3*cm])
        story.append(exp3_meta)
        
        exp3_points = [
            "Developed frontend components and backend APIs for various web applications",
            "Participated in agile development processes and daily standups",
            "Gained experience with version control (Git) and collaboration tools",
            "Built responsive websites using modern CSS frameworks and JavaScript",
            "Contributed to open-source projects and participated in hackathons"
        ]
        
        for point in exp3_points:
            story.append(Paragraph(f"• {point}", styles['Normal']))
        
        story.append(Spacer(1, 0.3*cm))
        
        # Technologies used
        tech_used3 = "Technologies: HTML/CSS, JavaScript, Python, Flask, MySQL, Bootstrap"
        story.append(Paragraph(tech_used3, ParagraphStyle('TechStyle', parent=styles['Italic'], fontSize=9, textColor=colors.grey)))
        
        story.append(Spacer(1, 0.4*cm))
        
        # ===== EDUCATION =====
        story.append(Paragraph("EDUCATION", section_style))
        
        # Education 1
        story.append(Paragraph("Bachelor of Science in Computer Science", styles['Heading3']))
        
        edu1_meta = Table([
            [Paragraph("University of Karachi", styles['Normal']), 
             Paragraph("2019 - 2023", ParagraphStyle('DateStyle', parent=styles['Normal'], alignment=2))]
        ], colWidths=[12*cm, 3*cm])
        story.append(edu1_meta)
        
        edu1_desc = "Graduated with distinction. Focus on Software Engineering, Web Technologies, and Artificial Intelligence. Relevant coursework: Data Structures, Algorithms, Database Systems, Web Development."
        story.append(Paragraph(edu1_desc, styles['Normal']))
        
        story.append(Spacer(1, 0.3*cm))
        
        # Education 2
        story.append(Paragraph("Advanced Python Programming", styles['Heading3']))
        
        edu2_meta = Table([
            [Paragraph("Coursera", styles['Normal']), 
             Paragraph("2022", ParagraphStyle('DateStyle', parent=styles['Normal'], alignment=2))]
        ], colWidths=[12*cm, 3*cm])
        story.append(edu2_meta)
        
        edu2_desc = "Specialized course covering advanced Python concepts, web frameworks, and software architecture patterns."
        story.append(Paragraph(edu2_desc, styles['Normal']))
        
        story.append(Spacer(1, 0.4*cm))
        
        # ===== CERTIFICATIONS =====
        story.append(Paragraph("CERTIFICATIONS", section_style))
        
        certifications = [
            ("AWS Certified Cloud Practitioner", "2023"),
            ("Python Professional Certification", "2022"),
            ("Full Stack Web Development", "2021"),
            ("Django Web Framework Specialist", "2021")
        ]
        
        for cert_name, cert_year in certifications:
            cert_table = Table([
                [Paragraph(f"• {cert_name}", styles['Normal']), 
                 Paragraph(cert_year, ParagraphStyle('DateStyle', parent=styles['Normal'], alignment=2))]
            ], colWidths=[12*cm, 3*cm])
            story.append(cert_table)
        
        story.append(Spacer(1, 0.4*cm))
        
        # ===== LANGUAGES =====
        story.append(Paragraph("LANGUAGES", section_style))
        
        languages = [
            ("English", "Fluent"),
            ("Urdu", "Native"),
            ("Arabic", "Basic")
        ]
        
        for lang_name, lang_level in languages:
            lang_table = Table([
                [Paragraph(lang_name, styles['Normal']), 
                 Paragraph(lang_level, ParagraphStyle('LevelStyle', parent=styles['Normal'], alignment=2, textColor=colors.grey))]
            ], colWidths=[12*cm, 3*cm])
            story.append(lang_table)
        
        # Build the PDF
        doc.build(story)
        
        # Get the PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Save to static folder for future use
        static_dir = os.path.join(app.root_path, 'static', 'downloads')
        os.makedirs(static_dir, exist_ok=True)
        
        static_path = os.path.join(static_dir, 'resume.pdf')
        with open(static_path, 'wb') as f:
            f.write(pdf_data)
        
        app.logger.info(f"✅ Successfully generated professional resume PDF")
        
        # Create a new buffer for serving
        serve_buffer = io.BytesIO(pdf_data)
        serve_buffer.seek(0)
        
        return send_file(
            serve_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        app.logger.error(f"❌ Error generating resume PDF: {str(e)}")
        import traceback
        app.logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        # Fallback to existing file
        static_path = os.path.join(app.root_path, 'static', 'downloads', 'resume.pdf')
        if os.path.exists(static_path):
            app.logger.info("🔄 Serving existing resume file as fallback")
            return send_file(
                static_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
        
        # Ultimate fallback: redirect to resume page
        flash('Could not generate resume PDF. Please view the online version.', 'error')
        return redirect(url_for('resume'))

def generate_burhan_resume_pdf(filename):
    """Generate a professional PDF resume for Burhan Ahmed with proper error handling"""
    try:
        # Check if reportlab is available
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            import io
        except ImportError as e:
            app.logger.error(f"❌ ReportLab not installed: {str(e)}")
            # Fallback: redirect to a static PDF or show error
            flash('PDF generation requires ReportLab library. Please install it.', 'error')
            return redirect(url_for('resume'))

        # Create PDF in memory
        buffer = io.BytesIO()
        
        # Use SimpleDocTemplate for better layout control
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch
        )
        
        styles = getSampleStyleSheet()
        story = []
        
        # Header Section
        title_style = styles['Heading1']
        title_style.alignment = 1  # Center
        title_style.textColor = colors.HexColor('#2E86AB')
        
        story.append(Paragraph("BURHAN AHMED", title_style))
        story.append(Paragraph("Full Stack Developer & Python Expert", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        # Contact Information - Simple table
        contact_data = [
            ["Email: devil160907@gmail.com", "Phone: +92 312 2626262"],
            ["Location: Karachi, Pakistan", "Portfolio: burhanahmed.dev"],
            ["LinkedIn: linkedin.com/in/burhan-ahmed", "GitHub: github.com/burhan-ahmed"]
        ]
        
        contact_table = Table(contact_data, colWidths=[2.8*inch, 2.8*inch])
        contact_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(contact_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Professional Summary
        story.append(Paragraph("PROFESSIONAL SUMMARY", styles['Heading2']))
        summary_text = """
        Passionate Full Stack Developer with 3+ years of experience building scalable web applications 
        using modern technologies. Strong expertise in Python, Flask, Django, React, and cloud technologies. 
        Proven track record of delivering high-quality software solutions that drive business growth and 
        improve user experience.
        """
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Technical Skills
        story.append(Paragraph("TECHNICAL SKILLS", styles['Heading2']))
        
        skills_data = [
            ["Backend:", "Python, Flask, Django, FastAPI, Node.js, PostgreSQL, MySQL, MongoDB"],
            ["Frontend:", "JavaScript, React, Vue.js, HTML5, CSS3, TypeScript, Tailwind CSS"],
            ["DevOps & Tools:", "Docker, AWS, Git, GitHub, CI/CD, Linux, Nginx, Redis"]
        ]
        
        skills_table = Table(skills_data, colWidths=[1*inch, 4.6*inch])
        skills_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(skills_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Work Experience
        story.append(Paragraph("WORK EXPERIENCE", styles['Heading2']))
        
        # Experience 1
        story.append(Paragraph("Senior Full Stack Developer", styles['Heading3']))
        story.append(Paragraph("Tech Innovations Pakistan | 2022 - Present", styles['Italic']))
        
        exp1_points = [
            "Developed and maintained 12+ web applications serving 100,000+ monthly users",
            "Reduced application load time by 45% through performance optimization",
            "Implemented CI/CD pipelines reducing deployment time by 70%",
            "Led a team of 4 junior developers, conducting code reviews and mentoring"
        ]
        
        for point in exp1_points:
            story.append(Paragraph(f"• {point}", styles['Normal']))
        
        story.append(Spacer(1, 0.1*inch))
        
        # Experience 2
        story.append(Paragraph("Full Stack Developer", styles['Heading3']))
        story.append(Paragraph("Digital Solutions Co. | 2021 - 2022", styles['Italic']))
        
        exp2_points = [
            "Built 18+ responsive web applications from concept to deployment",
            "Integrated third-party APIs including Stripe, Twilio, and Google Maps",
            "Improved code quality by 40% through testing standards",
            "Optimized database queries reducing page load times by 30%"
        ]
        
        for point in exp2_points:
            story.append(Paragraph(f"• {point}", styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Build the PDF
        doc.build(story)
        
        # Get the PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Save to static folder for future use
        static_dir = os.path.join(app.root_path, 'static', 'downloads')
        os.makedirs(static_dir, exist_ok=True)
        
        static_path = os.path.join(static_dir, 'resume.pdf')
        with open(static_path, 'wb') as f:
            f.write(pdf_data)
        
        app.logger.info(f"✅ Successfully generated professional resume PDF for Burhan Ahmed")
        
        # Create a new buffer for serving
        serve_buffer = io.BytesIO(pdf_data)
        serve_buffer.seek(0)
        
        return send_file(
            serve_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        app.logger.error(f"❌ Error generating Burhan's resume PDF: {str(e)}")
        import traceback
        app.logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        # Fallback: try to serve existing file or show error
        static_path = os.path.join(app.root_path, 'static', 'downloads', 'resume.pdf')
        if os.path.exists(static_path):
            app.logger.info("🔄 Serving existing resume file as fallback")
            return send_file(
                static_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
        
        flash('Could not generate resume PDF. Please try again later.', 'error')
        return redirect(url_for('resume'))
    
@app.route('/test-pdf-generation')
def test_pdf_generation():
    """Test PDF generation independently"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        import io
        
        # Create a simple PDF to test
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.drawString(100, 750, "Test PDF Generation")
        p.drawString(100, 730, "Burhan Ahmed - Full Stack Developer")
        p.drawString(100, 710, "If you can see this, PDF generation works!")
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name='test_resume.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        return f"PDF Generation Error: {str(e)}", 500

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    try:
        # Basic stats
        stats = {
            'projects': Project.query.count(),
            'blog_posts': BlogPost.query.count(),
            'messages': ContactMessage.query.count(),
            'unread_messages': ContactMessage.query.filter_by(read=False).count(),
        }
        
        # Recent messages (last 5)
        recent_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
        
        # Recent projects (last 3)
        recent_projects = Project.query.order_by(Project.created_at.desc()).limit(3).all()
        
        # Recent activity (combining different types of activities)
        recent_activity = []
        
        # Add recent messages to activity
        for msg in recent_messages[:3]:
            recent_activity.append({
                'type': 'message',
                'text': f'New message from {msg.name}: {msg.subject}',
                'time': format_timesince(msg.created_at)
            })
        
        # Add recent projects to activity
        for project in recent_projects[:2]:
            recent_activity.append({
                'type': 'project',
                'text': f'Project created: {project.title}',
                'time': format_timesince(project.created_at)
            })
        
        # Add blog posts activity
        recent_posts = BlogPost.query.order_by(BlogPost.created_at.desc()).limit(2).all()
        for post in recent_posts:
            status = "Published" if post.published else "Draft"
            recent_activity.append({
                'type': 'blog',
                'text': f'Blog post {status}: {post.title}',
                'time': format_timesince(post.created_at)
            })
        
        # Sort activities by time (newest first)
        recent_activity.sort(key=lambda x: x['time'], reverse=True)
        
        return render_template('admin/dashboard.html', 
                             stats=stats, 
                             recent_messages=recent_messages,
                             recent_projects=recent_projects,
                             recent_activity=recent_activity[:5])  # Limit to 5 most recent
        
    except Exception as e:
        app.logger.error(f"Error loading admin dashboard: {str(e)}")
        flash('Error loading dashboard', 'error')
        return render_template('admin/dashboard.html', 
                             stats={}, 
                             recent_messages=[],
                             recent_projects=[],
                             recent_activity=[])

def format_timesince(dt):
    """Format datetime as human-readable time since"""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"
    
@app.route('/admin/blog/new', methods=['GET', 'POST'])
@login_required
def new_blog_post():
    form = BlogPostForm()
    if form.validate_on_submit():
        try:
            post = BlogPost(
                title=form.title.data,
                slug=form.slug.data,
                content=form.content.data,
                excerpt=form.excerpt.data,
                published=form.published.data,
                author_id=current_user.id
            )
            db.session.add(post)
            db.session.commit()
            flash('Blog post created successfully!', 'success')
            return redirect(url_for('admin_blog'))
        except Exception as e:
            app.logger.error(f"Error creating blog post: {str(e)}")
            flash('Error creating blog post', 'error')
    return render_template('admin/blog_form.html', form=form, title='New Blog Post')

# Add these routes after your existing admin routes

@app.route('/admin/messages/<int:message_id>/read', methods=['POST'])
@login_required
def mark_message_read(message_id):
    """Mark a message as read"""
    try:
        message = ContactMessage.query.get_or_404(message_id)
        message.read = True
        db.session.commit()
        flash('Message marked as read', 'success')
    except Exception as e:
        app.logger.error(f"Error marking message as read: {str(e)}")
        flash('Error marking message as read', 'error')
    
    # Redirect back to the previous page or messages list
    if request.referrer:
        return redirect(request.referrer)
    return redirect(url_for('admin_messages'))

@app.route('/admin/messages/<int:message_id>/delete', methods=['POST'])
@login_required
def delete_message(message_id):
    """Delete a message"""
    try:
        message = ContactMessage.query.get_or_404(message_id)
        db.session.delete(message)
        db.session.commit()
        flash('Message deleted successfully', 'success')
    except Exception as e:
        app.logger.error(f"Error deleting message: {str(e)}")
        flash('Error deleting message', 'error')
    
    return redirect(url_for('admin_messages'))

@app.route('/admin/messages/<int:message_id>')
@login_required
def view_message(message_id):
    """View a single message"""
    try:
        message = ContactMessage.query.get_or_404(message_id)
        # Mark as read when viewing
        if not message.read:
            message.read = True
            db.session.commit()
        return render_template('admin/message_detail.html', message=message)
    except Exception as e:
        app.logger.error(f"Error viewing message {message_id}: {str(e)}")
        flash('Error viewing message', 'error')
        return redirect(url_for('admin_messages'))

@app.route('/admin/projects')
@login_required
def admin_projects():
    try:
        projects = Project.query.order_by(Project.created_at.desc()).all()
        return render_template('admin/projects.html', projects=projects)
    except Exception as e:
        app.logger.error(f"Error loading admin projects: {str(e)}")
        flash('Error loading projects', 'error')
        return render_template('admin/projects.html', projects=[])

@app.route('/admin/projects/new', methods=['GET', 'POST'])
@login_required
def new_project():
    form = ProjectForm()
    if form.validate_on_submit():
        try:
            project = Project(
                title=form.title.data,
                description=form.description.data,
                technologies=form.technologies.data,
                github_url=form.github_url.data,
                live_url=form.live_url.data,
                featured=form.featured.data,
                category=form.category.data
            )
            if form.image.data:
                image_url = save_image(form.image.data)
                if image_url:
                    project.image_url = image_url
            
            db.session.add(project)
            db.session.commit()
            flash('Project created successfully!', 'success')
            return redirect(url_for('admin_projects'))
        except Exception as e:
            app.logger.error(f"Error creating project: {str(e)}")
            flash('Error creating project', 'error')
    return render_template('admin/project_form.html', form=form, title='New Project')

@app.route('/admin/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        form = ProjectForm(obj=project)
        if form.validate_on_submit():
            project.title = form.title.data
            project.description = form.description.data
            project.technologies = form.technologies.data
            project.github_url = form.github_url.data
            project.live_url = form.live_url.data
            project.featured = form.featured.data
            project.category = form.category.data
            if form.image.data:
                image_url = save_image(form.image.data)
                if image_url:
                    project.image_url = image_url
            db.session.commit()
            flash('Project updated successfully!', 'success')
            return redirect(url_for('admin_projects'))
        return render_template('admin/project_form.html', form=form, project=project, title='Edit Project')
    except Exception as e:
        app.logger.error(f"Error editing project {project_id}: {str(e)}")
        flash('Error editing project', 'error')
        return redirect(url_for('admin_projects'))

@app.route('/admin/projects/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        db.session.delete(project)
        db.session.commit()
        flash('Project deleted successfully!', 'success')
    except Exception as e:
        app.logger.error(f"Error deleting project {project_id}: {str(e)}")
        flash('Error deleting project', 'error')
    return redirect(url_for('admin_projects'))

@app.route('/admin/messages')
@login_required
def admin_messages():
    """Display all contact messages"""
    try:
        messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
        app.logger.info(f"Found {len(messages)} messages in database")
        
        # Log message details for debugging
        for msg in messages[:5]:  # Log first 5 messages
            app.logger.info(f"Message {msg.id}: {msg.name} - {msg.subject} - Read: {msg.read}")
        
        return render_template('admin/messages.html', messages=messages)
    except Exception as e:
        app.logger.error(f"Error loading messages: {str(e)}")
        flash('Error loading messages', 'error')
        return render_template('admin/messages.html', messages=[])

# API Routes
@app.route('/api/projects')
def api_projects():
    try:
        projects = Project.query.all()
        return jsonify([{
            'id': p.id,
            'title': p.title,
            'description': p.description,
            'technologies': p.technologies,
            'github_url': p.github_url,
            'image_url': p.image_url,
            'category': p.category,
            'views': p.views
        } for p in projects])
    except Exception as e:
        app.logger.error(f"API error - projects: {str(e)}")
        return jsonify({'error': 'Unable to fetch projects'}), 500

@app.route('/api/contact', methods=['POST'])
@limiter.limit("3 per minute")
def api_contact():
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ['name', 'email', 'subject', 'message']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        message = ContactMessage(
            name=data['name'],
            email=data['email'],
            subject=data['subject'],
            message=data['message'],
            ip_address=request.remote_addr
        )
        db.session.add(message)
        db.session.commit()
        send_email_notification(message)
        return jsonify({'message': 'Contact message sent successfully'}), 201
    except Exception as e:
        app.logger.error(f"API error - contact: {str(e)}")
        return jsonify({'error': 'Unable to send message'}), 500

# SocketIO Handlers
@socketio.on('connect')
def handle_connect():
    app.logger.info('Client connected to chat')

@socketio.on('chat_message')
def handle_chat_message(data):
    try:
        user_message = data.get('message', '').lower()
        responses = {
            'hello': 'Hello! How can I help you learn more about my skills and projects?',
            'hi': 'Hi there! Feel free to ask me about my experience or projects.',
            'project': 'Check out my projects section to see my work with modern technologies!',
            'skill': 'I work with Python, Flask, JavaScript, React, and more. See the skills section!',
            'default': "I'm an AI assistant for this portfolio. Ask me about projects, skills, or experience!"
        }
        response = responses['default']
        for keyword, reply in responses.items():
            if keyword in user_message and keyword != 'default':
                response = reply
                break
        emit('chat_response', {
            'message': response,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        app.logger.error(f"Chat error: {str(e)}")
        emit('chat_response', {
            'message': 'Sorry, I encountered an error. Please try again.',
            'timestamp': datetime.utcnow().isoformat()
        })

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    # You'll need to create a SettingsForm for this
    form = SettingsForm()
    
    if form.validate_on_submit():
        try:

            flash('Settings updated successfully!', 'success')
            return redirect(url_for('admin_settings'))
        except Exception as e:
            app.logger.error(f"Error updating settings: {str(e)}")
            flash('Error updating settings', 'error')

    return render_template('admin/settings.html', form=form)

# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403

@app.errorhandler(429)
def ratelimit_error(error):
    return render_template('429.html'), 429

def init_db():
    """Initialize database with proper error handling"""
    try:
        with app.app_context():
            # Try to create tables
            db.create_all()
            
            # Create admin user if none exists
            if not User.query.filter_by(is_admin=True).first():
                admin = User(
                    username='admin',
                    email='admin@portfolio.com',
                    is_admin=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                
                # Add sample data
                sample_project = Project(
                    title='Sample Project',
                    description='A wonderful sample project built with modern technologies.',
                    technologies='Python, Flask, React, SQLite',
                    featured=True,
                    category='Web Development'
                )
                db.session.add(sample_project)
                
                sample_skill = Skill(
                    name='Python',
                    category='Backend',
                    proficiency=90,
                    featured=True
                )
                db.session.add(sample_skill)
                
                db.session.commit()
                print("✅ Database initialized with sample data!")
            else:
                print("✅ Database already initialized")
                
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        # If database is corrupted, try to recreate it
        try:
            print("🔄 Attempting to recreate database...")
            # Get database path
            db_path = os.path.join(instance_path, 'portfolio.db')
            
            # Close all connections
            db.session.close_all()
            # Remove the corrupted database file
            if os.path.exists(db_path):
                os.remove(db_path)
                print("🗑️ Removed corrupted database file")
            
            # Recreate database
            with app.app_context():
                db.create_all()
                
                # Create admin user
                admin = User(
                    username='admin',
                    email='admin@portfolio.com',
                    is_admin=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                
                # Add sample data
                sample_project = Project(
                    title='Sample Project',
                    description='A wonderful sample project built with modern technologies.',
                    technologies='Python, Flask, React, SQLite',
                    featured=True,
                    category='Web Development'
                )
                db.session.add(sample_project)
                
                sample_skill = Skill(
                    name='Python',
                    category='Backend',
                    proficiency=90,
                    featured=True
                )
                db.session.add(sample_skill)
                
                db.session.commit()
                print("✅ Database recreated successfully!")
                
        except Exception as recovery_error:
            print(f"❌ Failed to recover database: {str(recovery_error)}")
            # Final fallback - use in-memory database
            print("🔄 Using in-memory database as fallback...")
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
            with app.app_context():
                db.create_all()
                # Create minimal admin user
                admin = User(
                    username='admin',
                    email='admin@portfolio.com',
                    is_admin=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ Using in-memory database (data will be lost on restart)")

@app.route('/test-email')
def test_email():
    """Test email configuration"""
    try:
        # Check configuration
        config_info = {
            'MAIL_SERVER': app.config['MAIL_SERVER'],
            'MAIL_PORT': app.config['MAIL_PORT'],
            'MAIL_USE_TLS': app.config['MAIL_USE_TLS'],
            'MAIL_USE_SSL': app.config['MAIL_USE_SSL'],
            'MAIL_USERNAME': app.config['MAIL_USERNAME'],
            'MAIL_DEFAULT_SENDER': app.config['MAIL_DEFAULT_SENDER'],
            'MAIL_SUPPRESS_SEND': app.config.get('MAIL_SUPPRESS_SEND', False)
        }
        
        # Try to send a test email
        if not app.config.get('MAIL_SUPPRESS_SEND', False):
            msg = Message(
                subject="Test Email from Portfolio",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[app.config['MAIL_DEFAULT_SENDER']],
                body="This is a test email from your portfolio application."
            )
            mail.send(msg)
            return jsonify({
                'status': 'success',
                'message': 'Test email sent successfully!',
                'config': config_info
            })
        else:
            return jsonify({
                'status': 'suppressed',
                'message': 'Email sending is suppressed in development',
                'config': config_info
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'config': config_info
        }), 500

# ========== APPLICATION STARTUP ==========
if __name__ == '__main__':
    print("🚀 Starting Flask Portfolio Application...")
    print("📁 Working directory:", basedir)
    print("🔧 Environment:", os.environ.get('FLASK_ENV', 'development'))
    
    try:
        # Initialize database
        with app.app_context():
            init_db()
        print("✅ Database initialized successfully!")
        
        # Start the application
        print("🌐 Server starting on http://0.0.0.0:5000")
        print("📱 Access via: http://localhost:5000")
        print("🛑 Press Ctrl+C to stop the server")
        
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=5000, 
            debug=app.config.get('DEBUG', False),
            allow_unsafe_werkzeug=True
        )
    except Exception as e:
        print(f"❌ Failed to start application: {str(e)}")
        print("💡 Try running: flask run")