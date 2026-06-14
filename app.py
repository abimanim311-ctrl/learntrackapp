from flask.sansio import scaffold
import os
import datetime
import time
import ssl
from flask import Flask, render_template, redirect, url_for, flash, request, current_app, abort
from werkzeug.utils import secure_filename

# Transparently map MySQLdb to PyMySQL if mysqlclient is not compiled/installed
try:
    import MySQLdb
except ImportError:
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        pass

from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField, DateField, FileField, DecimalField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, ValidationError

# Load Configuration
from config import Config

# Initialize Flask App
app = Flask(__name__)
app.config.from_object(Config)

# Configuration is loaded from the Config class in config.py

# Initialize Extensions
mysql = MySQL(app)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Resource library for rule-based recommendation system
RESOURCES_LIBRARY = [
    {"title": "Official Python Tutorial", "link": "https://docs.python.org/3/tutorial/index.html", "category": "Python", "type": "Documentation"},
    {"title": "Real Python Learning Path", "link": "https://realpython.com/", "category": "Python", "type": "Article"},
    {"title": "Python for Everybody Course", "link": "https://www.coursera.org/specializations/python", "category": "Python", "type": "Course"},
    {"title": "MDN Web Development Guide", "link": "https://developer.mozilla.org/", "category": "Web Development", "type": "Documentation"},
    {"title": "freeCodeCamp Responsive Web Design", "link": "https://www.freecodecamp.org/learn/2022/responsive-web-design/", "category": "Web Development", "type": "Course"},
    {"title": "CSS-Tricks Flexbox & Grid Guides", "link": "https://css-tricks.com/", "category": "Web Development", "type": "Article"},
    {"title": "W3Schools SQL Tutorial", "link": "https://www.w3schools.com/sql/", "category": "Databases", "type": "Tutorial"},
    {"title": "SQLZoo Interactive Exercises", "link": "https://sqlzoo.net/", "category": "Databases", "type": "Tutorial"},
    {"title": "Kaggle Introduction to SQL Course", "link": "https://www.kaggle.com/learn/intro-to-sql", "category": "Databases", "type": "Course"},
    {"title": "Kaggle Machine Learning Courses", "link": "https://www.kaggle.com/learn", "category": "Machine Learning", "type": "Course"},
    {"title": "Scikit-Learn Machine Learning Guide", "link": "https://scikit-learn.org/stable/user_guide.html", "category": "Machine Learning", "type": "Documentation"},
    {"title": "Andrew Ng's Machine Learning Course", "link": "https://www.coursera.org/specializations/machine-learning-introduction", "category": "Machine Learning", "type": "Course"},
    {"title": "Eloquent JavaScript Textbook", "link": "https://eloquentjavascript.net/", "category": "JavaScript", "type": "Documentation"},
    {"title": "JavaScript.info Core Tutorial", "link": "https://javascript.info/", "category": "JavaScript", "type": "Tutorial"},
    {"title": "Learning How to Learn (Coursera)", "link": "https://www.coursera.org/learn/learning-how-to-learn", "category": "General", "type": "Course"},
    {"title": "Thomas Frank Student Productivity Guides", "link": "https://collegeinfogeek.com/", "category": "General", "type": "Article"}
]


# User Representation class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email, password, learning_style, interests, profile_image, is_admin):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.learning_style = learning_style
        self.interests = interests
        self.profile_image = profile_image
        self.is_admin = bool(is_admin)

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cur.fetchone()
    cur.close()
    if user_data:
        return User(
            id=user_data['id'],
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password'],
            learning_style=user_data['learning_style'],
            interests=user_data['interests'],
            profile_image=user_data['profile_image'],
            is_admin=user_data['is_admin']
        )
    return None


# Flask-WTF Forms Definitions
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    learning_style = SelectField('Learning Style', choices=[
        ('Visual', 'Visual (Pictures, Diagrams)'),
        ('Auditory', 'Auditory (Lectures, Podcasts)'),
        ('Reading/Writing', 'Reading/Writing (Textbooks, Notes)'),
        ('Kinesthetic', 'Kinesthetic (Hands-on, Coding)')
    ], default='Visual')
    interests = TextAreaField('Learning Interests (Comma separated)', validators=[Optional()])
    profile_image = FileField('Profile Image Upload (Optional)', validators=[Optional()])
    submit = SubmitField('Register Account')

    def validate_username(self, username):
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s", (username.data,))
        user = cur.fetchone()
        cur.close()
        if user:
            raise ValidationError('Username is already taken. Please choose another one.')

    def validate_email(self, email):
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM users WHERE email = %s", (email.data,))
        user = cur.fetchone()
        cur.close()
        if user:
            raise ValidationError('Email is already registered. Please sign in instead.')

