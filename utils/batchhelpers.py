from babel import support, Locale
from os import path


def get_translations(lang):
    dirname = path.join(path.dirname(__file__), '../translations')
    return support.Translations.load(dirname, [Locale.parse(lang)])
