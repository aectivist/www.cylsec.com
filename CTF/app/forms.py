from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
import re

from app.disposable_emails import is_disposable_email

USERNAME_RE = re.compile(r'^[a-zA-Z0-9_]+$')


def validate_username_value(username):
    """Shared username validation used by both the registration form and
    the raw update_username endpoint (which doesn't go through WTForms)."""
    if not username or not (3 <= len(username) <= 20):
        return 'Username must be between 3 and 20 characters.'
    if not USERNAME_RE.match(username):
        return 'Username may only contain letters, numbers, and underscores.'
    return None


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, field):
        if not USERNAME_RE.match(field.data):
            raise ValidationError('Username may only contain letters, numbers, and underscores.')

    def validate_email(self, field):
        if is_disposable_email(field.data):
            raise ValidationError('Disposable/throwaway email addresses are not allowed. Please use a permanent email address.')


class UsernameChangeForm(FlaskForm):
    new_username = StringField('New Username', validators=[DataRequired(), Length(min=3, max=20)])
    submit = SubmitField('Change Username')


class ForgotPasswordForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')
