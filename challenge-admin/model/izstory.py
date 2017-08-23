# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, IntegerField, DateField, validators
from rest import crudmgo, crud
from mod_auth import current_user
from bson import ObjectId
from .trail_modify import TrailDocument
import datetime


class IZStoryForm(Form):
    title = StringField("Title", [crud.put_optional, validators.DataRequired()])
    cover = StringField("Cover Picture", [crud.put_optional, validators.DataRequired()])
    nickname = StringField("Nickname", [crud.put_optional, validators.Optional()])
    bgcolor = StringField("Background Colour", [crud.put_optional, validators.Optional()])
    bgimage = StringField("Background Picture", [crud.put_optional, validators.Optional()])
    textcolor = StringField("Text Colour", [crud.put_optional, validators.Optional()])


class IZStory(TrailDocument):
    __collection__ = "izstories"
    __form__ = IZStoryForm
    _trail_modify = "modified"

    structure = {
        "title": basestring,
        "cover": basestring,
        "nickname": basestring,
        "bgcolor": basestring,
        "bgimage": basestring,
        "textcolor": basestring,
        "pages": [{
            "id": ObjectId,
            "image": basestring,
            "caption": basestring,
            "bgcolor": basestring,
            "bgimage": basestring,
            "textcolor": basestring
        }],
        "created": {
            "username": basestring,
            "by": ObjectId,
            "on": datetime.datetime
        },
        "modified": [{
            "username": basestring,
            "by": ObjectId,
            "on": datetime.datetime
        }],
        "status": bool,
        "meta": {},
        "group": bool,
        "public": bool
    }
    indexes = [
        {"fields": ["status", "created.by"]}
    ]
    default_values = {"created.by": lambda: current_user["_id"], "created.username": lambda: current_user["username"],
                      "created.on": crudmgo.localtime, "status": True, "group": False, "public": False}