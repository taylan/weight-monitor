from forms import LoginForm
from orm import dbsession, Measurement, User
from config import is_debug
from flask import Flask, render_template, request, jsonify, redirect, g, url_for, flash
from flask.ext.login import LoginManager, current_user, login_user, logout_user, login_required
from datetime import datetime
from werkzeug.exceptions import HTTPException
from utils.measurement_data import MeasurementData
from os import environ
from passlib.hash import bcrypt


period_lengths = {'last-week': 7, 'last-month': 30, 'last-year': 365, 'all-time': 100000}
period_titles = {7: 'Last Week', 30: 'Last Month', 365: 'Last Year', 100000: 'All Time'}

app = Flask(__name__)
app.jinja_env.globals['now'] = datetime.now()
app.jinja_env.globals['period_lengths'] = period_lengths
app.jinja_env.globals['period_titles'] = period_titles
app.secret_key = environ['APPSECRET']

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'


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
    return (u if bcrypt.verify(password, u.password_hash) else None) if u else None


@login_manager.user_loader
def load_user(user_id):
    return dbsession.query(User).filter(User.id == int(user_id)).first() or None


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = _verify_user(form.email, form.password)
        if user:
            login_user(user)
            return redirect(request.args.get("next") or url_for("index"))
        else:
            flash('Incorrect email or password.', category='danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash('Error in the {0} field - {1}'.format(getattr(form, field).label.text, error), 'danger')

    return render_template('login.html', form=form)


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
    ms = dbsession.query(Measurement).order_by(Measurement.measurement_date.desc()).limit(p).all()
    _calculate_diffs(ms)
    md = MeasurementData(period_titles[p], ms)

    return render_template('index.html', measurement_data=md)


if __name__ == '__main__':
    app.run(debug=is_debug(), use_reloader=False)
