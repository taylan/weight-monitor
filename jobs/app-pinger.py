from urllib import request
from os import environ
from urllib.parse import urljoin

request.urlopen(urljoin(environ['APPURL'], 'static/dummy.html')).read()
