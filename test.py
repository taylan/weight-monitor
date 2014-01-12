from subprocess import Popen, call
from os import path, rename
from sys import platform
from uuid import uuid4



exe_name = '_phantomjs-{0}'.format(platform)
exe_path = path.join(path.dirname(path.realpath(__file__)), exe_name)

call(['chmod', '+x', exe_path])
dest_file_name = '{0}.png'.format(uuid4())

print('starting')
params = '{0} {1} {2}'.format(exe_path, 'phantomjs-test.js', dest_file_name).split(' ')
print(params)
pjs_proc = Popen(params)
pjs_proc.wait()
print('done')


print('fuhu!' if path.exists(dest_file_name) else 'fuk!')