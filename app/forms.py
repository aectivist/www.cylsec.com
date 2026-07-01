from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
import re

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = EmailField('Email', validators=[DataRequired(), Email()])

    def validate_password_strength(form, field):
        p = field.data or ''
        if len(p) < 12 or not re.search(r'[A-Z]', p) or not re.search(r'[a-z]', p) or not re.search(r'[0-9]', p) or not re.search(r'[^A-Za-z0-9]', p):
            raise ValidationError('Password must be at least 12 characters long and include uppercase, lowercase, a number, and a symbol.')

    password = PasswordField('Password', validators=[DataRequired(), validate_password_strength])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')

class UsernameChangeForm(FlaskForm):
    new_username = StringField('New Username', validators=[DataRequired(), Length(min=3, max=80)])
    submit = SubmitField('Update Username')