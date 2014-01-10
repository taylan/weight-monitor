from subprocess import Popen
from os import path
from sys import platform


phantomjs_paths ={
    'win32': 'lib/phantomjs/phantomjs-win32/phantomjs.exe',
    'darwin': 'lib/phantomjs/phantomjs-darwin/phantomjs',
    'linux': 'lib/phantomjs/phantomjs-linux/phantomjs'
}


phantomjs_path = phantomjs_paths.get(platform, '')
if not phantomjs_path:
    print('No PhantomJS executable defined for platform {0}.'.format(platform))
exe_path = path.join(path.dirname(path.realpath(__file__)), phantomjs_path)
print(exe_path)
print('{0} {1} '.format(exe_path, path.join(path.dirname(path.realpath(__file__)), 'phantomjs-test.js')))

print('starting')
pjs_proc = Popen('{0} {1} '.format(exe_path, path.join(path.dirname(path.realpath(__file__)), 'phantomjs-test.js')))
pjs_proc.wait()
print('done')