from os import path, remove
from sys import exit
from datetime import datetime
from orm import dbsession, Measurement
from json import dumps
from utils.utils import execute_command

now = datetime.now().date()
last_measurement = dbsession.query(Measurement.measurement_date).order_by(Measurement.measurement_date.desc()).first()[0].date()
short_timestamp = now.strftime('%Y-%m-%d')
dest_timestamp = now.strftime('%Y-%m-%d_%H-%M-%S_%f')

days_since_last = (now - last_measurement).days

if days_since_last < 2:
    exit(0)

with open(path.join(path.dirname(path.realpath(__file__)), 'nag_mail_template.html')) as nag_tpl:
    template = nag_tpl.read()

mail_content = template.replace('[LAST_ENTRY_DATE]', last_measurement.strftime('%Y-%m-%d')).replace('[DAY_COUNT]', str(days_since_last))

mail_data = dict()
mail_data['Subject'] = {'Data': 'Weight Monitor Warning', 'Charset': 'UTF-8'}
mail_data['Body'] = {'Html': {'Data': mail_content, 'Charset': 'UTF-8'}}

mail_json_file_name = path.join(path.dirname(path.realpath(__file__)), '{0}_nag_mail.json'.format(dest_timestamp))
with open(mail_json_file_name, mode='w') as mail_content_json:
    mail_content_json.write(dumps(mail_data))

execute_command('aws ses send-email --from monitorweight@gmail.com --destination {0} --message {1}'
    .format('file://' + path.join(path.dirname(path.realpath(__file__)), 'notification-mail-recipients.json'),
            'file://' + mail_json_file_name))

remove(mail_json_file_name)
