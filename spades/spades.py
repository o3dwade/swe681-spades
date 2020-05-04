import re
import os
import logging

from passlib.hash import sha256_crypt
from flask import flash, redirect, url_for, request, render_template
from flask_login import LoginManager, login_required, login_user, logout_user

from spades.dbobjects import User
from . import app


retries = 0
logger = logging.getLogger('spades')
hdlr = logging.FileHandler(app.config['LOGFILE'])
logger.addHandler(hdlr)
login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/', methods=["GET", "POST"])
def login():
    global retries
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']

        if (__validate_input(username) and __verifyUser(username, password)):
            user = User(3)
            user.name = username
            login_user(user)
            return redirect(url_for('home', name=user.name))
        else:
            flash('Invalid credentials')
            logger.error('Invalid credentials for user' + username)
            retries = retries + 1
            return redirect(url_for('login'))
    else:
        return render_template('login.html')


@app.route('/home')
@app.route('/home/<name>')
def home(name=None):
    return render_template('home.html', name=name)


# callback to reload the user object
@login_manager.user_loader
def load_user(userid):
    return User.query.get(userid)


# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    return render_template('error.html'), 401


@app.route("/logout", methods=['GET'])
@login_required
def logout():
    logger.info(request.method)
    logout_user()
    return redirect(url_for('login'))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    logger.info(request.method)
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']

        if (__validate_input(username) == False):
            flash("Username is invalid")
            return redirect(url_for('signup'))
        if (__verifyExistingUser(username) == False):
            flash("User already exists.")
            return redirect(url_for('signup'))
        __registerUser(username, password)
        return redirect(url_for('login'))
    elif request.method == 'GET':
        return render_template("signup.html")


def __validate_input(input):
    if (len(input) < 5 or len(input) > 40):
        logger.error('Input length is incorrect for: ' + input)
        return False
    if re.match('^[A-Za-z0-9]+$', input) is None:
        logger.error('Regex failed for: ' + input)
        return False
    return True


def __verifyUser(username, password):
    users = __getUsers()
    if (username in users):
        return sha256_crypt.verify(password, users[username])
    else:
        return False


def __getUsers():
    users = { }

    # TODO Don't use hashmaps as we'll need to have username info like name
    if os.path.exists("../database.txt"):
        append_write = 'r' # append if already exists
    else:
        logger.error("Database file not found")
        return None
    with open("../database.txt", append_write) as f:
        for line in f:
            (key, val) = line.split()
            users[key] = val
    return users


def __verifyExistingUser(username):
    users = __getUsers()
    return username not in users


def __registerUser(username, password):
    hashedPassword = sha256_crypt.encrypt(password)

    # TODO Point to database instead of a text file
    # TODO Also store name
    if os.path.exists("../database.txt"):
        append_write = 'a' # append if already exists
    else:
        append_write = 'w' # make a new file if not
    with open("../database.txt", append_write) as file:
        file.write(username + " " + hashedPassword + "\n")
