from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import Email, ValidationError, DataRequired, Length, EqualTo
import re


# check for not allowed characters
def character_check(form, field):
    excluded_characters = "*?!'^+%&/()=}][{$#@<>"

    for character in field.data:
        if character in excluded_characters:
            raise ValidationError(f"Character {character} is not allowed.")

# check for phone number pattern
def phone_number_check(form, field):
    p = re.compile("^[0-9]{4}-[0-9]{3}-[0-9]{4}$")

    if not p.match(field.data):
        raise ValidationError("The phone number pattern is incorrect should be 'XXXX-XXX-XXXX'")


# check for password characters
def password_check(form, field):
    p = re.compile(r"(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W)")

    if not p.match(field.data):
        raise ValidationError("Password must contain at least 1 digit, 1 lowercase, 1 uppercase character and 1 special character")


# check of DOB pattern
def dob_check(form, field):
    p = re.compile("^[0-3][0-9]/[0-1][0-2]/[0-2][0-9][0-9][0-9]")

    if not p.match(field.data):
        raise ValidationError("The DOB pattern is incorrect should be 'XX/XX/XXXX'")


class RegisterForm(FlaskForm):
    email = StringField(validators=[Email(), DataRequired()])
    firstname = StringField(validators=[character_check, DataRequired()])
    lastname = StringField(validators=[character_check, DataRequired()])
    dob = StringField(validators=[dob_check, DataRequired()])
    phone = StringField(validators=[phone_number_check, DataRequired()])
    password = PasswordField(validators=[Length(min=6, max=12), password_check, DataRequired()])
    confirm_password = PasswordField(validators=[EqualTo('password', 'Both password fields must be equal!'), DataRequired()])
    submit = SubmitField()


class LoginForm(FlaskForm):
    email = StringField(validators=[Email(), DataRequired()])
    password = PasswordField(validators=[DataRequired()])
    pin = StringField(validators=[DataRequired(), Length(min=6, max=6)])
    recaptcha = RecaptchaField()
    submit = SubmitField()


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(validators=[Length(min=6, max=12), password_check, DataRequired()])
    new_password = PasswordField(validators=[Length(min=6, max=12), password_check, DataRequired()])
    confirm_new_password = PasswordField(validators=[EqualTo('new_password', 'Both password fields must be equal!'), DataRequired()])
    submit = SubmitField()
