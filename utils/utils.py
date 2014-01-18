from subprocess import Popen
from sys import platform


def execute_command(params):
    print('executing command', params)
    params = params.split(' ') if isinstance(params, str) else params
    proc = Popen(params, shell=(platform == 'win32'))
    proc.wait()


def copy_file_to_s3(file_name):
    execute_command('aws s3 --storage-class=REDUCED_REDUNDANCY --acl=public-read cp {0} s3://ta-weightmon-chart-images/'.format(file_name))
