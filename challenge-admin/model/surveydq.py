# -*- coding: utf-8 -*-
__author__ = 'n2m'

from rest import crudmgo
from bson import ObjectId
from mod_auth import current_user
import datetime
import pymongo


class SurveyDQ(crudmgo.RootDocument):
    __collection__ = "surveys"
    __json_omit__ = ("created", "modified")

    QUESTION_TYPES = {'radio': 1, 'checkbox': 2, 'scale': 3, 'text': 4}

    structure = {
        "name": basestring,
        "questions": [{
            "qid": ObjectId,
            "qns": basestring,
            "instruct": basestring,
            "typ": int,
            "opt": [],
            "ans": int,
            "meta": {},
            "lang": {}
        }],
        "meta": {},
        "created": {
            "by": ObjectId,
            "username": basestring,
            "on": datetime.datetime
        },
        "modified": [{
            "by": ObjectId,
            "on": datetime.datetime
        }]
    }

    indexes = [
        {"fields": ["questions.qid", "meta.locked"],
         "check": False}
    ]
    required = ["name"]
    default_values = {"created.on": crudmgo.localtime,
                      "created.by": lambda: current_user["_id"] if not current_user.is_anonymous else None,
                      "created.username": lambda: current_user.get("username") if not current_user.is_anonymous else None}

    def lock(self, save=False):
        if not isinstance(self.get("meta"), dict):
            self["meta"] = {}
        if self["meta"].get("locked"):
            return

        self["meta"]["locked"] = True
        if save:
            self.save()

    def unlock(self, save=False):
        if not isinstance(self.get("meta"), dict):
            return
        if not self["meta"].get("locked"):
            return

        self["meta"]["locked"] = False
        if save:
            self.save()

    def update_mod(self, save=False):
        if not isinstance(self["modified"], list):
            self["modified"] = []
        m = {"by": current_user["_id"], "on": crudmgo.localtime}
        self["modified"].append(m)
        if save:
            self.save()
        return m

    def meta(self, name, default=None):
        if isinstance(self.get("meta"), dict):
            return self["meta"].get(name, default)
        return default

    def set_meta(self, name, value):
        if not isinstance(self.get("meta"), dict):
            self["meta"] = {}
        self["meta"][name] = value
        self.save()


class SurveyDQAnswer(crudmgo.RootDocument):
    __collection__ = "surveyanswers"
    __json_omit__ = ("modified",)

    structure = {
        "surveyid": ObjectId,
        "surveyname": basestring,
        "missionid": ObjectId,
        "answers": [{
            "no": int,
            "qns": basestring,
            "qid": ObjectId,
            "ans": basestring,
            "anslist": [int],
            "ansval": int
        }],
        "meta": {},
        "created": {
            "by": ObjectId,
            "username": basestring,
            "on": datetime.datetime
        },
        "modified": [{
            "by": ObjectId,
            "on": datetime.datetime
        }]
    }

    indexes = [
        {"fields": ["answers.qid"],
         "check": False},
        {"fields": ["created.by", "surveyid"],
         "check": False},
        {"fields": ["surveyid", "missionid"],
         "check": False}
    ]
    # required = ["surveyid", "answers"]
    default_values = {"created.on": crudmgo.localtime,
                      "created.by": lambda: current_user["_id"] if not current_user.is_anonymous else None,
                      "created.username": lambda: current_user.get("username") if not current_user.is_anonymous else None,
                      "answers": [], "meta": {}, "modified": []}

    def update_mod(self, save=False):
        if not isinstance(self["modified"], list):
            self["modified"] = []
        m = {"by": current_user["_id"], "on": crudmgo.localtime}
        self["modified"].append(m)
        if save:
            self.save()
        return m

    def meta(self, name, default=None):
        if isinstance(self.get("meta"), dict):
            return self["meta"].get(name, default)
        return default

    def set_meta(self, name, value):
        if not isinstance(self.get("meta"), dict):
            self["meta"] = {}
        self["meta"][name] = value
        self.save()


class QuizResult(crudmgo.RootDocument):
    __collection__ = "quizresults"

    structure = {
        "surveyid": ObjectId,
        "score": int,
        "incorrect": [int],
        "incorrect_qid": [ObjectId],
        "meta": {},
        "created": {
            "by": ObjectId,
            "username": basestring,
            "on": datetime.datetime
        }
    }

    indexes = [
        {"fields": ["created.by", "surveyid"],
         "check": False},
        {"fields": ["surveyid", "score"],
         "check": False}
    ]
    default_values = {"meta": {}, "created.on": crudmgo.localtime,
                      "created.by": lambda: current_user["_id"] if not current_user.is_anonymous else None,
                      "created.username": lambda: current_user.get("username") if not current_user.is_anonymous else None}


class PollAnswer(crudmgo.RootDocument):
    __collection__ = "pollanswers"

    structure = {
        "poll": basestring,
        "answer": {
            "code": basestring,
            "value": basestring
        },
        "lang": basestring,
        "created": {
            "by": ObjectId,
            "username": basestring,
            "on": datetime.datetime
        }
    }
    default_values = {"created.on": crudmgo.localtime,
                      "created.by": lambda: current_user["_id"] if not current_user.is_anonymous else None,
                      "created.username": lambda: current_user.get("username") if not current_user.is_anonymous else None,
                      "lang": "en"}


class PollResult(crudmgo.RootDocument):
    __collection__ = "pollresults"

    structure = {
        "poll": basestring,
        "lang": basestring,
        "answer": {
            "code": basestring,
            "value": basestring,
            "count": int
        }
    }

    indexes = [
        {"fields": ["poll", "lang", "answer.code"],
         "unique": True,
         "check": False},
        {"fields": "answer.count",
         "check": False}
    ]
    default_values = {"lang": "en"}

    def add_result(self, poll, code, value, lang="en"):
        db = self.collection.database
        ans = db["PollAnswer"]()
        ans["poll"] = poll
        ans["lang"] = lang
        ans["answer"] = {
            "code": code,
            "value": value
        }
        ans.save()
        res = self.collection.update({"poll": poll, "lang": lang, "answer.code": code}, {"$inc": {"answer.count": 1}})
        if not res or res.get("nModified", 0) == 0:
            p = self()
            p["poll"] = poll
            p["lang"] = lang
            p["answer"] = {
                "code": code,
                "value": value,
                "count": 1
            }
            p.save()

    def get_results(self, poll, limit=10, lang="en"):
        q = self.find({"poll": poll, "lang": lang}).sort("answer.count", pymongo.DESCENDING)

        if limit:
            q = q.limit(limit)

        agg = self.collection.aggregate([{"$match": {"poll": poll, "lang": lang}},
                                         {"$group": {"_id": None,
                                                     "count": {"$sum": "$answer.count"}}}])
        return q, (agg["result"][0].get("count", 0) if agg.get("result") and len(agg["result"]) > 0 else 0)
