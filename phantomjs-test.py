from subprocess import Popen
from os import path
from sys import platform


phantomjs_paths ={
    'win32': 'bin/phantomjs-win32/phantomjs.exe',
    'darwin': 'bin/phantomjs-darwin/bin/phantomjs',
    'linux': 'bin/phantomjs-linux/bin/phantomjs'
}


phantomjs_path = phantomjs_paths.get(platform, '')
if not phantomjs_path:
    print('No PhantomJS executable defined for platform {0}.'.format(platform))
exe_path = path.join(path.dirname(path.realpath(__file__)), phantomjs_path)

print('starting')
pjs_proc = Popen('{0} phantomjs-test.js'.format(exe_path))
pjs_proc.wait()
print('done')