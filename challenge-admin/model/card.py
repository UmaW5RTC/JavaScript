__author__ = 'n2m'

from rest import crudmgo
from mod_auth import current_user
from .trail_modify import TrailDocument
import datetime
import random
import pymongo


class Card(TrailDocument):
    __collection__ = "cards"
    _trail_modify = "modified"

    structure = {
        "no": int,
        "code": basestring,
        "name": basestring,
        "descr": basestring,
        "price": int,
        "status": bool,
        "rarity": int,
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
        {"fields": "no",
         "check": False},
        {"fields": ["status", "rarity"],
         "check": False},
        {"fields": ["status", "no"],
         "check": False},
        {"fields": ["code", "status"],
         "check": False}
    ]
    default_values = {"created.by": lambda: current_user.id, "created.on": crudmgo.localtime, "price": 0, "rarity": 1,
                      "meta": {}, "created.username": lambda: current_user.get_username(), "status": True,
                      "modified": []}

    def cardsbyrarity(self):
        cards = self.find({"status": True})
        cardr = [[], [], []]
        for c in cards:
            if 1 <= c["rarity"] <= 3:
                cardr[c["rarity"] - 1].append(c)
        return cardr

    def rollcard(self, cards=None):
        if not cards or not isinstance(cards, (list, tuple)):
            cards = self.cardsbyrarity()

        r = random.randint(1, 100)
        if 1 <= r <= 2 and 2 in cards and cards[2]:
            card = random.choice(cards[2])
        elif 3 <= r <= 7 and 1 in cards and cards[1]:
            card = random.choice(cards[1])
        else:
            card = random.choice(cards[0])
        return card
