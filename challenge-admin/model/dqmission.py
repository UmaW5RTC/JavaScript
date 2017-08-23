# -*- coding: utf-8 -*-
__author__ = 'n2m'

from rest import crudmgo
from mod_auth import current_user
from bson import ObjectId
import datetime


class DqUserMission(crudmgo.RootDocument):
    __collection__ = "dqusermissions"
    __json_omit__ = ("resumed",)

    structure = {
        "mission": basestring,
        "userid": ObjectId,
        "started": datetime.datetime,
        "checkpoint": [{
            "name": basestring,
            "time": datetime.datetime
        }],
        "resumed": [datetime.datetime],
        "completed": datetime.datetime,
        "meta": {}
    }
    indexes = [
        {"fields": ["userid", "mission", "completed"],
         "check": False},
        {"fields": ["meta.like", "mission"],
         "sparse": True,
         "check": False}
    ]
    required = ["userid", "mission"]
    default_values = {"userid": lambda: current_user.id, "started": crudmgo.localtime, "resumed": [],
                      "checkpoint": [], "completed": None, "meta": {}}

    def start_mission(self, mission):
        if current_user.is_anonymous:
            return False
        m = self.find_one({"userid": current_user.id, "mission": mission, "completed": None})
        if m:
            if not isinstance(m.get("resumed"), list):
                m["resumed"] = []
            m["resumed"].append(crudmgo.localtime())
            if m.meta("isfirst") is None:
                m.set_meta("isfirst",
                           self.collection.find({"userid": current_user.id, "mission": mission}).count() == 1)
            else:
                m.save()
        else:
            m = self()
            m["mission"] = mission
            m.set_meta("isfirst", self.collection.find({"userid": current_user.id, "mission": mission}).count() == 0)

        return m

    def add_checkpoint(self, progress):
        if not isinstance(self.get("checkpoint"), list):
            self["checkpoint"] = []
        l = len(self["checkpoint"])
        if (l > 0 and self["checkpoint"][l-1]["name"] == progress) or (l == 0 and progress == "/"):
            return False

        c = {"name": progress,
             "time": crudmgo.localtime()}
        self["checkpoint"].append(c)
        self.save()
        return c

    def last_checkpoint(self):
        if isinstance(self.get("checkpoint"), list) and len(self["checkpoint"]) > 0:
            return self["checkpoint"][len(self["checkpoint"])-1]
        return None

    def complete(self):
        self["completed"] = crudmgo.localtime()
        self.save()

        return 1 if self.meta("isfirst") else 2

    def is_completed(self):
        return bool(self.get("completed", False))

    def meta(self, name, default=None):
        if isinstance(self.get("meta"), dict):
            return self["meta"].get(name, default)
        return default

    def set_meta(self, name, value):
        if not isinstance(self.get("meta"), dict):
            self["meta"] = {}
        self["meta"][name] = value
        self.save()

    def like(self):
        if not self.is_completed():
            return
        self.set_meta("like", True)

    def dislike(self):
        if not self.is_completed():
            return
        self.set_meta("like", False)
