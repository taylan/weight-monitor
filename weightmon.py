from orm import dbsession, Measurement
from config import is_debug
from flask import Flask, render_template, request, send_from_directory, jsonify
from datetime import datetime

app = Flask(__name__)
app.jinja_env.globals['now'] = datetime.now()

@app.route('/', methods=['GET'])
def index():
    last_7_days = dbsession.query(Measurement).order_by(Measurement.measurement_date.desc()).limit(7)
    return render_template('index.html', last_7_days=last_7_days)


if __name__ == '__main__':
    app.run(debug=is_debug(), use_reloader=False)
