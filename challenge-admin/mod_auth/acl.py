# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import abort
from functools import wraps
from . import current_user, current_userid


class requires(object):
    req = None

    def __init__(self, req):
        self.req = req

    def __call__(self, func):
        @wraps(func)
        def check(*args, **kargs):
            if not self.req():
                abort(403)
            return func(*args, **kargs)
        return check


def requires_login(func):
    @wraps(func)
    def check(*args, **kargs):
        if not current_userid:
            abort(400)
        return func(*args, **kargs)
    return check


class requires_role(object):
    roles = None

    def __init__(self, roles):
        self.roles = roles

    def __call__(self, func):
        @wraps(func)
        def check(*args, **kargs):
            u = current_user
            if u.is_anonymous:
                abort(400)
            if not u.has_role(self.roles):
                abort(403)
            return func(*args, **kargs)
        return check


def requires_anonymous(func):
    @wraps(func)
    def check(*args, **kargs):
        if current_userid:
            abort(403)
        return func(*args, **kargs)
    return check