from flask_wtf import Form
from wtforms import TextField, PasswordField
from wtforms.widgets import TextInput
from wtforms.validators import Email, DataRequired


class EmailField(TextField):
    widget = TextInput(input_type='email')


class LoginForm(Form):
    email = EmailField('email', validators=[Email(), DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
