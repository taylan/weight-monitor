from urllib import request
from os import environ

request.urlopen(environ['APPURL']).read()