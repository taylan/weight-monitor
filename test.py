from subprocess import Popen, call
from os import path
from sys import platform


exe_name = 'phantomjs-{0}'.format(platform)
exe_path = path.join(path.dirname(path.realpath(__file__)), exe_name)

call(['chmod', '+x', exe_path])

print('starting')
params = '{0} {1}'.format(exe_path, 'phantomjs-test.js').split(' ')
print(params)
pjs_proc = Popen(params)
pjs_proc.wait()
print('done')