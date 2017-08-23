# -*- coding: utf-8 -*-
__author__ = 'n2m'

from rest import crudmgo, crud
from mod_auth import current_user
from bson import ObjectId
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, DateField, validators
import datetime


class AnnForm(Form):
    title = StringField("Title", [crud.put_optional, validators.Optional()])
    body = StringField("Body", [crud.put_optional, validators.DataRequired()])
    until = DateField("Util", [crud.put_optional, validators.Optional()])
    public = BooleanField("Public", [crud.put_optional, validators.Optional()])
    teacher = BooleanField("For Teachers", [crud.put_optional, validators.Optional()])


class MessageForm(Form):
    title = StringField("Title", [crud.put_optional, validators.Optional()])
    body = StringField("Body", [crud.put_optional, validators.DataRequired()])
    to = StringField("To", [crud.put_optional, validators.Optional()])
    ann = StringField("Announcement", [crud.put_optional, validators.Optional()])


class Announcement(crudmgo.RootDocument):
    __collection__ = "announcements"
    __form__ = AnnForm

    structure = {
        "title": basestring,
        "summary": basestring,
        "body": basestring,
        "tags": [],
        "created": {
            "username": basestring,
            "by": ObjectId,
            "on": datetime.datetime
        },
        "squad_code": [basestring],
        "until": datetime.datetime,
        "status": bool,
        "public": bool,
        "teacher": bool,
        "lang": basestring,
        "meta": {}
    }
    indexes = [
        {"fields": ["until", "status"]},
        {"fields": ["public"]},
        {"fields": ["teacher"]},
        {"fields": ["squad_code", "status"]}
    ]
    default_values = {"created.by": lambda: current_user["_id"], "teacher": False, "public": False,
                      "created.username": lambda: "iZ HERO TEAM" if current_user.has_role("administrator") else current_user["username"],
                      "created.on": crudmgo.localtime, "status": True, "tags": [], "meta": {}, "title": ""}

    def update_public(self, value):
        if current_user.has_role("administrator"):
            self["public"] = bool(value)
            if value:
                self["teacher"] = False

    def update_teacher(self, value):
        if current_user.has_role("administrator"):
            self["teacher"] = bool(value)
            if value:
                self["public"] = False

    def update_body(self, value):
        self["summary"] = value.replace("\n", " ").replace("\r", " ")[0:100] if value else ""
        self["body"] = value

    def markread(self, autosave=True):
        if current_user.has_role("administrator") or not self.get("_id"):
            return
        inbox = self.collection.database["Inbox"].getuserinbox()
        inbox.markread(self["_id"], False, autosave)
        return inbox

    def markannread(self, ann, is_model=False, autosave=True):
        if current_user.has_role("administrator"):
            return

        inbox = self.collection.database["Inbox"].getuserinbox()
        for a in ann:
            inbox.markread(a, is_model, autosave)
        inbox.save()
        return inbox


class Inbox(crudmgo.RootDocument):
    __collection__ = "inboxes"
    _read_set = None

    structure = {
        "read": [ObjectId]
    }
    indexes = [
        {"fields": "read"}
    ]
    default_values = {"read": []}

    def getuserinbox(self, userid=None, makeset=True):
        if not userid:
            userid = current_user["_id"]

        inbox = self.find_one({"_id": userid})
        hasinbox = bool(inbox and inbox.get("read"))

        if not hasinbox:
            inbox = self()
            inbox["_id"] = userid

        if not inbox.get("read"):
            inbox["read"] = []

        if makeset:
            inbox._read_set = set(inbox["read"])

        return inbox

    def markread(self, ann, is_model=False, autosave=True):
        if not self.get("_id"):
            return

        if not self._read_set:
            self._read_set = set(self.get("read") or [])

        if is_model:
            self._read_set.add(ann.get("_id"))
        elif isinstance(ann, ObjectId):
            self._read_set.add(ann)
        elif ObjectId.is_valid(ann):
            self._read_set.add(ObjectId(ann))
        else:
            return

        if autosave:
            self.save()

    def save(self, *args, **kargs):
        if self._read_set:
            self["read"] = list(self._read_set)
        return super(Inbox, self).save(*args, **kargs)


class Message(crudmgo.RootDocument):
    __collection__ = "messages"
    __form__ = MessageForm

    structure = {
        "title": basestring,
        "summary": basestring,
        "body": basestring,
        "ann": ObjectId,
        "updated": datetime.datetime,
        "created": {
            "username": basestring,
            "by": ObjectId,
            "on": datetime.datetime
        },
        "replies": [{
            "body": basestring,
            "created": {
                "username": basestring,
                "by": ObjectId,
                "on": datetime.datetime
            }
        }],
        "to": ObjectId,
        "meta": {}
    }
    indexes = [
        {"fields": ["ann"]},
        {"fields": ["created.by"]},
        {"fields": ["to"]}
    ]
    default_values = {"created.by": lambda: current_user["_id"], "to": None, "ann": None,
                      "created.username": lambda: "iZ HERO TEAM" if current_user.has_role("administrator") else current_user["username"],
                      "created.on": crudmgo.localtime, "updated": crudmgo.localtime}

    def markread(self, autosave=True):
        if not self.get("meta"):
            self["meta"] = {}

        isreceipt = self.isreceipt()
        if not isreceipt and self["meta"].get("hasreply"):
            self["meta"]["hasreply"] = False
        elif isreceipt and not self["meta"].get("read"):
            self["meta"]["read"] = True

        if autosave:
            self.save()

    def markunread(self, autosave=True):
        if not self.get("meta"):
            self["meta"] = {}

        if self.isreceipt():
            self["meta"]["hasreply"] = True
        else:
            self["meta"]["read"] = False

        if autosave:
            self.save()

    def addreply(self, body, autosave=True):
        if not self.get("replies"):
            self["replies"] = []

        timenow = crudmgo.localtime()

        self["replies"].insert(0, {
            "body": body,
            "created": {
                "username": current_user["username"] if current_user.has_role("teacher") else "iZ HERO TEAM",
                "by": current_user["_id"],
                "on": timenow
            }
        })

        self.markunread(False)
        self["updated"] = timenow

        if autosave:
            self.save()

    def isreceipt(self):
        return (current_user.has_role("administrator") and not self.get("to")) or \
               (self.get("to") == current_user["_id"])

    def update_body(self, value):
        self["summary"] = value.replace("\n", " ").replace("\r", " ")[0:100] if value else ""
        self["body"] = value

    def update_to(self, value):
        if not isinstance(value, ObjectId) and ObjectId.is_valid(value):
            self["to"] = ObjectId(value)
        else:
            self["to"] = None

    def update_ann(self, value):
        if not isinstance(value, ObjectId) and ObjectId.is_valid(value):
            self["ann"] = ObjectId(value)
        else:
            self["ann"] = None
