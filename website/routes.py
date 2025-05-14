from flask import Blueprint, render_template, request, flash, redirect, url_for, Response
from .models import Contact, PhoneDetection
from . import db
from flask_login import login_required, current_user
from .forms import ContactForm
from .phone_detector import generate_phone_detection_frames  # ✅ Import the video generator

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('home.html')

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/faq')
def faq():
    return render_template('faq.html')

@main.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        new_message = Contact(name=form.name.data, email=form.email.data, message=form.message.data)
        db.session.add(new_message)
        db.session.commit()
        flash("Your message has been sent!", "success")
        return redirect(url_for('main.contact'))
    return render_template('contact.html', form=form)

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# ✅ Route to show the detection video stream
@main.route('/run_phone_detection')
@login_required
def run_phone_detection():
    return render_template('phone_detection.html')  # ✅ This should match your actual template name

# ✅ Route for video stream source
@main.route('/video_feed')
@login_required
def video_feed():
    return Response(generate_phone_detection_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
