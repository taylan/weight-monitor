from subprocess import call
from os import path, getcwd
from sys import platform
from datetime import datetime
from orm import dbsession, Measurement, User
from sqlalchemy import desc
from json import dumps
from utils.utils import execute_command, copy_file_to_s3, set_current_dir, _remove_files


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

set_current_dir(__file__)

exe_name = '_phantomjs-{0}{1}'.format(platform, '.exe' if platform == 'win32' else '')
exe_path = path.join(getcwd(), exe_name)
if platform != 'win32':
    call(['chmod', '+x', exe_path])

now = datetime.now()
dest_timestamp = now.strftime('%Y-%m-%d_%H-%M-%S_%f')
short_timestamp = now.strftime('%Y-%m-%d')

periods = {7: 'Last Week', 30: 'Last Month', 365: 'Last Year', 100000: 'All Time'}


def get_measurements(user_id, limit):
    ms = dbsession.query(Measurement).filter(Measurement.user_id == user_id).order_by(
        desc(Measurement.measurement_date)).limit(limit).all()
    ms = sorted(ms, key=lambda m: m.measurement_date)
    return ms


def get_chart_data(ms):
    return [[m.measurement_date.strftime('%y-%m-%d'), m.value] for m in ms]


def prepare_and_save_chart_content(chart_content_template, chart_fn, user_id, period):
    measurements = get_measurements(user_id, period)
    chart_data = get_chart_data(measurements)
    content = chart_content_template.replace('[CHART_DATA]', ', '.join(map(str, chart_data)))
    content = content.replace('[CHART_TITLE]', periods[period])

    with open(chart_fn, mode='w') as dest_chart:
        dest_chart.write(content)


def _get_chart_template():
    with open(path.join(getcwd(), 'chart_template.html')) as chart_template:
        return chart_template.read()


def save_chart_image(chart_fn, chart_img):
    execute_command('{0} {1} {2} {3}'.format(exe_path, 'pjs-scr-cap.js', chart_fn, chart_img))
    copy_file_to_s3(chart_img)


def prepare_chart_images(user_id):
    for p in periods.keys():
        chart_file = '{0}_{1}_{2}.html'.format(dest_timestamp, p, user_id)
        chart_img = '{0}_{1}_{2}.png'.format(dest_timestamp, p, user_id)
        chart_template = _get_chart_template()
        prepare_and_save_chart_content(chart_template, chart_file, user_id, p)
        save_chart_image(chart_file, chart_img)

        _remove_files(chart_file, chart_img)
        print('P: {0} U: {1} complete'.format(p, user_id))


def _get_notification_mail_template():
    with open(path.join(getcwd(), 'notification_mail_template.html')) as notif_tpl:
        return notif_tpl.read()


def get_graph_contents(user_id):
    grphs = []
    for p in sorted(periods.keys()):
        chart_img = '{0}_{1}_{2}.png'.format(dest_timestamp, p, user_id)
        grphs.append(report_graph_template.replace('[PERIOD]', periods[p]).replace('[IMAGE_NAME]', chart_img))
    return grphs


def create_and_save_full_report(full_report_fn, user_id):
    template = _get_notification_mail_template()
    graphs = get_graph_contents(user_id)
    mail_content = template.replace('[REPORT_DATE]', short_timestamp).replace('[GRAPHS]', '\n'.join(graphs)).replace(
        '[FULL_REPORT_NAME]', full_report_fn)
    with open(path.join(getcwd(), full_report_fn), mode='w') as mail_cont:
        mail_cont.write(mail_content)
    return mail_content


def create_and_save_mail_json(mail_json_fn, content):
    mail_data = dict()
    mail_data['Subject'] = {'Data': 'Weight Monitor Report for {0}'.format(short_timestamp), 'Charset': 'UTF-8'}
    mail_data['Body'] = {'Html': {'Data': content, 'Charset': 'UTF-8'}}

    with open(mail_json_fn, mode='w') as mail_content_json:
        mail_content_json.write(dumps(mail_data))


def create_and_save_notification_recipients_json(notif_recip_json_fn, recipient):
    notif_recip_content = dumps({"ToAddresses": [recipient], "CcAddresses": [], "BccAddresses": []})
    with open(notif_recip_json_fn, mode='w') as notif_recip_json:
        notif_recip_json.write(notif_recip_content)


users = dbsession.query(User).all()
for u in users:
    prepare_chart_images(u.id)

    full_report_file_name = '{0}_{1}_mail.html'.format(dest_timestamp, u.id)
    mail_content = create_and_save_full_report(full_report_file_name, u.id)
    copy_file_to_s3(full_report_file_name)

    mail_json_file_name = path.join(getcwd(), '{0}_{1}_mail.json'.format(dest_timestamp, u.id))
    create_and_save_mail_json(mail_json_file_name, mail_content)

    notif_recipients_file_name = path.join(getcwd(),
                                           'notification-mail-recipients_{0}_{1}.json'.format(dest_timestamp, u.id))
    create_and_save_notification_recipients_json(notif_recipients_file_name, u.email)

    execute_command('aws ses send-email --from monitorweight@gmail.com --destination {0} --message {1}'
    .format('file://' + notif_recipients_file_name,
            'file://' + mail_json_file_name))

    _remove_files(full_report_file_name, mail_json_file_name, notif_recipients_file_name)
