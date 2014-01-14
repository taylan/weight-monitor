from subprocess import Popen, call
from os import path, remove
from sys import platform
from datetime import datetime
from orm import dbsession, Measurement
from sqlalchemy import desc


exe_name = '_phantomjs-{0}{1}'.format(platform, '.exe' if platform == 'win32' else '')
exe_path = path.join(path.dirname(path.realpath(__file__)), exe_name)
if platform != 'win32':
    call(['chmod', '+x', exe_path])

dest_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')

periods = {7: 'Last Week', 30: 'Last Month', 365: 'Last Year', 100000: 'All Time'}


def _execute_command(params):
    params = params.split(' ') if isinstance(params, str) else params
    proc = Popen(params, shell=True)
    proc.wait()


def _copy_file_to_s3(file_name):
    _execute_command('aws s3 --storage-class=REDUCED_REDUNDANCY --acl=public-read cp {0} s3://ta-weightmon-chart-images/'.format(file_name))


for p in periods.keys():
    with open(path.join(path.dirname(path.realpath(__file__)), 'chart_template.html')) as chart_template:
        chart_content = chart_template.read()
    chart_file_name = '{0}_{1}.html'.format(dest_timestamp, p)
    chart_img_name = '{0}_{1}.png'.format(dest_timestamp, p)

    measurements = dbsession.query(Measurement).order_by(desc(Measurement.measurement_date)).limit(p).all()
    measurements = sorted(measurements, key=lambda m: m.measurement_date)
    dt = [[m.measurement_date.strftime('%y-%m-%d'), m.value] for m in measurements]
    chart_content = chart_content.replace('[CHART_DATA]', ', '.join(map(str, dt)))
    chart_content = chart_content.replace('[CHART_TITLE]', periods[p])

    with open(chart_file_name, mode='w') as dest_chart:
        dest_chart.write(chart_content)

    _execute_command('{0} {1} {2} {3}'.format(exe_path, 'pjs-scr-cap.js', chart_file_name, chart_img_name))
    _copy_file_to_s3(chart_img_name)
    print('P: {0} complete'.format(p))
    remove(chart_file_name)
    remove(chart_img_name)

