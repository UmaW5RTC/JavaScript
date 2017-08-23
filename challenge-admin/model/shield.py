# -*- coding: utf-8 -*-
__author__ = 'n2m'

from rest import crudmgo
from bson import ObjectId
import datetime


class ShieldCode(crudmgo.RootDocument):
    __collection__ = "shieldcodes"

    structure = {
        "name": basestring,
        "code": basestring,
        "claimed": [
            {"username": basestring,
             "by": ObjectId,
             "on": datetime.datetime}
        ],
        "expiry": basestring,
        "limits": int,
        "rewards": {
            "coins": int,
            "points": int
        }
    }
    indexes = [
        {"fields": ["code", "claimed.by"],
         "check": False},
        {"fields": "expiry"},
        {"fields": "claimed.by",
         "check": False}
    ]
    required = ["name", "code"]
    default_values = {"claimed": []}

    def insert_user(self, user):
        self.collection.update({"_id": self["_id"]},
                               {"$push": {"claimed": {"username": user["username"],
                                                      "by": user["_id"],
                                                      "on": crudmgo.utctime()}}})