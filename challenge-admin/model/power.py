# -*- coding: utf-8 -*-
__author__ = 'n2m'

from rest import crud, crudmgo
from flask.ext.wtf import Form
from wtforms import StringField, SelectField, validators
from bson import ObjectId


class CompetencyForm(Form):
    name = StringField("SEL Competency", [crud.put_optional, validators.DataRequired()])
    definition = StringField("Working Definition", [crud.put_optional, validators.DataRequired()])


class TopicForm(Form):
    name = StringField("Cyber Wellness Topic", [crud.put_optional, validators.DataRequired()])


class ValueForm(Form):
    name = StringField("Cyber Wellness Value", [crud.put_optional, validators.DataRequired()])
    definition = StringField("Working Definition", [crud.put_optional, validators.DataRequired()])


class MissionForm(Form):
    id = StringField("ID", [crud.put_optional, validators.DataRequired()])
    code = StringField("Code", [crud.put_optional, validators.DataRequired()])
    name = StringField("Name", [crud.put_optional, validators.DataRequired()])
    power = SelectField("Power", [crud.put_optional, validators.DataRequired()],
                        choices=[("radar", "iZ RADAR"), ("eyes", "iZ EYES"), ("shout", "iZ SHOUT"),
                                 ("protect", "iZ PROTECT"), ("ears", "iZ EARS"), ("control", "iZ CONTROL"),
                                 ("teleport", "iZ TELEPORT")])
    selcompetency = StringField("SEL Competency", [crud.put_optional, validators.DataRequired()])
    cwtopic = StringField("CW Topic", [crud.put_optional, validators.DataRequired()])
    cwvalue = StringField("CW Value", [crud.put_optional, validators.DataRequired()])
    objective = StringField("Learning Objective", [crud.put_optional, validators.DataRequired()])


class SELCompetency(crudmgo.RootDocument):
    __collection__ = "selcompetencies"
    __crud_searchfield__ = ("name",)
    __form__ = CompetencyForm

    structure = {
        "name": basestring,
        "definition": basestring
    }
    indexes = [
        {"fields": "name",
         "unique": True}
    ]
    required = ["name"]


class CWTopic(crudmgo.RootDocument):
    __collection__ = "cwtopics"
    __crud_searchfield__ = ("name",)
    __form__ = TopicForm

    structure = {
        "name": basestring,
        "definition": basestring
    }
    indexes = [
        {"fields": "name",
         "unique": True}
    ]
    required = ["name"]


class CWValue(crudmgo.RootDocument):
    __collection__ = "cwvalues"
    __crud_searchfield__ = ("name",)
    __form__ = ValueForm

    structure = {
        "name": basestring,
        "definition": basestring
    }
    indexes = [
        {"fields": "name",
         "unique": True}
    ]
    required = ["name"]


class Power(crudmgo.RootDocument):
    __collection__ = "powers"
    __crud_searchfield__ = ("name", "id")
    __form__ = MissionForm

    structure = {
        "id": basestring,
        "name": basestring,
        "definition": basestring,
        "pos": int,
        "adventure": int
    }
    indexes = [
        {"fields": "id",
         "unique": True},
        {"fields": "name",
         "unique": True}
    ]
    required = ["id", "name"]


class Mission(crudmgo.RootDocument):
    __collection__ = "missions"
    __crud_searchfield__ = ("name", "id", "sub_mission")

    structure = {
        "id": basestring,
        "code": basestring,
        "name": basestring,
        "power": basestring,
        "power_id": ObjectId,
        "sub_mission": [],
        "rewards": [],
        "selcompetency": [ObjectId],
        "cwtopic": [ObjectId],
        "cwvalue": [ObjectId],
        "level": int,   # easy/intermediate/advanced
        "time": int,
        "objective": basestring,
        "hits": int,
        "completed": int
    }
    indexes = [
        {"fields": "id",
         "unique": True},
        {"fields": "name",
         "unique": True},
        {"fields": "power",
         "unique": True}
    ]
    required = ["id", "name", "power"]
    default_values = {"hits": 0, "completed": 0}

    def update_raw(self, data):
        self["id"] = data.get("id", self.get("id"))
        self["name"] = data.get("name", self.get("name"))
        self["code"] = data.get("code", self.get("code"))
        self["power"] = data.get("power", self.get("power"))
        self["power_id"] = data.get("power_id", self.get("power_id"))

        if self["power_id"] and ObjectId.is_valid(self["power_id"]):
            self["power_id"] = ObjectId(self["power_id"])
            power = self.collection.database["Power"].find_one({"_id": self["power_id"]})
            if power:
                self["power"] = power["name"]

        selcompetencies = data.getlist("selcompetency")
        if selcompetencies and isinstance(selcompetencies, list) and selcompetencies[0] is not None:
            self["selcompetency"] = selcompetencies
            for i in xrange(len(self["selcompetency"])):
                self["selcompetency"][i] = ObjectId(self["selcompetency"][i])

        cwtopics = data.getlist("cwtopic")
        if cwtopics and isinstance(cwtopics, list) and cwtopics[0] is not None:
            self["cwtopic"] = cwtopics
            for i in xrange(len(self["cwtopic"])):
                self["cwtopic"][i] = ObjectId(self["cwtopic"][i])

        cwvalues = data.getlist("cwvalue")
        if cwvalues and isinstance(cwvalues, list) and cwvalues[0] is not None:
            self["cwvalue"] = cwvalues
            for i in xrange(len(self["cwvalue"])):
                self["cwvalue"][i] = ObjectId(self["cwvalue"][i])

        self["level"] = int(data.get("level", self.get("level", 1)))
        self["time"] = int(data.get("time", self.get("time", 5)))
        self["objective"] = data.get("objective", self.get("objective"))
