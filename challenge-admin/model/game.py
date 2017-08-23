# -*- coding: utf-8 -*-
__author__ = 'n2m'

from rest import crudmgo
from mod_auth import current_user
from .trail_modify import TrailDocument
import datetime


class Game(TrailDocument):
    __collection__ = "games"
    _trail_modify = "modified"

    structure = {
        "title": basestring,
        "descr": basestring,
        "cover": basestring,
        "price": int,
        "game_code": basestring,
        "status": bool,
        "meta": {},
        "created": {
            "by": basestring,
            "on": datetime.datetime,
            "username": basestring
        },
        "modified": [{
            "by": basestring,
            "on": datetime.datetime,
            "username": basestring
        }]
    }
    indexes = [
        {"fields": "price"},
        {"fields": "status"},
        {"fields": "game_code",
         "unique": True}
    ]
    default_values = {"created.by": lambda: current_user.id, "created.on": crudmgo.localtime, "meta": {}, "price": 0,
                      "created.username": lambda: current_user.get_username(), "status": True, "modified": []}