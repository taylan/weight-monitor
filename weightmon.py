from orm import dbsession, Measurement
from config import is_debug
from flask import Flask, render_template, request, send_from_directory, jsonify

app = Flask(__name__)


if __name__ == '__main__':
    app.run(debug=is_debug(), use_reloader=False)