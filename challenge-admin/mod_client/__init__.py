# -*- coding: utf-8 -*-
__author__ = 'jonathannew'

from flask import Blueprint

client = Blueprint('client', __name__)

SUPPORTED_LANG = ['en', 'ko', 'es']
DEFAULT_LANG = 'en'

import jinja_filters
import views

