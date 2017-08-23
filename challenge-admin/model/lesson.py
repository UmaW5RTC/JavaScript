# -*- coding: utf-8 -*-
__author__ = 'n2m'

from rest import crud, crudmgo
from flask.ext.wtf import Form
from wtforms import StringField, IntegerField, validators


class LessonForm(Form):
    no = IntegerField("No.", [crud.put_optional, validators.DataRequired()])
    name = StringField("Name", [crud.put_optional, validators.Optional()])
    objective = StringField("Objective", [crud.put_optional, validators.Optional()])
    keypoints = StringField("Key Learning Points", [crud.put_optional, validators.Optional()])
    time = IntegerField("CW Value", [crud.put_optional, validators.Optional()])
    lang = StringField("Language", [crud.put_optional, validators.DataRequired()])


class Lesson(crudmgo.RootDocument):
    __form__ = LessonForm
    __collection__ = "lessons"
    __crud_searchfield__ = ("name", )

    structure = {
        "no": int,
        "name": basestring,
        "time": int,
        "objective": basestring,
        "keypoints": basestring,
        "pdf": basestring,
        "ppt": basestring,
        "lang": basestring
    }
    required = ["no", "name"]
    default_values = {"lang": "en"}
