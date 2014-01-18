from subprocess import call
from os import path, remove
from sys import platform
from datetime import datetime
from orm import dbsession, Measurement
from sqlalchemy import desc
from json import dumps
from utils.utils import execute_command, copy_file_to_s3


report_graph_template = """<table class='row'
                                   style='border-spacing: 0; border-collapse: collapse; vertical-align: top; text-align: left; width: 100%; position: relative; display: block; padding: 0px;'>
                                <tr style='vertical-align: top; text-align: left; padding: 0;' align='left'>
                                    <td class='wrapper last'
                                        style='word-break: break-word; -webkit-hyphens: auto; -moz-hyphens: auto; hyphens: auto; border-collapse: collapse !important; vertical-align: top; text-align: left; position: relative; color: #222222; font-family: sans-serif; font-weight: normal; line-height: 19px; font-size: 14px; margin: 0; padding: 10px 0px 0px;'
                                        align='left' valign='top'>

                                        <table class='twelve columns'
                                               style='border-spacing: 0; border-collapse: collapse; vertical-align: top; text-align: left; width: 580px; margin: 0 auto; padding: 0;'>
                                            <tr style='vertical-align: top; text-align: left; padding: 0;' align='left'>
                                                <td style='word-break: break-word; -webkit-hyphens: auto; -moz-hyphens: auto; hyphens: auto; border-collapse: collapse !important; vertical-align: top; text-align: left; color: #222222; font-family: sans-serif; font-weight: normal; line-height: 19px; font-size: 14px; margin: 0; padding: 0px 0px 10px;'
                                                    align='left' valign='top'>

                                                    <h4 style='color: #222222; font-family: sans-serif; font-weight: normal; text-align: left; line-height: 1.3; word-break: normal; font-size: 28px; margin: 0; padding: 0;'
                                                        align='left'>[PERIOD]</h4>
                                                    <a href='https://s3.amazonaws.com/ta-weightmon-chart-images/[IMAGE_NAME]'>
                                                    <img width='580' height='300' src='https://s3.amazonaws.com/ta-weightmon-chart-images/[IMAGE_NAME]'
                                                         style='outline: none; text-decoration: none; -ms-interpolation-mode: bicubic; width: auto; max-width: 100%; float: left; clear: both; display: block;'
                                                         align='left'/></a></td>
                                                <td class='expander'
                                                    style='word-break: break-word; -webkit-hyphens: auto; -moz-hyphens: auto; hyphens: auto; border-collapse: collapse !important; vertical-align: top; text-align: left; visibility: hidden; width: 0px; color: #222222; font-family: sans-serif; font-weight: normal; line-height: 19px; font-size: 14px; margin: 0; padding: 0;'
                                                    align='left' valign='top'></td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>"""


exe_name = '_phantomjs-{0}{1}'.format(platform, '.exe' if platform == 'win32' else '')
exe_path = path.join(path.dirname(path.realpath(__file__)), exe_name)
if platform != 'win32':
    call(['chmod', '+x', exe_path])

now = datetime.now()
dest_timestamp = now.strftime('%Y-%m-%d_%H-%M-%S_%f')

periods = {7: 'Last Week', 30: 'Last Month', 365: 'Last Year', 100000: 'All Time'}


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

    execute_command('{0} {1} {2} {3}'.format(exe_path, 'pjs-scr-cap.js', chart_file_name, chart_img_name))
    copy_file_to_s3(chart_img_name)
    print('P: {0} complete'.format(p))
    remove(chart_file_name)
    remove(chart_img_name)

with open(path.join(path.dirname(path.realpath(__file__)), 'notification_mail_template.html')) as notif_tpl:
    template = notif_tpl.read()

graphs = []
for p in sorted(periods.keys()):
    chart_img_name = '{0}_{1}.png'.format(dest_timestamp, p)
    graphs.append(report_graph_template.replace('[PERIOD]', periods[p]).replace('[IMAGE_NAME]', chart_img_name))

short_timestamp = now.strftime('%Y-%m-%d')
full_report_file_name = '{0}_mail.html'.format(dest_timestamp)
mail_content = template.replace('[REPORT_DATE]', short_timestamp).replace('[GRAPHS]', '\n'.join(graphs)).replace('[FULL_REPORT_NAME]', full_report_file_name)
with open(path.join(path.dirname(path.realpath(__file__)), full_report_file_name), mode='w') as mail_cont:
    mail_cont.write(mail_content)
copy_file_to_s3(full_report_file_name)

mail_data = dict()
mail_data['Subject'] = {'Data': 'Weight Monitor Report for {0}'.format(short_timestamp), 'Charset': 'UTF-8'}
mail_data['Body'] = {'Html': {'Data': mail_content, 'Charset': 'UTF-8'}}

mail_json_file_name = path.join(path.dirname(path.realpath(__file__)), '{0}_mail.json'.format(dest_timestamp))
with open(mail_json_file_name, mode='w') as mail_content_json:
    mail_content_json.write(dumps(mail_data))

execute_command('aws ses send-email --from monitorweight@gmail.com --destination {0} --message {1}'
    .format('file://' + path.join(path.dirname(path.realpath(__file__)), 'notification-mail-recipients.json'),
            'file://' + mail_json_file_name))

remove(full_report_file_name)
remove(mail_json_file_name)
