from babel import Locale
from flask import request, url_for
from flask_babel import gettext


def url_for_lang(lang):
    args = request.args.copy()
    args['hl'] = lang
    return url_for(request.endpoint, **args)


def lang_name(code):
    return Locale(code).languages[code]


def get_translation(msgid):
    return gettext(msgid)


def slugify(s):
    return s.lower().replace(' ', '-')
