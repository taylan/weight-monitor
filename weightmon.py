from datetime import datetime, timedelta
import json
from fitbit.exceptions import HTTPUnauthorized
from os import environ

from passlib.hash import bcrypt
from sqlalchemy.sql import exists
from sqlalchemy import and_
from flask_compress import Compress
from flask_babel import Babel, gettext
from flask_assets import Environment, Bundle
from markupsafe import Markup
from werkzeug.exceptions import HTTPException
import fitbit

from forms import LoginForm, RegisterForm
from orm import dbsession, Measurement, User
from config import is_debug, LANGUAGES, PERIODS
from flask import (Flask, render_template, request, jsonify, redirect, g,
                   url_for, flash, session)
from flask_login import (LoginManager, current_user, login_user,
                             logout_user, login_required)
from flask_oauthlib.client import OAuth
from utils.formutils import write_errors_to_flash
from utils.templatehelpers import url_for_lang, lang_name, get_translation
from utils.data import get_measurement_data
from utils.impersonation import ImpersonationContext


def get_send_file_max_age(self, name):
    return 31449600


Flask.get_send_file_max_age = get_send_file_max_age

app = Flask(__name__)
app.config['COMPRESS_DEBUG'] = is_debug()
app.config['ASSETS_DEBUG'] = is_debug()
app.jinja_env.globals['now'] = datetime.utcnow()
app.jinja_env.globals['periods'] = PERIODS
app.jinja_env.globals['url_for_lang'] = url_for_lang
app.jinja_env.globals['lang_name'] = lang_name
app.jinja_env.globals['get_translation'] = get_translation
app.jinja_env.globals['LANGUAGES'] = LANGUAGES
app.jinja_env.globals['ADMIN_USER'] = environ['ADMIN_USER']
app.jinja_env.globals['impersonation_context'] = ImpersonationContext()
app.secret_key = environ['APPSECRET']

login_manager = LoginManager(app)
login_manager.login_view = 'login'

oauth = OAuth()
fitbit_oauth = oauth.remote_app(
    'fitbit',
    base_url='https://api.fitbit.com/',
    request_token_url='http://api.fitbit.com/oauth/request_token',
    access_token_url='http://api.fitbit.com/oauth/access_token',
    authorize_url='http://www.fitbit.com/oauth/authorize',
    consumer_key=environ['FBCONSUMERKEY'],
    consumer_secret=environ['FBCONSUMERSECRET']
)
oauth.init_app(app)

Compress(app)
babel = Babel(app)

assets = Environment(app)
assets.register('all_js',
                Bundle('js/jquery-2.0.3.min.js', 'js/bootstrap.min.js',
                       'js/picker.js', 'js/picker.date.js',
                       'js/bootstrap-editable.min.js', 'js/spin.min.js',
                       'js/ladda.min.js', 'js/weight-monitor.js',
                       filters='rjsmin', output='gen/weightmon-packed.js'))
assets.register('all_css',
                Bundle('css/bootstrap.min.css', 'css/pickadate.css',
                       'css/pickadate.date.css', 'css/bootstrap-editable.css',
                       'css/ladda-themeless.min.css', 'css/animate.min.css',
                       'css/weight-monitor.css',
                       output='gen/weightmon-packed.css'))


@fitbit_oauth.tokengetter
def get_fitbit_token(token=None):
    oauth_data = json.loads(g.user.fitbit_oauth_data)
    return (
        oauth_data['oauth_token'],
        oauth_data['oauth_token_secret']
    )


@babel.localeselector
def get_locale():
    return g.lang


def _user_is_authenticated():
    return g.user and g.user.is_authenticated()


def _current_user_id():
    imp_context = app.jinja_env.globals['impersonation_context']
    return imp_context.user_id if imp_context.is_impersonating else g.user.id


@app.before_request
def before_request():
    g.user = current_user
    g.lang = request.args.get('hl', request.cookies.get('lang', '')) \
                 or request.accept_languages.best_match(
        LANGUAGES) or LANGUAGES[0]
    login_manager.login_message = Markup(
        gettext('login_message').format('/register'))


@app.after_request
def after_request(resp):
    resp.set_cookie('lang', value=g.lang,
                    expires=int((datetime.now() +
                                 timedelta(days=365)).timestamp()),
                    httponly=True)
    return resp


def _verify_user(email, password):
    u = dbsession.query(User).filter(User.email == email).first() or None
    return (u if bcrypt.verify(password, u.password_hash) else None) \
        if u else None


