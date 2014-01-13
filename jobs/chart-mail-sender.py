from subprocess import Popen, call
from os import path, remove
from sys import platform
from datetime import datetime
from orm import dbsession, Measurement
from sqlalchemy import desc


exe_name = '_phantomjs-{0}{1}'.format(platform, '.exe' if platform == 'windows' else '')
exe_path = path.join(path.dirname(path.realpath(__file__)), exe_name)
call(['chmod', '+x', exe_path])

dest_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')


for p in [7, 30, 365, 3000]:
    with open(path.join(path.dirname(path.realpath(__file__)), 'chart_template.html')) as chart_template:
        chart_content = chart_template.read()
    chart_file_name = '{0}_{1}.html'.format(dest_timestamp, p)
    chart_img_name = '{0}_{1}.png'.format(dest_timestamp, p)

    measurements = dbsession.query(Measurement).order_by(desc(Measurement.measurement_date)).limit(p).all()
    measurements = sorted(measurements, key=lambda m: m.measurement_date)
    dt = [[m.measurement_date.strftime('%y-%m-%d'), m.value] for m in measurements]
    chart_content = chart_content.replace('[CHART_DATA]', ', '.join(map(str, dt)))
    chart_content = chart_content.replace('[CHART_TITLE]', 'Last {0} days'.format(p))

    with open(chart_file_name, mode='w') as dest_chart:
        dest_chart.write(chart_content)

    params = '{0} {1} {2} {3}'.format(exe_path, 'phantomjs-screen-capture.js', chart_file_name, chart_img_name).split(' ')
    print(params)
    pjs_proc = Popen(params)
    pjs_proc.wait()
    print('P: {0} complete'.format(p))
    remove(chart_file_name)

