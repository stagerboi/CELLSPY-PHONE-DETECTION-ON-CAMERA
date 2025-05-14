from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from .forms import SignupForm, LoginForm
from flask_login import login_user, logout_user, login_required

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Email already exists.', category='error')
        else:
            new_user = User(email=form.email.data, password=generate_password_hash(form.password.data, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully!', category='success')
            return redirect(url_for('auth.login'))
    return render_template('signup.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully!', category='success')
            return redirect(url_for('main.home'))
        else:
            flash('Incorrect email or password.', category='error')
    return render_template('login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', category='info')
    return redirect(url_for('auth.login'))