@login_manager.user_loader
def load_user(user_id):
    return dbsession.query(User).filter(User.id == int(user_id)).first() or None


@app.route('/fitbit_connect')
def fitbit_connect():
    if session.get('fitbit_token', None):
        return redirect(url_for('index'))

    return fitbit_oauth.authorize(callback=url_for('fitbit_authorized',
                                                   _external=True))


@app.route('/fitbit_oauth_callback')
@fitbit_oauth.authorized_handler
def fitbit_authorized(resp):
    next_url = request.args.get('next') or url_for('index')
    if resp is None:
        flash('Fitbit connection request denied.', category='danger')
        return redirect(next_url)

    user = dbsession.query(User).filter(User.id == g.user.id).first()
    user.fitbit_oauth_data = json.dumps(resp)
    dbsession.commit()

    return redirect(next_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if _user_is_authenticated():
        return redirect('/')

    form = LoginForm()
    if form.validate_on_submit():
        user = _verify_user(form.email.data, form.password.data)
        if user:
            login_user(user, remember=True)
            return redirect(request.args.get("next") or url_for("index"))
        else:
            flash(gettext('Incorrect email or password.'), category='danger')
    else:
        write_errors_to_flash(form)

    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if _user_is_authenticated():
        return redirect('/')

    form = RegisterForm()
    if form.validate_on_submit():
        if dbsession.query(
                exists().where(User.email == form.email.data)).scalar():
            warning_markup = Markup(
                'User with email %(email) already exists. '
                'Click <a href="%(login_link)">here</a> to login.',
                email=form.email.data, login_link=url_for('login'))
            flash(warning_markup, 'warning')
            return render_template('register.html', form=form)
        user = User(name=form.name.data,
                    email=form.email.data,
                    password_hash=bcrypt.encrypt(form.password.data))
        dbsession.add(user)
        dbsession.commit()
        login_user(user, remember=True)
        return redirect('/')
    else:
        write_errors_to_flash(form)

    return render_template('register.html', form=form)


@app.route('/impersonate', methods=['POST'])
def impersonate():
    act = request.form.get('imp_action', '').lower()
    email = request.form.get('imp_email', '')
    if act not in ['stop', 'go'] or (act == 'go' and not email):
        return redirect('/')

    user = None if act == 'stop' else \
        dbsession.query(User).filter(User.email == email).first()
    app.jinja_env.globals['impersonation_context'] = \
        ImpersonationContext(user.id,
                             user.email) if user else ImpersonationContext()
    return redirect('/')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


def _save_to_fitbit(date, weight):
    fbd = current_user.fitbit_oauth_data
    if not fbd:
        return

    fbd_obj = json.loads(fbd)
    try:
        fb = fitbit.Fitbit(environ['FBCONSUMERKEY'],
                           environ['FBCONSUMERSECRET'],
                           resource_owner_key=fbd_obj['oauth_token'],
                           resource_owner_secret=fbd_obj['oauth_token_secret'],
                           system='en_UK')

        fb.body(date=date, data={'weight': weight})
    except HTTPUnauthorized:
        flash('Fitbit oauth token expired.', category='danger')
    except Exception as ex:
        flash('Unexpected error while saving weight data to Fitbit.'
              'Error: {0}'.format(ex), category='danger')


@app.route('/save', methods=['POST'])
def save_measurement():
    try:
        date_val = datetime.strptime(
            request.form.get('d', request.form.get('pk', '')), '%Y-%m-%d')
        value = request.form.get('value', '')
        weight_val = float(request.form.get('v', value).replace(',', '.'))
    except (ValueError, HTTPException):
        if request.headers.get('X-Requested-With', ''):
            return jsonify({'r': False})
        else:
            return redirect(request.referrer)

    m = dbsession.query(Measurement).filter(
        and_(Measurement.measurement_date ==
             date_val, Measurement.user_id == current_user.id)).first() \
        or Measurement(measurement_date=date_val, user_id=current_user.id)
    m.value = weight_val
    dbsession.add(m)
    dbsession.commit()
    if request.headers.get('X-Requested-With', ''):
        return jsonify({'r': True})
    else:
        return redirect(request.referrer)


@app.route('/', methods=['GET'])
@app.route('/p/<period>', methods=['GET'])
@login_required
def index(period='last-week'):
    md = get_measurement_data(period, gettext(period), _current_user_id())
    return render_template('index.html', measurement_data=md)


if __name__ == '__main__':
    app.run(debug=is_debug(), use_reloader=False)
