# -*- coding: utf-8 -*-
__author__ = 'n2m'

from rest import crudmgo, crud
from mod_auth import current_user
from bson import ObjectId
from dateutil import parser, tz
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, DateField, validators
import datetime

FRIENDS = {
    "naam": {
        "code": "naam",
        "name": "Master Naam",
        "text": "",
        "last": None,
        "unread": 0,
        "mission": "",
        "progress": ""
    },
    "jj": {
        "code": "jj",
        "name": "J.J.",
        "text": "",
        "last": None,
        "unread": 0,
        "mission": "",
        "progress": ""
    },
    "nana": {
        "code": "nana",
        "name": "Nana",
        "text": "",
        "last": None,
        "unread": 0,
        "mission": "",
        "progress": ""
    },
    "drpark": {
        "code": "drpark",
        "name": "Dr. Park",
        "text": "",
        "last": None,
        "unread": 0,
        "mission": "",
        "progress": ""
    },
    "courage": {
        "code": "courage",
        "name": "Courage",
        "text": "",
        "last": None,
        "unread": 0,
        "mission": "",
        "progress": ""
    },
    "smart": {
        "code": "smart",
        "name": "Smart",
        "text": "",
        "last": None,
        "unread": 0,
        "mission": "",
        "progress": ""
    },
    "snooper": {
        "code": "snooper",
        "name": "Snooper",
        "text": "",
        "last": None,
        "unread": 0,
        "mission": "",
        "progress": ""
    },
    "boolee": {
        "code": "boolee",
        "name": "Boolee",
        "text": "",
        "last": None,
        "unread": 0,
        "mission": "",
        "progress": ""
    },
    "brutus": {
        "code": "brutus",
        "name": "Brutus",
        "text": "",
        "last": None,
        "unread": 0,
        "mission": "",
        "progress": ""
    },
    "lu": {
        "code": "lu",
        "name": "Lu",
        "text": "",
        "last": None,
        "unread": 0,
        "mission": "",
        "progress": ""
    },
    "safe": {
        "code": "safe",
        "name": "Safe",
        "text": "",
        "last": None,
        "unread": 0,
        "mission": "",
        "progress": ""
    },
    "mabel": {
        "code": "mabel",
        "name": "Mabel",
        "text": "",
        "last": None,
        "unread": 0,
        "mission": "",
        "progress": ""
    },
    "grace": {
        "code": "grace",
        "name": "Grace",
        "text": "",
        "last": None,
        "unread": 0,
        "mission": "",
        "progress": ""
    },
    "goldenrule": {
        "code": "goldenrule",
        "name": "Lu, Master Naam Group Chat",
        "text": "",
        "last": None,
        "unread": 0,
        "mission": "",
        "progress": ""
    },
    "izhero": {
        "code": "izhero",
        "name": "DQ World",
        "text": "",
        "last": None,
        "unread": 0,
        "mission": "",
        "progress": ""
    }
}


