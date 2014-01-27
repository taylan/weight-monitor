from flask import request, url_for


def url_for_lang(lang):
    args = request.args.copy()
    args['hl'] = lang
    return url_for(request.endpoint, **args)
