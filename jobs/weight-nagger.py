from os import path, getcwd, environ
from datetime import datetime
from orm import dbsession, Measurement, User
from json import dumps
from utils.utils import execute_command, set_current_dir, _remove_files
from random import choice

set_current_dir(__file__)
now = datetime.now().date()
short_timestamp = now.strftime('%Y-%m-%d')
dest_timestamp = now.strftime('%Y-%m-%d_%H-%M-%S_%f')
disappoint_images = ['RuYH0', 'WSmpayC', 'tPzTdA4', 'ldtpOON', 'sYquW0y', 'JKHTl', 'Opv98', 'S3VpN', 't5BwT',
                     'xcmP1', '1vxHz', 'D9dQr', 'sez4T', 'YDvsK', 'qkfZa', 'wm9Srgj', 'JR0JX8b', 'SEpCU',
                     'KWfNGxQ', 'bEdpq', 'IZD3z', 'zmPFF', 'm1Q72', '2JA8F', 'Zv3lZ', 'z0PaK']


def prepare_nag_mail_content(last_msmt):
    with open(path.join(getcwd(), 'nag_mail_template.html')) as nag_tpl:
        template = nag_tpl.read()

    return template.replace('[LAST_ENTRY_DATE]', last_msmt.strftime('%Y-%m-%d')).replace('[DAY_COUNT]', str(
        days_since_last)).replace('[WEIGHT_MONITOR_URL]', environ['APPURL']) \
        .replace('[DISAPPOINT_IMAGE_SRC]', 'http://i.imgur.com/{0}.gif'.format(choice(disappoint_images)))


def create_and_save_nag_mail_json(mail_json_fn):
    mail_data = dict()
    mail_data['Subject'] = {'Data': 'Weight Monitor Warning', 'Charset': 'UTF-8'}
    mail_data['Body'] = {'Html': {'Data': prepare_nag_mail_content(last_measurement), 'Charset': 'UTF-8'}}

    with open(mail_json_fn, mode='w') as mail_content_json:
        mail_content_json.write(dumps(mail_data))


def create_and_save_notification_recipients_json(notif_recip_json_fn, recipient):
    notif_recip_content = dumps({"ToAddresses": [recipient], "CcAddresses": [], "BccAddresses": []})
    with open(notif_recip_json_fn, mode='w') as notif_recip_json:
        notif_recip_json.write(notif_recip_content)


users = dbsession.query(User).all()
for u in users:
    last_measurement = dbsession.query(Measurement.measurement_date).filter(Measurement.user_id == u.id).order_by(
        Measurement.measurement_date.desc()).first()
    if not last_measurement:
        print('No measurements for {0}'.format(u))
        continue

    last_measurement = last_measurement[0].date()
    days_since_last = (now - last_measurement).days

    if days_since_last < 2:
        continue

    mail_json_file_name = path.join(getcwd(), '{0}_{1}_nag_mail.json'.format(dest_timestamp, u.id))
    create_and_save_nag_mail_json(mail_json_file_name)

    not_recipients_filename = path.join(getcwd(), 'notification-mail-recipients_{0}_{1}.json'.format(dest_timestamp,
                                                                                                     u.id))
    create_and_save_notification_recipients_json(not_recipients_filename, u.email)

    execute_command('aws ses send-email --from monitorweight@gmail.com --destination {0} --message {1}'
    .format('file://' + not_recipients_filename,
            'file://' + mail_json_file_name))

    _remove_files(mail_json_file_name, not_recipients_filename)
