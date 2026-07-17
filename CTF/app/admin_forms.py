from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, IntegerField, BooleanField,
                     SelectField, SubmitField)
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class ChallengeForm(FlaskForm):
    title        = StringField('Title',       validators=[DataRequired(), Length(max=100)])
    description  = TextAreaField('Description', validators=[DataRequired()])
    difficulty   = SelectField('Difficulty',  choices=[
        ('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard'), ('Insane', 'Insane')
    ])
    points       = IntegerField('Points',     validators=[DataRequired(), NumberRange(min=1)], default=100)
    flag         = StringField('Flag',        validators=[Optional(), Length(max=100)])
    category_id  = SelectField('Category',   coerce=int)
    is_active    = BooleanField('Active',     default=True)
    type         = SelectField('Type',        choices=[
        ('web', 'Web'), ('pwn', 'Pwn'), ('rev', 'Reverse Engineering'),
        ('crypto', 'Crypto'), ('forensics', 'Forensics'),
        ('misc', 'Misc'), ('docker', 'Docker'),
    ])
    file_url       = StringField('File URL',       validators=[Optional(), Length(max=200)])
    challenge_url  = StringField('Challenge URL',  validators=[Optional(), Length(max=200)])
    instance_name  = SelectField('Docker Instance', choices=[('', '— none —')])
    submit         = SubmitField('Save')

    def update_instance_choices(self):
        from app.instance_manager import get_available_instances
        instances = get_available_instances(None)
        self.instance_name.choices = [('', '— none —')] + [(i, i) for i in instances]


class CategoryForm(FlaskForm):
    name        = StringField('Name',        validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Description', validators=[Optional()])
    icon        = StringField('Icon (emoji or text)', validators=[Optional(), Length(max=100)])
    submit      = SubmitField('Save')


class SystemSettingsForm(FlaskForm):
    system_log_message = TextAreaField('System Message', validators=[Optional(), Length(max=500)])
    submit             = SubmitField('Save Settings')