class LoginForm(FlaskForm):
    email = StringField('Email Address or Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class GoalForm(FlaskForm):
    title = StringField('Goal Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description / Objectives', validators=[Optional()])
    category = StringField('Category / Subject', validators=[DataRequired(), Length(max=50)])
    target_date = DateField('Target Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed')
    ], default='Pending')
    submit = SubmitField('Save Learning Goal')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=100)])
    learning_style = SelectField('Learning Style', choices=[
        ('Visual', 'Visual (Pictures, Diagrams)'),
        ('Auditory', 'Auditory (Lectures, Podcasts)'),
        ('Reading/Writing', 'Reading/Writing (Textbooks, Notes)'),
        ('Kinesthetic', 'Kinesthetic (Hands-on, Coding)')
    ])
    interests = TextAreaField('Interests (Comma separated)', validators=[Optional()])
    profile_image = FileField('Update Profile Image', validators=[Optional()])
    submit = SubmitField('Update Details')

class PasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='New passwords must match')])
    submit = SubmitField('Change Password')

class ProgressLogForm(FlaskForm):
    study_date = DateField('Study Date', validators=[DataRequired()])
    hours = DecimalField('Hours Studied', validators=[DataRequired()])
    topic = StringField('Topic Covered', validators=[DataRequired(), Length(max=150)])
    notes = TextAreaField('Study Notes', validators=[Optional()])
    submit = SubmitField('Update Progress Log')



# Helper Utilities
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def award_badge(user_id, badge_name):
    """Safely award a badge to a user if not already earned and trigger notification."""
    cur = mysql.connection.cursor()
    try:
        # Check if badge already exists
        cur.execute("SELECT id FROM badges WHERE user_id = %s AND badge_name = %s", (user_id, badge_name))
        if not cur.fetchone():
            cur.execute("INSERT INTO badges (user_id, badge_name) VALUES (%s, %s)", (user_id, badge_name))
            msg = f"Congratulations! You've unlocked the achievement badge: {badge_name}!"
            cur.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (user_id, msg))
            mysql.connection.commit()
            return True
    except Exception as e:
        print(f"Error awarding badge: {e}")
    finally:
        cur.close()
    return False

def update_streak(user_id, study_date):
    """Calculate and update study streak when user logs study hours."""
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT * FROM streaks WHERE user_id = %s", (user_id,))
        streak = cur.fetchone()
        
        if not streak:
            # First log ever
            cur.execute(
                "INSERT INTO streaks (user_id, current_streak, longest_streak, last_checkin) VALUES (%s, 1, 1, %s)",
                (user_id, study_date)
            )
            current_streak = 1
        else:
            last_checkin = streak['last_checkin']
            current_streak = streak['current_streak']
            longest_streak = streak['longest_streak']
            
            if last_checkin:
                if isinstance(last_checkin, str):
                    last_checkin_date = datetime.datetime.strptime(last_checkin, '%Y-%m-%d').date()
                else:
                    last_checkin_date = last_checkin
                
                # Check date difference
                diff = (study_date - last_checkin_date).days
                
                if diff == 1:
                    # Consecutive day study
                    current_streak += 1
                    if current_streak > longest_streak:
                        longest_streak = current_streak
                    cur.execute(
                        "UPDATE streaks SET current_streak = %s, longest_streak = %s, last_checkin = %s WHERE user_id = %s",
                        (current_streak, longest_streak, study_date, user_id)
                    )
                elif diff > 1:
                    # Streak broken (days missed), reset to 1
                    current_streak = 1
                    cur.execute(
                        "UPDATE streaks SET current_streak = 1, last_checkin = %s WHERE user_id = %s",
                        (study_date, user_id)
                    )
                # If diff == 0, study logged on same day, streak doesn't change
            else:
                current_streak = 1
                cur.execute(
                    "UPDATE streaks SET current_streak = 1, longest_streak = 1, last_checkin = %s WHERE user_id = %s",
                    (study_date, user_id)
                )
        mysql.connection.commit()
        
        # Award streak achievements based on streak milestones
        if current_streak >= 3:
            award_badge(user_id, '3 Day Streak')
        if current_streak >= 7:
            award_badge(user_id, '7 Day Streak')
        if current_streak >= 30:
            award_badge(user_id, '30 Day Streak')
            
    except Exception as e:
        print(f"Streak calculation error: {e}")
    finally:
        cur.close()

