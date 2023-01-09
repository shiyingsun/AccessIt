import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))

def register():
    # this function allows the user to register a new account
    containsNumber = False  # this bool variable checks if the password contains a number
    containsCapital = False  # this bool variable checks if the password contains a capital letter
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        db = get_db()
        error = None

        # this if statement makes sure that both the username and password fields are filled
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        # this if statement makes sure the password is at least 8 characters
        if len(password) < 8:
            error = 'Password needs to contain at least 8 characters'

        # makes sure the password contains a number and capital
        for i in password:
            if i.isdigit():
                containsNumber = True
            if i.isupper():
                containsCapital = True

        # this throws errors if the password doesn't meet requirements
        if not containsNumber:
            error = 'Password needs to contain a number'

        if not containsCapital:
            error = 'Password needs to contain a capital'

        if error is None:
            try:
                # this adds the user to the database if there isn't an error
                db.execute(
                    "INSERT INTO user (username, password,email) VALUES (?, ?,?)",
                    (username, generate_password_hash(password), email),
                )
                db.commit()
            except db.IntegrityError:
                # throw an error and doesn't allow user to proceed if the username is taken
                error = f"User {username} is already registered."
            else:
                # redirects user to login if registration is successful
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    # this function
    if request.method == 'POST':
        username = request.form['username']  # this links to the HTML of the inputs
        password = request.form['password']
        db = get_db()
        error = None
        # this looks for the username entered from the database
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        # This if statement checks the entered username and password against the database
        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        # if there are no errors, it allows the user to login and redirects to the 'posts' page
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Login needed to do this action")
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view