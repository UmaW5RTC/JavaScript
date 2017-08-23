# -*- coding: utf-8 -*-
__author__ = 'n2m'

from rest import crudmgo
from bson import ObjectId
from pymongo import errors
import datetime
import random


def generate_code(prefix="", i=10):
    if not isinstance(prefix, basestring):
        prefix = ""
    slist = "01234578ABCDEFGHJKMNPQRTUVWXY"
    return prefix.upper() + "".join(random.choice(slist) for _ in xrange(i))


def humanify_code(code):
    if not isinstance(code, basestring) or len(code) == 0:
        return code

    code = code.upper()
    chars = code[1:]
    code = code[0]
    i = 0

    for c in chars:
        i += 1
        if i % 4 == 0:
            code += "-"
        code += c

    return code


def parse_code(code):
    if not isinstance(code, basestring) or len(code) == 0:
        return code

    code = code.upper().replace("-", "").replace("6", "G").replace("9", "G")
    return code.replace("I", "1").replace("L", "1").replace("O", "0").replace("S", "5").replace("Z", "2")


class DQReportAccess(crudmgo.RootDocument):
    __collection__ = "dqreportaccesses"

    structure = {
        "userid": ObjectId,
        "username": basestring,
        "code": basestring,
        "receipt": basestring,
        "orderid": basestring,
        "email": basestring,
        "createdon": datetime.datetime,
        "byadminname": basestring,
        "byadmin": ObjectId,
        "meta": {}
    }
    indexes = [
        {"fields": "code",
         "unique": True,
         "check": False},
        {"fields": "orderproduct",
         "unique": True,
         "sparse": True,
         "check": False},
        {"fields": ["userid"],
         "check": False}
    ]
    required = ["code"]
    default_values = {"createdon": crudmgo.localtime, "userid": None, "meta": {}}

    def new_dqreport(self, admin=None, orderid=None, i=None, email=None):
        mem = self()
        if admin:
            mem["byadminname"] = admin.get_username()
            mem["byadmin"] = admin.id

        if email:
            mem["email"] = email

        if orderid:
            mem["orderid"] = orderid
            if i is not None:
                try:
                    mem["orderproduct"] = "%s-%s" % (orderid, str(i))
                    mem.save()
                except errors.DuplicateKeyError:
                    return 0
                except Exception:
                    return None

        while True:
            try:
                mem["code"] = generate_code("DR")
                mem.save()
                break
            except errors.DuplicateKeyError:
                pass
            except Exception:
                return None

        return mem

    def find_by_orderid_i(self, orderid, i):
        return self.find_one({"orderproduct": "%s-%s" % (orderid, str(i))})

    def meta(self, name, default=None):
        if isinstance(self.get("meta"), dict):
            return self["meta"].get(name, default)
        return default

    def set_meta(self, name, value, save=True):
        if not isinstance(self.get("meta"), dict):
            self["meta"] = {}
        self["meta"][name] = value
        if save:
            self.save()


