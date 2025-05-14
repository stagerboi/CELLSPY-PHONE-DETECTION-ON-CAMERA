from flask import Flask, render_template, redirect, url_for, request, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import InputRequired, Length, EqualTo, Email
from werkzeug.security import generate_password_hash, check_password_hash
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import os
import cv2
from ultralytics import YOLO

app = Flask(__name__)

# Paths and configs
db_path = os.path.join(app.root_path, 'instance', 'cellspy.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

if not os.path.exists(os.path.dirname(db_path)):
    os.makedirs(os.path.dirname(db_path))

app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and login
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# YOLO model
from ultralytics import YOLO
model = YOLO('yolov8n.pt')  # Or 'yolov8s.pt', etc.
camera = cv2.VideoCapture(0)

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Flask-Admin
admin = Admin(app, name='CellSpy Admin', template_mode='bootstrap3')
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Contact, db.session))

# Forms
class SignUpForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(), Length(min=3, max=100)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('password', message='Passwords must match')])

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(), Length(min=3, max=100)])
    password = PasswordField('Password', validators=[InputRequired()])

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[InputRequired(), Email(), Length(min=3, max=100)])
    message = TextAreaField('Message', validators=[InputRequired(), Length(min=10, max=500)])

# Video frame generator
import pygame
import threading
import time

# Load YOLO model
model = YOLO('yolov8n.pt')

# Constants
PHONE_CLASS_ID = 67  # COCO class ID for cell phone

# Sound setup
pygame.mixer.init()
alert_sound = pygame.mixer.Sound("static/sounds/alert.wav")
last_played_time = 0

def play_alert_sound():
    global last_played_time
    now = time.time()
    if now - last_played_time > 3:  # delay between alerts
        last_played_time = now
        threading.Thread(target=alert_sound.play, daemon=True).start()

# UPDATED generate_frames function
def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break

        results = model(frame, stream=True)

        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                if cls == PHONE_CLASS_ID:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = box.conf[0]
                    label = f"Phone {conf:.2f}"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                                0.6, (0, 0, 255), 2)
                    play_alert_sound()

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        new_message = Contact(name=form.name.data, email=form.email.data, message=form.message.data)
        db.session.add(new_message)
        db.session.commit()
        flash("Your message has been sent!", "success")
        return redirect(url_for('contact'))
    return render_template('contact.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email already exists!", "danger")
        else:
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')  
            new_user = User(email=form.email.data, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash("Account created successfully!", "success")
            return redirect(url_for('login'))
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash("Invalid email or password!", "danger")
    return render_template('login.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/run_phone_detection')
@login_required
def run_phone_detection():
    return render_template('detection_stream.html')

@app.route('/video_feed')
@login_required
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for('login'))

# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
