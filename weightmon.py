from orm import dbsession, Measurement
from config import is_debug
from flask import Flask, render_template, request, send_from_directory, jsonify, redirect
from datetime import datetime

app = Flask(__name__)
app.jinja_env.globals['now'] = datetime.now()


@app.route('/save', methods=['POST'])
def save_measurement():
    print(request.headers)
    try:
        date_val = datetime.strptime(request.form['d'], '%Y-%m-%d')
        weight_val = float(request.form['v'])
    except ValueError:
        return jsonify(r='e') if request.headers.get('X-Requested-With', '') else redirect(request.referrer)

    m = dbsession.query(Measurement).filter(Measurement.measurement_date==date_val).first() or Measurement(measurement_date=date_val)
    m.value = weight_val
    dbsession.add(m)
    dbsession.commit()
    return jsonify(r='e') if request.headers.get('X-Requested-With', '') else redirect(request.referrer)


@app.route('/', methods=['GET'])
def index():
    last_7_days = dbsession.query(Measurement).order_by(Measurement.measurement_date.desc()).limit(7)
    return render_template('index.html', last_7_days=last_7_days)


if __name__ == '__main__':
    app.run(debug=is_debug(), use_reloader=False)