class Membership(crudmgo.RootDocument):
    __collection__ = "memberships"

    structure = {
        "userid": ObjectId,
        "username": basestring,
        "code": basestring,
        "started": datetime.datetime,
        "duration": int,
        "expiry": datetime.datetime,
        "dqreport": bool,
        "school": ObjectId,
        "sponsor": basestring,
        "receipt": basestring,
        "orderid": basestring,
        "email": basestring,
        "createdon": datetime.datetime,
        "byadminname": basestring,
        "byadmin": ObjectId,
        "meta": {}
    }
    indexes = [
        {"fields": "code",
         "unique": True,
         "check": False},
        {"fields": "orderproduct",
         "unique": True,
         "sparse": True,
         "check": False},
        {"fields": ["userid"],
         "check": False}
    ]
    required = ["code", "duration"]
    default_values = {"createdon": crudmgo.localtime, "userid": None, "meta": {}, "duration": 0,
                      "expiry": lambda: datetime.datetime.max}

    def new_member(self, duration=0, dqreport=False, sponsor="", admin=None, orderid=None, i=None, email=None):
        mem = self()
        mem["sponsor"] = sponsor
        mem["duration"] = 0 if not isinstance(duration, int) or duration <= 0 else duration
        mem["dqreport"] = bool(dqreport)
        if mem["duration"] == 0:
            mem["expiry"] = datetime.datetime.max
        if admin:
            mem["byadminname"] = admin.get_username()
            mem["byadmin"] = admin.id

        if email:
            mem["email"] = email

        if orderid:
            mem["orderid"] = orderid
            if i is not None:
                try:
                    mem["orderproduct"] = "%s-%s" % (orderid, str(i))
                    mem.save()
                except errors.DuplicateKeyError:
                    return 0
                except Exception:
                    return None

        while True:
            try:
                mem["code"] = generate_code("NM")
                mem.save()
                break
            except errors.DuplicateKeyError:
                pass
            except Exception:
                return None

        return mem

    def find_by_orderid_i(self, orderid, i):
        return self.find_one({"orderproduct": "%s-%s" % (orderid, str(i))})

    def meta(self, name, default=None):
        if isinstance(self.get("meta"), dict):
            return self["meta"].get(name, default)
        return default

    def set_meta(self, name, value):
        if not isinstance(self.get("meta"), dict):
            self["meta"] = {}
        self["meta"][name] = value
        self.save()


class SchoolMembership(crudmgo.RootDocument):
    __collection__ = "schoolmemberships"

    structure = {
        "userid": ObjectId,
        "username": basestring,
        "code": basestring,
        "studentcode": basestring,
        "membership": {
            "count": int,
            "assigned": int
        },
        "sponsor": basestring,
        "school": basestring,
        "country": basestring,
        "receipt": basestring,
        "orderid": basestring,
        "email": basestring,
        "createdon": datetime.datetime,
        "byadminname": basestring,
        "byadmin": ObjectId,
        "meta": {}
    }
    indexes = [
        {"fields": "code",
         "unique": True,
         "check": False},
        {"fields": "orderproduct",
         "unique": True,
         "sparse": True,
         "check": False},
        {"fields": ["userid"],
         "check": False}
    ]
    required = ["code"]
    default_values = {"membership": {"count": 0, "assigned": 0}, "createdon": crudmgo.localtime,
                      "userid": None, "meta": {}}

    def new_member(self, count=0, sponsor="", admin=None, orderid=None, i=None, email=None):
        mem = self()
        mem["membership"] = {
            "count": count,
            "assigned": 0
        }
        mem["sponsor"] = sponsor
        if admin:
            mem["byadminname"] = admin.get_username()
            mem["byadmin"] = admin.id

        if email:
            mem["email"] = email

        if orderid:
            mem["orderid"] = orderid
            if i is not None:
                try:
                    mem["orderproduct"] = "%s-%s" % (orderid, str(i))
                    mem.save()
                except errors.DuplicateKeyError:
                    return 0
                except Exception:
                    return None

        while True:
            try:
                mem["studentcode"] = generate_code("ST")
                mem.save()
                break
            except errors.DuplicateKeyError:
                pass
            except Exception:
                return None

        while True:
            try:
                mem["code"] = generate_code("TE")
                mem.save()
                break
            except errors.DuplicateKeyError:
                pass
            except Exception:
                return None

        return mem

    def find_by_orderid_i(self, orderid, i):
        return self.find_one({"orderproduct": "%s-%s" % (orderid, str(i))})

    def meta(self, name, default=None):
        if isinstance(self.get("meta"), dict):
            return self["meta"].get(name, default)
        return default

    def set_meta(self, name, value):
        if not isinstance(self.get("meta"), dict):
            self["meta"] = {}
        self["meta"][name] = value
        self.save()
