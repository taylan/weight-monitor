from flask_wtf import Form
from wtforms import TextField, PasswordField
from wtforms.widgets import TextInput
from wtforms.validators import Email, DataRequired, EqualTo


class EmailField(TextField):
    widget = TextInput(input_type='email')


class LoginForm(Form):
    email = EmailField('email', validators=[Email(), DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])


class RegisterForm(Form):
    email = EmailField('email', validators=[Email(), DataRequired()])
    name = TextField('name', validators=[DataRequired()])
    password = PasswordField('password', validators=[
        DataRequired(),
        EqualTo('password_confirm', message='Passwords must match')
    ])
    password_confirm = PasswordField('password_confirm', validators=[DataRequired()])