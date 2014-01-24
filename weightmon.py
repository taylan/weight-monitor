from forms import LoginForm, RegisterForm
from markupsafe import Markup
from orm import dbsession, Measurement, User
from config import is_debug
from flask import Flask, render_template, request, jsonify, redirect, g, url_for, flash
from flask.ext.login import LoginManager, current_user, login_user, logout_user, login_required
from datetime import datetime
from werkzeug.exceptions import HTTPException
from utils.measurement_data import MeasurementData
from utils.formutils import write_errors_to_flash
from os import environ
from passlib.hash import bcrypt
from sqlalchemy.sql import exists


period_lengths = {'last-week': 7, 'last-month': 30, 'last-year': 365, 'all-time': 100000}
period_titles = {7: 'Last Week', 30: 'Last Month', 365: 'Last Year', 100000: 'All Time'}

app = Flask(__name__)
app.jinja_env.globals['now'] = datetime.now()
app.jinja_env.globals['period_lengths'] = period_lengths
app.jinja_env.globals['period_titles'] = period_titles
app.secret_key = environ['APPSECRET']

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_msg_markup = Markup('Please log in to access this page. Not a member? Register <a href="{0}">here</a>.'.format('/register'))
login_manager.login_message = login_msg_markup


def _calculate_diffs(measurements):
    for i, m in reversed(list(enumerate(measurements))):
        if i == len(measurements) - 1:
            m.diff = 0
        else:
            m.diff = m.value - measurements[i + 1].value


@app.before_request
def before_request():
    g.user = current_user


def _verify_user(email, password):
    u = dbsession.query(User).filter(User.email == email).first() or None
    print(u)
    return (u if bcrypt.verify(password, u.password_hash) else None) if u else None


@login_manager.user_loader
def load_user(user_id):
    return dbsession.query(User).filter(User.id == int(user_id)).first() or None


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = _verify_user(form.email.data, form.password.data)
        if user:
            login_user(user, remember=True)
            return redirect(request.args.get("next") or url_for("index"))
        else:
            flash('Incorrect email or password.', category='danger')
    else:
        write_errors_to_flash(form)

    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if dbsession.query(exists().where(User.email == form.email.data)).scalar():
            warning_markup = Markup('User with email {0} already exists. Click <a href="{1}">here</a> to login.'.format(form.email.data, url_for('login')))
            flash(warning_markup, 'warning')
            return render_template('register.html', form=form)
        user = User(name=form.name.data, email=form.email.data, password_hash = bcrypt.encrypt(form.password.data))
        dbsession.add(user)
        dbsession.commit()
        login_user(user, remember=True)
        redirect('/')
    else:
        write_errors_to_flash(form)

    return render_template('register.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/save', methods=['POST'])
def save_measurement():
    try:
        date_val = datetime.strptime(request.form.get('d', request.form.get('pk', '')), '%Y-%m-%d')
        weight_val = float(request.form.get('v', request.form.get('value', '')))
    except (ValueError, HTTPException):
        return jsonify(r='e') if request.headers.get('X-Requested-With', '') else redirect(request.referrer)

    m = dbsession.query(Measurement).filter(Measurement.measurement_date == date_val).first() or Measurement(
        measurement_date=date_val)
    m.value = weight_val
    dbsession.add(m)
    dbsession.commit()
    return jsonify(r='e') if request.headers.get('X-Requested-With', '') else redirect(request.referrer)


@app.route('/', methods=['GET'])
@app.route('/p/<period>', methods=['GET'])
@login_required
def index(period='last-week'):
    p = period_lengths.get(period, 7)
    ms = dbsession.query(Measurement).filter(Measurement.user_id == g.user.id).order_by(Measurement.measurement_date.desc()).limit(p).all()
    print(ms)
    _calculate_diffs(ms)
    md = MeasurementData(period_titles[p], ms)

    return render_template('index.html', measurement_data=md)


if __name__ == '__main__':
    app.run(debug=is_debug(), use_reloader=False)
