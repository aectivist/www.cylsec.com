from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange
from app.instance_manager import get_available_instances

class ChallengeForm(FlaskForm):
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    difficulty = SelectField('Difficulty', choices=[
        ('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard'), ('Insane', 'Insane')
    ], validators=[DataRequired()])
    points = IntegerField('Points', validators=[DataRequired(), NumberRange(min=1, max=9999)])
    flag = StringField('Flag', validators=[DataRequired(), Length(max=100)])
    is_active = BooleanField('Active (visible to users)', default=True)

    # Modular fields
    type = SelectField('Challenge Type', choices=[
        ('web', 'Web'), ('pwn', 'Pwn'), ('forensics', 'Forensics'),
        ('rev', 'Reverse Engineering'), ('crypto', 'Crypto'), ('osint', 'OSINT')
    ], validators=[DataRequired()])
    file_url = StringField('File URL (download link)', validators=[Length(max=200)])
    challenge_url = StringField('Challenge URL (web or netcat)', validators=[Length(max=200)])
    
    # Instance selection
    instance_name = SelectField('CTF Instance (optional)', choices=[], validators=[])

    submit = SubmitField('Save Challenge')
    
    def __init__(self, *args, **kwargs):
        super(ChallengeForm, self).__init__(*args, **kwargs)
        # Populate instance choices based on type
        self.update_instance_choices()
    
    def update_instance_choices(self):
        """Update instance dropdown based on selected challenge type."""
        # Add empty option
        self.instance_name.choices = [('', '-- No Instance --')]
        
        # Get challenge type from form data
        challenge_type = self.type.data or 'web'
        
        # Get available instances for this type
        instances = get_available_instances(challenge_type)
        
        # Add instances to choices
        for instance in instances:
            self.instance_name.choices.append((instance, instance))


class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Description')
    submit = SubmitField('Save Category')

class SystemSettingsForm(FlaskForm):
    system_log_message = TextAreaField('System Log Message', validators=[Length(max=1000)])
    submit = SubmitField('Update System Log')