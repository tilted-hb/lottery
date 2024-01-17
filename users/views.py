# IMPORTS
import logging
from datetime import datetime

from flask import Blueprint, render_template, flash, redirect, url_for, session, request
from markupsafe import Markup

from app import db
from models import User
from users.forms import RegisterForm, LoginForm, ChangePasswordForm
from flask_login import login_user, current_user, logout_user, login_required

# CONFIG
users_blueprint = Blueprint('users', __name__, template_folder='templates')


# VIEWS
# view registration
@users_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # create signup form object
    form = RegisterForm()
    # check if user is anonymous
    if not current_user.is_anonymous:
        logging.warning('User [%s, id: %s, role: %s, %s] tried to access restricted page on [%s]',
                        current_user.email,
                        current_user.id,
                        current_user.role,
                        request.remote_addr,
                        datetime.now())

        return render_template('errors/403.html')

    # if request method is POST or form is valid
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # if this returns a user, then the email already exists in database

        # if email already exists redirect user back to signup page with error message so user can try again
        if user:
            flash('Email address already exists')
            return render_template('users/register.html', form=form)
        # get the registration date
        registered_on = datetime.now()

        # create a new user with the form data
        new_user = User(email=form.email.data,
                        firstname=form.firstname.data,
                        lastname=form.lastname.data,
                        # dob=form.dob.data,
                        phone=form.phone.data,
                        password=form.password.data,
                        role='user',
                        registered_on=registered_on)
        # log the registration of the user
        logging.warning('User [%s, %s] registered on %s',
                        form.email.data,
                        request.remote_addr,
                        registered_on)

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()
        # add the username to the session
        session['username'] = new_user.email
        # sends user to login page
        return redirect(url_for('users.setup_2fa'))
    # if request method is GET or form not valid re-render signup page
    return render_template('users/register.html', form=form)


# view user login
@users_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    # get the login form from the modules class
    form = LoginForm()
    # check if user is anonymous
    if not current_user.is_anonymous:
        # log restricted access
        logging.warning('User [%s, id: %s, role: %s, %s] tried to access restricted page on [%s]',
                        current_user.email,
                        current_user.id,
                        current_user.role,
                        request.remote_addr,
                        datetime.now())

        return render_template('errors/403.html')
    # if no attempts set to 0
    if not session.get('authentication_attempts'):
        session['authentication_attempts'] = 0

    if form.validate_on_submit():
        n = 3
        user = User.query.filter_by(email=form.email.data).first()
        # if login information is incorrect
        if not user or not user.verify_password(form.password.data) or not user.verify_pin(form.pin.data):
            # logg the failed attempt
            logging.warning('User [%s, %s] has failed the login attempt on [%s]',
                            form.email.data,
                            request.remote_addr,
                            datetime.now())
            # add one attempt
            session['authentication_attempts'] += 1
            # if 3 or more attempts block the form
            if session.get('authentication_attempts') >= 3:
                flash(Markup(
                    'Number of incorrect login attempts exceeded 3. Please click <a href="/reset">here</a> to reset.'))
                return render_template('users/login.html')
            attempts_remaining = n - session.get('authentication_attempts')
            flash(
                f'Invalid credentials, user does not exist, incorrect PIN or recaptcha is not completed! {attempts_remaining} login attempts remaining.')
            return render_template('users/login.html', form=form)
        # login the user
        login_user(user)
        # set authentication attempts to 0
        session['authentication_attempts'] = 0
        # set their last login to current login
        current_user.last_login = current_user.current_login
        # set their current login to current time
        current_user.current_login = datetime.now()
        db.session.commit()
        # log the login of the user
        logging.warning('User [%s, id: %s, %s] logged in on [%s], previous login [%s]',
                        form.email.data,
                        current_user.id,
                        request.remote_addr,
                        current_user.current_login,
                        current_user.last_login)
        # redirect to admin page if the users role is admin
        if current_user.role != 'user':
            return redirect(url_for('admin.admin'))
        # redirect to lottery page if user's role is user
        return redirect(url_for('lottery.lottery'))

    return render_template('users/login.html', form=form)


# logout function
@users_blueprint.route('/logout')
@login_required
def logout():
    # log the logout attempt
    logging.warning('User [%s, id: %s, %s] logged out on [%s]',
                    current_user.email,
                    current_user.id,
                    request.remote_addr,
                    datetime.now())
    # logout the user
    logout_user()
    session['authentication_attempts'] = 0

    return redirect(url_for('index'))


# view user account
@users_blueprint.route('/account')
@login_required
def account():
    return render_template('users/account.html',
                           acc_no=current_user.id,
                           email=current_user.email,
                           firstname=current_user.firstname,
                           lastname=current_user.lastname,
                           phone=current_user.phone)


# setup 2fa for the user page
@users_blueprint.route('/setup_2fa')
def setup_2fa():
    # check if user is not anonymous
    if not current_user.is_anonymous:
        logging.warning('User [%s, id: %s, role: %s, %s] tried to access restricted page on [%s]',
                        current_user.email,
                        current_user.id,
                        current_user.role,
                        request.remote_addr,
                        datetime.now())

        return render_template('errors/403.html')
    # check if user has just registered
    if 'username' not in session:
        return redirect(url_for('index'))
    # get the user by username
    user = User.query.filter_by(email=session['username']).first()

    if not user:
        return redirect(url_for('main.index'))
    # delete username from the session
    del session['username']

    return render_template('users/setup_2fa.html', email=user.email, uri=user.get_2fa_uri()), 200, {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }


# reset the login attempts of the user
@users_blueprint.route('/reset')
def reset():
    # check if the user is anonymous
    if not current_user.is_anonymous:
        logging.warning('User [%s, id: %s, role: %s, %s] tried to access restricted page on [%s]',
                        current_user.email,
                        current_user.id,
                        current_user.role,
                        request.remote_addr,
                        datetime.now())

        return render_template('errors/403.html')
    # reset the attempts
    session['authentication_attempts'] = 0
    return redirect(url_for('users.login'))


# view to change the password
@users_blueprint.route('/new_password', methods=('GET', 'POST'))
def change_password():
    form = ChangePasswordForm()
    # get the form from forms module
    # authentication check
    if not current_user.is_authenticated:
        return render_template('errors/403.html')

    if form.validate_on_submit():
        # check if current password match
        if form.current_password.data != current_user.password:
            flash('Current password does not match!')
            return render_template('users/new_password.html', form=form)
        # check if new password and current are the same
        if form.new_password.data == current_user.password:
            flash('New password cannot be same as previous!')
            return render_template('users/new_password.html', form=form)
        # update the password in the db
        current_user.password = form.new_password.data
        db.session.commit()

        return render_template('users/account.html',
                               message='Password changed successfully!',
                               acc_no=current_user.id,
                               email=current_user.email,
                               firstname=current_user.firstname,
                               lastname=current_user.lastname,
                               phone=current_user.phone)

    return render_template('users/new_password.html', form=form)