def refresh_recommendations(user_id):
    """Personalized learning recommendation system matching categories & interests."""
    cur = mysql.connection.cursor()
    try:
        # Fetch user interests
        cur.execute("SELECT interests FROM users WHERE id = %s", (user_id,))
        user_row = cur.fetchone()
        interests_str = user_row['interests'] if user_row and user_row['interests'] else ""
        interests = [term.strip().lower() for term in interests_str.split(',') if term.strip()]
        
        # Fetch active goal categories
        cur.execute("SELECT DISTINCT category FROM goals WHERE user_id = %s AND status != 'Completed'", (user_id,))
        active_cats = cur.fetchall()
        goal_categories = [cat['category'].strip().lower() for cat in active_cats]
        
        # Merge search keys
        search_terms = set(interests + goal_categories)
        
        matches = []
        for res in RESOURCES_LIBRARY:
            res_category = res['category'].lower()
            # Recommend matching topics or general study articles
            if res_category == 'general' or any(term in res_category or res_category in term for term in search_terms):
                matches.append(res)
                
        # Deduplicate and cap list at 4 items
        unique_matches = []
        seen_links = set()
        for m in matches:
            if m['link'] not in seen_links:
                seen_links.add(m['link'])
                unique_matches.append(m)
        
        final_recs = unique_matches[:4]
        
        # Delete old recommendations and update
        cur.execute("DELETE FROM recommendations WHERE user_id = %s", (user_id,))
        for rec in final_recs:
            cur.execute(
                "INSERT INTO recommendations (user_id, title, resource_link, category, resource_type) VALUES (%s, %s, %s, %s, %s)",
                (user_id, rec['title'], rec['link'], rec['category'], rec['type'])
            )
        mysql.connection.commit()
    except Exception as e:
        print(f"Recommendations error: {e}")
    finally:
        cur.close()

def run_background_checks(user_id):
    """Generate dynamic notifications for deadlines & missed study days."""
    cur = mysql.connection.cursor()
    try:
        today = datetime.date.today()
        
        # 1. Deadline reminders for goals (<= 3 days remaining)
        cur.execute("SELECT id, title, target_date FROM goals WHERE user_id = %s AND status != 'Completed'", (user_id,))
        active_goals = cur.fetchall()
        
        for goal in active_goals:
            target = goal['target_date']
            if isinstance(target, str):
                target = datetime.datetime.strptime(target, '%Y-%m-%d').date()
            
            days_left = (target - today).days
            if 0 <= days_left <= 3:
                msg = f"Reminder: Your goal '{goal['title']}' is due on {target} ({days_left} days remaining)."
                # Ensure we don't spam the database with duplicate unread alerts
                cur.execute("SELECT id FROM notifications WHERE user_id = %s AND message = %s AND is_read = FALSE", (user_id, msg))
                if not cur.fetchone():
                    cur.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (user_id, msg))
        
        # 2. Missed study log day (no progress logged for > 1 day)
        if active_goals:
            cur.execute("SELECT MAX(study_date) as last_date FROM progress_logs WHERE user_id = %s", (user_id,))
            log_row = cur.fetchone()
            last_date = log_row['last_date']
            
            days_since = 999
            if last_date:
                if isinstance(last_date, str):
                    last_date = datetime.datetime.strptime(last_date, '%Y-%m-%d').date()
                days_since = (today - last_date).days
                
            if days_since > 1:
                last_date_str = last_date.strftime('%Y-%m-%d') if last_date else "signup"
                msg = f"Don't lose momentum! You haven't logged study progress since {last_date_str}."
                cur.execute("SELECT id FROM notifications WHERE user_id = %s AND message = %s AND is_read = FALSE", (user_id, msg))
                if not cur.fetchone():
                    cur.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (user_id, msg))
        
        mysql.connection.commit()
    except Exception as e:
        print(f"Background check error: {e}")
    finally:
        cur.close()


# Context Processor to inject notification parameters into navbar/layout
@app.context_processor
def inject_notifications():
    if current_user.is_authenticated:
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT message, created_at FROM notifications WHERE user_id = %s AND is_read = FALSE ORDER BY created_at DESC",
            (current_user.id,)
        )
        unread = cur.fetchall()
        cur.close()
        return {
            'unread_notifications': unread,
            'unread_count': len(unread)
        }
    return {
        'unread_notifications': [],
        'unread_count': 0
    }

# Routing Handlers
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])

