from datetime import datetime
from os import path, environ
from requests import get, post


def _get_weightbot_data():
    print('Getting Weightbot data (from weightbot_data.csv)')
    with open(path.join(path.dirname(path.realpath(__file__)), '..', 'weight-data/weightbot_data.csv')) as wb_file:
        wb_data = wb_file.read().splitlines()
        return [{'total': float(x.split(',')[1].strip()), 'date': datetime.strptime(x.split(',')[0], '%Y-%m-%d')} for x
                in wb_data]


def _get_mfp_data():
    print('Getting MyFitnessPal data (from www.myfitnesspal.com)')
    mfp_login_url = 'https://www.myfitnesspal.com/account/login'
    login_req = post(mfp_login_url, {'username': 'taylanaydinli', 'password': environ['MFPPASS']}, verify=False)
    session_id = login_req.cookies['_session_id']

    mfp_data_url = 'http://www.myfitnesspal.com/reports/results/progress/1/365.json?report_name=Weight'
    resp = get(mfp_data_url, cookies=dict(_session_id=session_id)).json()

    weight_data = [x for x in resp['data'] if x['total'] > 0]

    for w in weight_data:
        w['date'] = '2014/{0}'.format(w['date']) if w['date'].startswith('1/') else '2013/{0}'.format(w['date'])

    return [{'total': x['total'], 'date': datetime.strptime(x['date'].replace('/', '-'), '%Y-%m-%d')} for x in
            weight_data]


def get_weight_data():
    return _get_weightbot_data() + _get_mfp_data()
