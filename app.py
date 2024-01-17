# IMPORTS
import logging

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_qrcode import QRcode
from flask_login import LoginManager
import os
from dotenv import load_dotenv
from flask_talisman import Talisman

# configure the logger class in the lottery.log file
logger = logging.getLogger()
file_handler = logging.FileHandler('lottery.log', 'a')
file_handler.setLevel(logging.WARNING)
logger.addHandler(file_handler)
# load dotenv reader
load_dotenv()

# CONFIG
app = Flask(__name__)
# get the secret key from .env file
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# get the recaptcha keys from .env file
app.config['RECAPTCHA_PUBLIC_KEY'] = os.getenv('RECAPTCHA_PUBLIC_KEY')
app.config['RECAPTCHA_PRIVATE_KEY'] = os.getenv('RECAPTCHA_PRIVATE_KEY')


# initialise database
db = SQLAlchemy(app)
# set the content security policy for the app
csp = {
    'default-src': [
        '\'self\'',
        'https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.2/css/bulma.min.css'
    ],
    'frame-src': [
        '\'self\'',
        'https://www.google.com',
        'https://www.google.com/recaptcha',
        'https://recaptcha.google.com/recaptcha/'
    ],
    'script-src': [
        '\'self\'',
        '\'unsafe-inline\'',
        'https://www.google.com/recaptcha/',
        'https://www.gstatic.com/recaptcha'
    ],
    'img-src': [
        'data:'
    ],
    'style-src-elem': [
        '\'self\'',
        '\'unsafe-inline\'',
        'https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.2/css/bulma.min.css',
        'https://www.google.com/recaptcha/',
        'https://www.gstatic.com/recaptcha'
    ],
    'script-src-elem': [
        '\'self\'',
        '\'unsafe-inline\'',
        'https://www.google.com/recaptcha/ https://www.gstatic.com/recaptcha',
        'https://www.google.com/recaptcha/',
        'https://www.gstatic.com/recaptcha',
        'https://www.gstatic.com/recaptcha/releases/cwQvQhsy4_nYdnSDY4u7O5_B/recaptcha__en_gb.js'
    ]
}
talisman = Talisman(app, content_security_policy=csp)
# configure the qrcode class
qrcode = QRcode(app)


# ERROR VIEWS
@app.errorhandler(400)
def bad_request(error):
    return render_template('errors/400.html'), 400


@app.errorhandler(403)
def bad_request(error):
    return render_template('errors/403.html'), 403


@app.errorhandler(404)
def bad_request(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def bad_request(error):
    return render_template('errors/500.html'), 500


@app.errorhandler(503)
def bad_request(error):
    return render_template('errors/503.html'), 503


# HOME PAGE VIEW
@app.route('/')
def index():
    return render_template('main/index.html')


# BLUEPRINTS
# import blueprints
from users.views import users_blueprint
from admin.views import admin_blueprint
from lottery.views import lottery_blueprint


#  register blueprints with app
app.register_blueprint(users_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(lottery_blueprint)

# set up the login manager class
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.init_app(app)

from models import User


# load the user by id
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


if __name__ == "__main__":
    # run app with the self-signed certificates
    app.run(ssl_context=('cert.pem', 'key.pem'))