def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        cur = mysql.connection.cursor()
        # Allow signin with username or email
        cur.execute("SELECT * FROM users WHERE email = %s OR username = %s", (form.email.data, form.email.data))
        user_data = cur.fetchone()
        cur.close()
        
        if user_data and bcrypt.check_password_hash(user_data['password'], form.password.data):
            user = User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                learning_style=user_data['learning_style'],
                interests=user_data['interests'],
                profile_image=user_data['profile_image'],
                is_admin=user_data['is_admin']
            )
            login_user(user, remember=form.remember.data)
            flash('Signed in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check credentials.', 'danger')
            
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        profile_img = 'default_avatar.png'
        
        # Profile Picture Upload Handler
        if form.profile_image.data and form.profile_image.data.filename:
            file = form.profile_image.data
            if allowed_file(file.filename):
                filename = f"user_{int(time.time())}_{secure_filename(file.filename)}"
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                profile_img = filename
            else:
                flash('Invalid image format. Allowed formats: PNG, JPG, JPEG, GIF', 'danger')
                return render_template('auth/register.html', form=form)

        cur = mysql.connection.cursor()
        try:
            # Create user
            cur.execute(
                "INSERT INTO users (username, email, password, learning_style, interests, profile_image) VALUES (%s, %s, %s, %s, %s, %s)",
                (form.username.data, form.email.data, hashed_password, form.learning_style.data, form.interests.data, profile_img)
            )
            user_id = cur.lastrowid
            
            # Initialize streak record
            cur.execute("INSERT INTO streaks (user_id, current_streak, longest_streak) VALUES (%s, 0, 0)", (user_id,))

            
            # Welcome Notification
            cur.execute(
                "INSERT INTO notifications (user_id, message) VALUES (%s, 'Welcome to LearnTrack! Create your first learning goal to start.')",
                (user_id,)
            )
            mysql.connection.commit()
            
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error registering user: {e}", 'danger')
        finally:
            cur.close()

    return render_template('auth/register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Run dynamic alarms
    run_background_checks(current_user.id)
    # Update recommendation system
    refresh_recommendations(current_user.id)
    
    cur = mysql.connection.cursor()
    
    # 1. Fetch user stats
    cur.execute("SELECT * FROM streaks WHERE user_id = %s", (current_user.id,))
    streak_data = cur.fetchone() or {'current_streak': 0, 'longest_streak': 0}
    
    cur.execute("SELECT COUNT(*) as total FROM goals WHERE user_id = %s", (current_user.id,))
    total_goals = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as total FROM goals WHERE user_id = %s AND status = 'Completed'", (current_user.id,))
    completed_goals = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as total FROM goals WHERE user_id = %s AND status != 'Completed'", (current_user.id,))
    pending_goals = cur.fetchone()['total']
    
    cur.execute("SELECT SUM(hours) as total FROM progress_logs WHERE user_id = %s", (current_user.id,))
    total_hours = cur.fetchone()['total'] or 0.0
    
    stats = {
        'current_streak': streak_data['current_streak'],
        'longest_streak': streak_data['longest_streak'],
        'total_goals': total_goals,
        'completed_goals': completed_goals,
        'pending_goals': pending_goals,
        'total_hours': float(total_hours)
    }
    
    # 2. Fetch Active Goals for the Quick Log dropdown
    cur.execute("SELECT id, title, category FROM goals WHERE user_id = %s AND status != 'Completed'", (current_user.id,))
    active_goals = cur.fetchall()
    
    # 3. Fetch Recent Progress Logs (last 5)
    cur.execute(
        "SELECT p.*, g.title as goal_title, g.category as goal_category "
        "FROM progress_logs p "
        "JOIN goals g ON p.goal_id = g.id "
        "WHERE p.user_id = %s "
        "ORDER BY p.study_date DESC, p.created_at DESC LIMIT 5",
        (current_user.id,)
    )
    logs = cur.fetchall()
    
    # 4. Fetch Recommendations
    cur.execute("SELECT * FROM recommendations WHERE user_id = %s", (current_user.id,))
    recommendations = cur.fetchall()
    
    # 5. Fetch Earned Badges
    cur.execute("SELECT badge_name FROM badges WHERE user_id = %s", (current_user.id,))
    badges_rows = cur.fetchall()
    earned_badges = [row['badge_name'] for row in badges_rows]
    
    # 6. Check for active reminders
    today = datetime.date.today()
    reminders = []
    
    # Find active deadlines due within 3 days
    cur.execute("SELECT title, target_date FROM goals WHERE user_id = %s AND status != 'Completed'", (current_user.id,))
    goals_check = cur.fetchall()
    for g in goals_check:
        target = g['target_date']
        if isinstance(target, str):
            target = datetime.datetime.strptime(target, '%Y-%m-%d').date()
        days_left = (target - today).days
        if 0 <= days_left <= 3:
            reminders.append({
                'type': 'deadline',
                'title': g['title'],
                'date': target.strftime('%Y-%m-%d'),
                'days_left': days_left
            })
            
    # Missed checkin reminder
    cur.execute("SELECT MAX(study_date) as last_date FROM progress_logs WHERE user_id = %s", (current_user.id,))
    last_study = cur.fetchone()['last_date']
    if active_goals:
        days_since = 999
        if last_study:
            if isinstance(last_study, str):
                last_study = datetime.datetime.strptime(last_study, '%Y-%m-%d').date()
            days_since = (today - last_study).days
        if days_since > 1:
            last_study_str = last_study.strftime('%Y-%m-%d') if last_study else "signup"
            reminders.append({
                'type': 'missed_study',
                'message': f"You haven't logged study hours since {last_study_str}. Log progress to keep your streak!"
            })
            
    cur.close()
    
    return render_template(
        'dashboard/index.html',
        stats=stats,
        active_goals=active_goals,
        logs=logs,
        recommendations=recommendations,
        earned_badges=earned_badges,
        reminders=reminders,
        today_date=today.strftime('%Y-%m-%d')
    )

@app.route('/log_progress', methods=['POST'])
@login_required
def log_progress():
    goal_id = request.form.get('goal_id')
    study_date_str = request.form.get('study_date')
    hours = request.form.get('hours')
    topic = request.form.get('topic')
    notes = request.form.get('notes')
    
    if not (goal_id and study_date_str and hours and topic):
        flash('Please fill out all required fields to log progress.', 'warning')
        return redirect(url_for('dashboard'))
        
    try:
        hours_val = float(hours)
        study_date = datetime.datetime.strptime(study_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid progress log data formats.', 'danger')
        return redirect(url_for('dashboard'))
        
    cur = mysql.connection.cursor()
    try:
        # Verify goal ownership
        cur.execute("SELECT id FROM goals WHERE id = %s AND user_id = %s", (goal_id, current_user.id))
        if not cur.fetchone():
            flash('Access denied or invalid goal reference.', 'danger')
            return redirect(url_for('dashboard'))
            
        # Add log
        cur.execute(
            "INSERT INTO progress_logs (user_id, goal_id, study_date, hours, topic, notes) VALUES (%s, %s, %s, %s, %s, %s)",
            (current_user.id, goal_id, study_date, hours_val, topic, notes)
        )
        mysql.connection.commit()
        
        # Calculate streaks
        update_streak(current_user.id, study_date)
        
        flash('Study progress logged successfully!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error logging progress: {e}", 'danger')
    finally:
        cur.close()
        
    return redirect(url_for('dashboard'))

@app.route('/progress/delete/<int:log_id>', methods=['POST'])
@login_required
def delete_log(log_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT id FROM progress_logs WHERE id = %s AND user_id = %s", (log_id, current_user.id))
        if not cur.fetchone():
            flash('Log not found or access denied.', 'danger')
            return redirect(url_for('dashboard'))
            
        cur.execute("DELETE FROM progress_logs WHERE id = %s", (log_id,))
        mysql.connection.commit()
        flash('Study log deleted successfully.', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error deleting study log: {e}", 'danger')
    finally:
        cur.close()
    return redirect(url_for('dashboard'))

@app.route('/progress/edit/<int:log_id>', methods=['GET', 'POST'])
@login_required
def edit_log(log_id):
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT p.*, g.title as goal_title "
        "FROM progress_logs p "
        "JOIN goals g ON p.goal_id = g.id "
        "WHERE p.id = %s AND p.user_id = %s",
        (log_id, current_user.id)
    )
    log = cur.fetchone()
    cur.close()
    
    if not log:
        flash('Progress log not found or access denied.', 'danger')
        return redirect(url_for('dashboard'))
        
    form = ProgressLogForm()
    
    if form.validate_on_submit():
        cur = mysql.connection.cursor()
        try:
            cur.execute(
                "UPDATE progress_logs SET study_date = %s, hours = %s, topic = %s, notes = %s WHERE id = %s",
                (form.study_date.data, form.hours.data, form.topic.data, form.notes.data, log_id)
            )
            mysql.connection.commit()
            
            # Recalculate streak in case they updated study_date
            update_streak(current_user.id, form.study_date.data)
            
            flash('Progress log updated successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error updating progress log: {e}", 'danger')
        finally:
            cur.close()
            
    elif request.method == 'GET':
        s_date = log['study_date']
        if isinstance(s_date, str):
            form.study_date.data = datetime.datetime.strptime(s_date, '%Y-%m-%d').date()
        else:
            form.study_date.data = s_date
            
        form.hours.data = log['hours']
        form.topic.data = log['topic']
        form.notes.data = log['notes']
        
    return render_template('dashboard/edit_progress.html', form=form, goal_title=log['goal_title'])


# Goal Routes
@app.route('/goals')
@login_required
def goals_list():
    cur = mysql.connection.cursor()
    # Fetch active goals (Pending or In Progress) with total hours logged
    cur.execute(
        "SELECT g.*, SUM(p.hours) as total_hours "
        "FROM goals g "
        "LEFT JOIN progress_logs p ON g.id = p.goal_id "
        "WHERE g.user_id = %s AND g.status != 'Completed' "
        "GROUP BY g.id "
        "ORDER BY g.created_at DESC",
        (current_user.id,)
    )
    active = cur.fetchall()
    
    # Fetch completed goals
    cur.execute(
        "SELECT g.*, SUM(p.hours) as total_hours "
        "FROM goals g "
        "LEFT JOIN progress_logs p ON g.id = p.goal_id "
        "WHERE g.user_id = %s AND g.status = 'Completed' "
        "GROUP BY g.id "
        "ORDER BY g.created_at DESC",
        (current_user.id,)
    )
    completed = cur.fetchall()
    cur.close()
    
    return render_template('goals/index.html', active_goals=active, completed_goals=completed)

@app.route('/goals/add', methods=['GET', 'POST'])
@login_required
def add_goal():
    form = GoalForm()
    if form.validate_on_submit():
        cur = mysql.connection.cursor()
        try:
            cur.execute(
                "INSERT INTO goals (user_id, title, description, category, target_date, status) VALUES (%s, %s, %s, %s, %s, %s)",
                (current_user.id, form.title.data, form.description.data, form.category.data, form.target_date.data, form.status.data)
            )
            mysql.connection.commit()
            
            # Check for "First Goal" badge achievement
            cur.execute("SELECT COUNT(*) as count FROM goals WHERE user_id = %s", (current_user.id,))
            count = cur.fetchone()['count']
            if count == 1:
                award_badge(current_user.id, 'First Goal')
                
            flash('Goal created successfully!', 'success')
            return redirect(url_for('goals_list'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error creating goal: {e}", 'danger')
        finally:
            cur.close()
            
    return render_template('goals/add.html', form=form)

@app.route('/goals/edit/<int:goal_id>', methods=['GET', 'POST'])
@login_required
def edit_goal(goal_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM goals WHERE id = %s AND user_id = %s", (goal_id, current_user.id))
    goal = cur.fetchone()
    cur.close()
    
    if not goal:
        flash('Goal not found or access denied.', 'danger')
        return redirect(url_for('goals_list'))
        
    form = GoalForm()
    if form.validate_on_submit():
        cur = mysql.connection.cursor()
        try:
            cur.execute(
                "UPDATE goals SET title = %s, description = %s, category = %s, target_date = %s, status = %s WHERE id = %s",
                (form.title.data, form.description.data, form.category.data, form.target_date.data, form.status.data, goal_id)
            )
            mysql.connection.commit()
            
            # Check if updated to Completed
            if form.status.data == 'Completed':
                cur.execute("SELECT COUNT(*) as count FROM goals WHERE user_id = %s AND status = 'Completed'", (current_user.id,))
                completed_count = cur.fetchone()['count']
                if completed_count >= 5:
                    award_badge(current_user.id, 'Goal Master')
                    
            flash('Goal updated successfully.', 'success')
            return redirect(url_for('goals_list'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error updating goal: {e}", 'danger')
        finally:
            cur.close()
            
    elif request.method == 'GET':
        # Prepopulate values
        form.title.data = goal['title']
        form.description.data = goal['description']
        form.category.data = goal['category']
        # Extract date object
        t_date = goal['target_date']
        if isinstance(t_date, str):
            form.target_date.data = datetime.datetime.strptime(t_date, '%Y-%m-%d').date()
        else:
            form.target_date.data = t_date
        form.status.data = goal['status']
        
    return render_template('goals/edit.html', form=form)

@app.route('/goals/complete/<int:goal_id>', methods=['POST'])
@login_required
def complete_goal(goal_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT id, title FROM goals WHERE id = %s AND user_id = %s", (goal_id, current_user.id))
        goal = cur.fetchone()
        if not goal:
            flash('Goal not found or access denied.', 'danger')
            return redirect(url_for('goals_list'))
            
        cur.execute("UPDATE goals SET status = 'Completed' WHERE id = %s", (goal_id,))
        cur.execute(
            "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
            (current_user.id, f"Goal completed: '{goal['title']}'! Awesome job!")
        )
        mysql.connection.commit()
        
        # Check Goal Master badge (>= 5 completed goals)
        cur.execute("SELECT COUNT(*) as count FROM goals WHERE user_id = %s AND status = 'Completed'", (current_user.id,))
        completed_count = cur.fetchone()['count']
        if completed_count >= 5:
            award_badge(current_user.id, 'Goal Master')
            
        flash('Goal marked completed!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error completing goal: {e}", 'danger')
    finally:
        cur.close()
    return redirect(url_for('goals_list'))

@app.route('/goals/delete/<int:goal_id>', methods=['POST'])
@login_required
def delete_goal(goal_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT id FROM goals WHERE id = %s AND user_id = %s", (goal_id, current_user.id))
        if not cur.fetchone():
            flash('Goal not found or access denied.', 'danger')
            return redirect(url_for('goals_list'))
            
        cur.execute("DELETE FROM goals WHERE id = %s", (goal_id,))
        mysql.connection.commit()
        flash('Goal deleted successfully.', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error deleting goal: {e}", 'danger')
    finally:
        cur.close()
    return redirect(url_for('goals_list'))


# Notifications management
@app.route('/notifications/mark_all_read')
@login_required
def mark_all_notifications_read():
    cur = mysql.connection.cursor()
    try:
        cur.execute("UPDATE notifications SET is_read = TRUE WHERE user_id = %s", (current_user.id,))
        mysql.connection.commit()
        flash('Notifications cleared.', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error clearing notifications: {e}", 'danger')
    finally:
        cur.close()
    return redirect(request.referrer or url_for('dashboard'))


# Settings and profile management
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    password_form = PasswordForm()
    
    if form.validate_on_submit():
        profile_img = current_user.profile_image
        
        # New profile image file uploaded
        if form.profile_image.data and form.profile_image.data.filename:

            file = form.profile_image.data
            if allowed_file(file.filename):
                filename = f"user_{current_user.id}_{int(time.time())}_{secure_filename(file.filename)}"
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # Delete old avatar file if not default
                if current_user.profile_image and current_user.profile_image != 'default_avatar.png':
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_image)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass
                profile_img = filename
            else:
                flash('Invalid image format. Allowed formats: PNG, JPG, JPEG, GIF', 'danger')
                return redirect(url_for('profile'))

        cur = mysql.connection.cursor()
        try:
            # Check unique constraints on usernames/emails for other users
            cur.execute("SELECT id FROM users WHERE username = %s AND id != %s", (form.username.data, current_user.id))
            if cur.fetchone():
                flash('Username is already taken.', 'danger')
                return redirect(url_for('profile'))
                
            cur.execute("SELECT id FROM users WHERE email = %s AND id != %s", (form.email.data, current_user.id))
            if cur.fetchone():
                flash('Email is already registered.', 'danger')
                return redirect(url_for('profile'))
                
            cur.execute(
                "UPDATE users SET username = %s, email = %s, learning_style = %s, interests = %s, profile_image = %s WHERE id = %s",
                (form.username.data, form.email.data, form.learning_style.data, form.interests.data, profile_img, current_user.id)
            )
            mysql.connection.commit()
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error updating profile details: {e}", 'danger')
        finally:
            cur.close()
            
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.learning_style.data = current_user.learning_style
        form.interests.data = current_user.interests
        
    return render_template('profile/index.html', form=form, password_form=password_form)

@app.route('/profile/change_password', methods=['POST'])
@login_required
def change_password():
    password_form = PasswordForm()
    if password_form.validate_on_submit():
        cur = mysql.connection.cursor()
        cur.execute("SELECT password FROM users WHERE id = %s", (current_user.id,))
        hashed_pwd = cur.fetchone()['password']
        cur.close()
        
        # Verify current password
        if bcrypt.check_password_hash(hashed_pwd, password_form.current_password.data):
            new_hashed = bcrypt.generate_password_hash(password_form.new_password.data).decode('utf-8')
            cur = mysql.connection.cursor()
            try:
                cur.execute("UPDATE users SET password = %s WHERE id = %s", (new_hashed, current_user.id))
                mysql.connection.commit()
                flash('Password changed successfully!', 'success')
            except Exception as e:
                mysql.connection.rollback()
                flash(f"Error changing password: {e}", 'danger')
            finally:
                cur.close()
        else:
            flash('Verification of current password failed.', 'danger')
    else:
        for field, errors in password_form.errors.items():
            for err in errors:
                flash(f"{password_form[field].label.text}: {err}", 'danger')
                
    return redirect(url_for('profile'))


# Admin Routes
@app.route('/admin')
@login_required
def admin_dashboard():
    # Role gate checking
    if not current_user.is_admin:
        abort(403)
        
    cur = mysql.connection.cursor()
    
    # 1. Platform Statistics
    cur.execute("SELECT COUNT(*) as count FROM users")
    total_users = cur.fetchone()['count']
    
    cur.execute("SELECT COUNT(*) as count FROM goals")
    total_goals = cur.fetchone()['count']
    
    cur.execute("SELECT COUNT(*) as count FROM progress_logs")
    total_logs = cur.fetchone()['count']
    
    cur.execute("SELECT SUM(hours) as total FROM progress_logs")
    total_hours = cur.fetchone()['total'] or 0.0
    
    stats = {
        'total_users': total_users,
        'total_goals': total_goals,
        'total_logs': total_logs,
        'total_hours': float(total_hours)
    }
    
    # 2. View all Users
    cur.execute("SELECT id, username, email, learning_style, profile_image, is_admin FROM users ORDER BY username ASC")
    users = cur.fetchall()
    
    # 3. View all active Goals with creator username
    cur.execute(
        "SELECT g.*, u.username "
        "FROM goals g "
        "JOIN users u ON g.user_id = u.id "
        "ORDER BY g.created_at DESC"
    )
    goals = cur.fetchall()
    
    # 4. View recent progress logs
    cur.execute(
        "SELECT p.*, u.username, g.title as goal_title, g.category as goal_category "
        "FROM progress_logs p "
        "JOIN users u ON p.user_id = u.id "
        "JOIN goals g ON p.goal_id = g.id "
        "ORDER BY p.study_date DESC, p.created_at DESC LIMIT 15"
    )
    logs = cur.fetchall()
    cur.close()
    
    return render_template('admin/index.html', stats=stats, users=users, goals=goals, logs=logs)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        abort(403)
    # Prevent self-deletion
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    cur = mysql.connection.cursor()
    try:
        # Delete user avatar file if exists
        cur.execute("SELECT profile_image FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        if row and row['profile_image'] and row['profile_image'] != 'default_avatar.png':
            old_path = os.path.join(app.config['UPLOAD_FOLDER'], row['profile_image'])
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except OSError:
                    pass
                    
        # Perform cascade delete
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        mysql.connection.commit()
        flash('User account deleted successfully.', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error deleting user account: {e}", 'danger')
    finally:
        cur.close()
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_goal/<int:goal_id>', methods=['POST'])
@login_required
def admin_delete_goal(goal_id):
    if not current_user.is_admin:
        abort(403)
        
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM goals WHERE id = %s", (goal_id,))
        mysql.connection.commit()
        flash('Goal deleted successfully from platform.', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error moderating goal deletion: {e}", 'danger')
    finally:
        cur.close()
        
    return redirect(url_for('admin_dashboard'))


# Auto Database Schema Setup and Sample Seeding
def init_db():
    with app.app_context():
        try:
            # Check if users table exists
            cur = mysql.connection.cursor()
            cur.execute("SELECT 1 FROM users LIMIT 1")
            cur.close()
            print("Database tables are already initialized.")
        except Exception as e:
            print(f"Users table check failed: {e}")
            print("Initializing database tables from schema.sql...")
            try:
                schema_path = os.path.join(app.root_path, 'database', 'schema.sql')
                if os.path.exists(schema_path):
                    with open(schema_path, 'r', encoding='utf-8') as f:
                        schema_sql = f.read()
                    
                    # Clean comments and parse statements separated by semicolons
                    queries = []
                    current_query = []
                    for line in schema_sql.split('\n'):
                        line_stripped = line.strip()
                        if line_stripped.startswith('--') or line_stripped.startswith('/*') or not line_stripped:
                            continue
                        if ';' in line:
                            parts = line.split(';')
                            current_query.append(parts[0])
                            queries.append(' '.join(current_query).strip())
                            current_query = [parts[1]]
                        else:
                            current_query.append(line)
                            
                    cur = mysql.connection.cursor()
                    for q in queries:
                        if q.strip():
                            cur.execute(q)
                    mysql.connection.commit()
                    cur.close()
                    print("Schema imported successfully.")
                    
                    # Seed data
                    seed_path = os.path.join(app.root_path, 'database', 'sample_data.sql')
                    if os.path.exists(seed_path):
                        cur = mysql.connection.cursor()
                        cur.execute("SELECT COUNT(*) as count FROM users")
                        user_count = cur.fetchone()['count']
                        cur.close()
                        
                        if user_count == 0:
                            print("Seeding database with sample_data.sql...")
                            with open(seed_path, 'r', encoding='utf-8') as f:
                                seed_sql = f.read()
                            
                            queries = []
                            current_query = []
                            for line in seed_sql.split('\n'):
                                line_stripped = line.strip()
                                if line_stripped.startswith('--') or line_stripped.startswith('/*') or not line_stripped:
                                    continue
                                if ';' in line:
                                    parts = line.split(';')
                                    current_query.append(parts[0])
                                    queries.append(' '.join(current_query).strip())
                                    current_query = [parts[1]]
                                else:
                                    current_query.append(line)
                                    
                            cur = mysql.connection.cursor()
                            cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
                            for q in queries:
                                if q.strip():
                                    cur.execute(q)
                            cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
                            mysql.connection.commit()
                            cur.close()
                            print("Seeding completed.")
                else:
                    print(f"schema.sql not found at {schema_path}")
            except Exception as ex:
                print(f"Error during schema loading: {ex}")

if __name__ == '__main__':


    init_db()
    # Read port from environment variable (compatible with cloud runners)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
