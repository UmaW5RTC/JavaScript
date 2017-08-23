__author__ = 'n2m'

from rest import crudmgo
from mod_auth import current_user
from bson import ObjectId
from .trail_modify import TrailDocument
import datetime


class Comic(TrailDocument):
    __collection__ = "comics"
    _trail_modify = "modified"

    structure = {
        "title": {},
        "descr": basestring,
        "cover": basestring,
        "price": int,
        "pages": [basestring],
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
        {"fields": "status"}
    ]
    default_values = {"created.by": lambda: current_user.id, "created.on": crudmgo.localtime, "meta": {}, "price": 0,
                      "created.username": lambda: current_user.get_username(), "status": True, "modified": []}


class CollectionShelf(crudmgo.RootDocument):
    __collection__ = "collectionshelf"

    structure = {
        "_id": ObjectId,
        "comics": [{
            "id": ObjectId,
            "purchased": datetime.datetime
        }],
        "stickers": [{
            "id": ObjectId,
            "purchased": datetime.datetime
        }],
        "cards": [{
            "id": ObjectId,
            "count": int,
            "purchased": datetime.datetime
        }]
    }
    indexes = [
        {"fields": ["comics.id", "_id"],
         "check": False},
        {"fields": ["cards.id", "_id"],
         "check": False}
    ]
    default_values = {"comics": [], "stickers": [], "cards": []}

    def getshelf(self, userid):
        try:
            if not isinstance(userid, ObjectId):
                userid = ObjectId(userid)
            shelf = self.find_one({"_id": userid})
            if not shelf:
                shelf = self()
                shelf["_id"] = userid
                shelf["comics"] = []
                shelf["stickers"] = []
                shelf["cards"] = []
            return shelf
        except Exception:
            pass

        return None

    def has_comic(self, comicid):
        if not isinstance(comicid, ObjectId):
            comicid = ObjectId(comicid)

        if self.get("_id") and self.get("comics"):
            for c in self["comics"]:
                if c["id"] == comicid:
                    return True
        return False

    def get_comiclist(self):
        comics = self.get("comics") or []
        return [c["id"] for c in comics]

    def add_comic(self, comicid):
        if self.get("_id"):
            if not isinstance(comicid, ObjectId):
                comicid = ObjectId(comicid)
            if not self.get("comics"):
                self["comics"] = []

            self["comics"].append({
                "id": comicid,
                "purchased": crudmgo.utctime()
            })

            self.save()
            return True
        return False

    def has_card(self, cardid):
        return self.get_card(cardid) is not None

    def get_card(self, cardid):
        if self.get("_id") and self.get("cards"):
            if not isinstance(cardid, ObjectId):
                cardid = ObjectId(cardid)

            for c in self["cards"]:
                if c["id"] == cardid:
                    return c
        return None

    def add_card(self, cardid):
        if self.get("_id"):
            if not isinstance(cardid, ObjectId):
                cardid = ObjectId(cardid)
            if not self.get("cards"):
                self["cards"] = []

            c = self.get_card(cardid)
            if c is not None:
                c["count"] += 1
            else:
                self["cards"].append({
                    "id": cardid,
                    "count": 1,
                    "purchased": crudmgo.utctime()
                })

            self.save()
            return True
        return False

    def get_cardlist(self):
        cards = self.get("cards") or []
        return [c["id"] for c in cards]

    def get_cardmap(self):
        cards = self.get("cards") or []
        return {c["id"]: c for c in cards}

    def remove_card(self, cardid):
        c = self.get_card(cardid)
        if c is not None:
            c["count"] -= 1
            if c["count"] == 0:
                self.collection.update({"_id": self["_id"]}, {"$pull": {"cards": {"id": cardid}}})
                self.reload()
            else:
                self.save()
            return True
        return False