class Messenger(crudmgo.RootDocument):
    __collection__ = "messengers"
    __friends__ = FRIENDS

    structure = {
        "missions": {},
        "userid": ObjectId,
        "friends": {},
        "arrange": [],
        "meta": {}
    }
    indexes = [
        {"fields": ["userid"],
         "unique": True,
         "check": False}
    ]
    required = ["userid"]
    default_values = {"userid": lambda: current_user.id, "meta": {}}

    def start(self, init=True):
        if current_user.is_anonymous:
            return None

        m = self.find_one({"userid": current_user.id})
        if m is None and init:
            m = self()
            m["userid"] = current_user.id
            m["friends"] = []
            m["meta"] = {}
            m.save()
        return m

    def add_friend(self, code, save=True):
        if code not in FRIENDS:
            return None

        if not isinstance(self.get("friends"), dict):
            self["friends"] = {}
        elif code in self["friends"]:
            return self["friends"][code]

        self["friends"][code] = FRIENDS[code].copy()
        if not isinstance(self.get("arrange"), list):
            self["arrange"] = []
        self["arrange"].insert(0, code)
        if save:
            self.save()
        return self["friends"][code]

    def update_friend(self, code, text, time, unread, mission=None, progress=None, save=True):
        if code not in FRIENDS:
            return False

        self.add_friend(code, False)
        self["friends"][code]["text"] = text
        self["friends"][code]["last"] = time

        if unread is True:
            self["friends"][code]["unread"] += 1
        elif isinstance(unread, int) and not isinstance(unread, bool):
            self["friends"][code]["unread"] = unread

        if isinstance(mission, basestring):
            self["friends"][code]["mission"] = mission
        if isinstance(progress, basestring):
            self["friends"][code]["progress"] = progress

        if self["arrange"][0] != code:
            found = False
            i = len(self["arrange"]) - 1
            for c in reversed(self["arrange"]):
                if found:
                    self["arrange"][i+1] = c
                elif c == code:
                    found = True
                i -= 1
            self["arrange"][0] = code
        if save:
            self.save()

        return True

    def friend_update_mission(self, code, mission, progress="", save=True):
        if code not in FRIENDS or code not in self.get("friends", {}):
            return

        self["friends"][code]["mission"] = mission
        self["friends"][code]["progress"] = progress
        if save:
            self.save()

    def mark_readall(self, code, update=True):
        if code not in FRIENDS or code not in self.get("friends", {}) or not self["friends"][code].get("unread"):
            return

        if update:
            chatlog = self.collection.database["ChatLog"].collection
            chatlog.update({"userid": self["userid"], "unread": True, "friend": code},
                           {"$set": {"unread": False}},
                           multi=True)
        self["friends"][code]["unread"] = 0
        self.save()

    def unread(self, code):
        if code not in FRIENDS or code not in self.get("friends", {}) or not self["friends"][code].get("unread"):
            return 0
        return self["friends"][code]["unread"]

    def friend_complete_mission(self, code, save=True):
        self.friend_update_mission(code, "", save=save)

    def complete_mission(self, mission, save=True):
        if not isinstance(self.get("missions"), dict):
            self["missions"] = {}
        if mission not in self["missions"]:
            self["missions"][mission] = True
            if save:
                self.save()

    def meta(self, name, default=None):
        if isinstance(self.get("meta"), dict):
            return self["meta"].get(name, default)
        return default

    def set_meta(self, name, value):
        if not isinstance(self.get("meta"), dict):
            self["meta"] = {}
        self["meta"][name] = value
        self.save()


class ChatForm(Form):
    friend = StringField("Friend", [crud.put_optional, validators.DataRequired()])
    text = StringField("Text", [crud.put_optional, validators.Optional()])
    video = StringField("Video", [crud.put_optional, validators.Optional()])
    unread = BooleanField("Unread", [crud.put_optional, validators.Optional()], default=False)
    me = BooleanField("Me", [crud.put_optional, validators.Optional()], default=False)
    sender = StringField("Sender", [crud.put_optional, validators.Optional()])


class ChatLog(crudmgo.RootDocument):
    __collection__ = "chatlogs"
    __form__ = ChatForm

    structure = {
        "userid": ObjectId,
        "friend": basestring,
        "text": basestring,
        "time": datetime.datetime,
        "video": basestring,
        "unread": bool,
        "me": bool,
        "sender": basestring,
        "meta": {}
    }
    indexes = [
        {"fields": ["userid", "friend", "-time"],
         "check": False}
    ]
    required = ["userid", "friend", "time"]
    default_values = {"userid": lambda: current_user.id, "time": crudmgo.localtime,
                      "unread": False, "me": False, "meta": {}}

    def newline(self, messengerid, friend):
        c = self()
        c["messengerid"] = messengerid
        c["friend"] = friend
        return c

    def meta(self, name, default=None):
        if isinstance(self.get("meta"), dict):
            return self["meta"].get(name, default)
        return default

    def set_meta(self, name, value):
        if not isinstance(self.get("meta"), dict):
            self["meta"] = {}
        self["meta"][name] = value
        self.save()

    def update_friend(self, value):
        if value not in FRIENDS:
            return "Friend does not exists"

        self["friend"] = value

    def update_time(self, value):
        try:
            self["time"] = parser.parse(value)
            if not self["time"].tzinfo:
                self["time"].replace(tzinfo=tz.tzutc())
        except ValueError:
            return "Invalid date/time"

    # just used to prevent users from updating meta dict using http post
    def update_meta(self, value):
        pass
