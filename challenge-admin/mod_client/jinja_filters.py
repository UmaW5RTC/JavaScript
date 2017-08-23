from datetime import datetime
from flask import current_app, g, abort, request
from mod_auth import current_user
from . import client, SUPPORTED_LANG, DEFAULT_LANG


@client.context_processor
def utility_processor():

    return {
        'current_user': current_user,
        'now': datetime.now}


@client.url_defaults
def add_language_code(endpoint, values):
    values.setdefault('lang', (hasattr(g, "lang") and g.lang) or request.accept_languages.best_match(SUPPORTED_LANG) or DEFAULT_LANG)


@client.url_value_preprocessor
def pull_lang_code(endpoint, values):
    lang = values.pop('lang', request.accept_languages.best_match(SUPPORTED_LANG) or DEFAULT_LANG)

    if lang not in SUPPORTED_LANG:
        abort(404)

    g.lang = lang


