import logging
from datetime import datetime

import bcrypt
from cryptography.fernet import Fernet
from dotenv import load_dotenv

from app import db, app
from flask_login import UserMixin
import pyotp


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    # User authentication information.
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    pin_key = db.Column(db.String(32), nullable=False, default=pyotp.random_base32())

    # User information
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False, default='user')
    registered_on = db.Column(db.DateTime, nullable=False)
    current_login = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    # key information
    key = db.Column(db.BLOB, nullable=False)

    # Define the relationship to Draw
    draws = db.relationship('Draw')

    def __init__(self, email, firstname, lastname, phone, password, role, registered_on):
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.phone = phone
        # hash the password before storing
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.role = role
        self.registered_on = registered_on
        self.current_login = None
        self.last_login = None
        self.key = Fernet.generate_key()

    # get the uri from email and pin key
    def get_2fa_uri(self):
        return str(pyotp.totp.TOTP(self.pin_key).provisioning_uri(
            name=self.email,
            issuer_name='LotteryWebApp'
        ))

    # verify the hashed passwords
    def verify_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password)

    # verify the time-based pin keys
    def verify_pin(self, pin):
        return pyotp.TOTP(self.pin_key).verify(pin)




class Draw(db.Model):
    __tablename__ = 'draws'

    id = db.Column(db.Integer, primary_key=True)

    # ID of user who submitted draw
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)

    # 6 draw numbers submitted
    numbers = db.Column(db.String(100), nullable=False)

    # Draw has already been played (can only play draw once)
    been_played = db.Column(db.BOOLEAN, nullable=False, default=False)

    # Draw matches with master draw created by admin (True = draw is a winner)
    matches_master = db.Column(db.BOOLEAN, nullable=False, default=False)

    # True = draw is master draw created by admin. User draws are matched to master draw
    master_draw = db.Column(db.BOOLEAN, nullable=False)

    # Lottery round that draw is used
    lottery_round = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, user_id, numbers, master_draw, lottery_round):
        self.user_id = user_id
        self.numbers = numbers
        self.been_played = False
        self.matches_master = False
        self.master_draw = master_draw
        self.lottery_round = lottery_round


def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()

        registered_on = datetime.now()
        email = 'admin@email.com'

        admin = User(email=email,
                     password='Admin1!',
                     firstname='Alice',
                     lastname='Jones',
                     phone='0191-123-4567',
                     role='admin',
                     registered_on=registered_on)

        logging.warning('User [%s, %s] registered on %s',
                        email,
                        'localhost',
                        registered_on)

        db.session.add(admin)
        db.session.commit()


# load the dotenv reader
load_dotenv()


# encrypt the numbers
def encrypt(data, key):
    return Fernet(key).encrypt(bytes(data, 'utf-8'))


# decrypt the numbers
def decrypt(data, key):
    return Fernet(key).decrypt(data).decode('utf-8')