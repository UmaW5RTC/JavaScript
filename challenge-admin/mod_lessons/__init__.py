# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename
from flask.ext import restful
from rest import crudmgo
from mod_auth import acl
from bson import ObjectId
import os

admin_powers = crudmgo.CrudMgoBlueprint("admin_powers", __name__, model="Power")
admin_missions = crudmgo.CrudMgoBlueprint("admin_missions", __name__, model="Mission")
admin_competencies = crudmgo.CrudMgoBlueprint("admin_competencies", __name__, model="SELCompetency")
admin_cwtopics = crudmgo.CrudMgoBlueprint("admin_cwtopics", __name__, model="CWTopic")
admin_cwvalues = crudmgo.CrudMgoBlueprint("admin_cwvalues", __name__, model="CWValue")
admin_lessons = crudmgo.CrudMgoBlueprint("admin_lessons", __name__, model="Lesson")

teacher_powers = crudmgo.CrudMgoBlueprint("teacher_powers", __name__, model="Power")
teacher_missions = crudmgo.CrudMgoBlueprint("teacher_missions", __name__, model="Mission")
teacher_competencies = crudmgo.CrudMgoBlueprint("teacher_competencies", __name__, model="SELCompetency")
teacher_cwtopics = crudmgo.CrudMgoBlueprint("teacher_cwtopics", __name__, model="CWTopic")
teacher_cwvalues = crudmgo.CrudMgoBlueprint("teacher_cwvalues", __name__, model="CWValue")


@admin_powers.resource
class PowerList(crudmgo.ListAPI):
    order = "pos"
    limit = 0
    method_decorators = [acl.requires_role("administrator")]


@admin_powers.resource
class PowerItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("administrator")]


@admin_missions.resource
class MissionList(crudmgo.ListAPI):
    limit = 0
    method_decorators = [acl.requires_role("administrator")]

    def get(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("power", type=str, store_missing=False)
        args = pr.parse_args()

        if args.get("power") and ObjectId.is_valid(args["power"]):
            self.filter_by = {"power_id": ObjectId(args["power"])}

        return super(MissionList, self).get()


@admin_missions.resource
class MissionItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("administrator")]


@admin_competencies.resource
class CompetencyList(crudmgo.ListAPI):
    limit = 0
    method_decorators = [acl.requires_role("administrator")]


@admin_competencies.resource
class CompetencyItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("administrator")]


@admin_cwtopics.resource
class CWTopicList(crudmgo.ListAPI):
    limit = 0
    method_decorators = [acl.requires_role("administrator")]


@admin_cwtopics.resource
class CWTopicItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("administrator")]


@admin_cwvalues.resource
class CWValueList(crudmgo.ListAPI):
    limit = 0
    method_decorators = [acl.requires_role("administrator")]


@admin_cwvalues.resource
class CWValueItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("administrator")]


@teacher_powers.resource
class TPowerList(crudmgo.ListAPI):
    order = "pos"
    limit = 0
    readonly = True
    method_decorators = [acl.requires_role("teacher")]


@teacher_powers.resource
class TPowerItem(crudmgo.ItemAPI):
    readonly = True
    method_decorators = [acl.requires_role("teacher")]


@teacher_missions.resource
class TMissionList(crudmgo.ListAPI):
    order = "code"
    limit = 0
    readonly = True
    method_decorators = [acl.requires_role("teacher")]

    def get(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("power", type=str, store_missing=False)
        pr.add_argument("competency", type=str, store_missing=False)
        pr.add_argument("topic", type=str, store_missing=False)
        pr.add_argument("value", type=str, store_missing=False)
        args = pr.parse_args()
        self.filter_by = {}

        if args.get("power") and ObjectId.is_valid(args["power"]):
            self.filter_by["power_id"] = ObjectId(args["power"])
        if args.get("competency") and ObjectId.is_valid(args["competency"]):
            self.filter_by["selcompetency"] = ObjectId(args["competency"])
        if args.get("topic") and ObjectId.is_valid(args["topic"]):
            self.filter_by["cwtopic"] = ObjectId(args["topic"])
        if args.get("value") and ObjectId.is_valid(args["value"]):
            self.filter_by["cwvalue"] = ObjectId(args["value"])

        return super(TMissionList, self).get()


@teacher_missions.resource
class TMissionItem(crudmgo.ItemAPI):
    readonly = True
    method_decorators = [acl.requires_role("teacher")]


@teacher_competencies.resource
class TCompetencyList(crudmgo.ListAPI):
    readonly = True
    limit = 0
    method_decorators = [acl.requires_role("teacher")]


@teacher_competencies.resource
class TCompetencyItem(crudmgo.ItemAPI):
    readonly = True
    method_decorators = [acl.requires_role("teacher")]


@teacher_cwtopics.resource
class TCWTopicList(crudmgo.ListAPI):
    readonly = True
    limit = 0
    method_decorators = [acl.requires_role("teacher")]


@teacher_cwtopics.resource
class TCWTopicItem(crudmgo.ItemAPI):
    readonly = True
    method_decorators = [acl.requires_role("teacher")]


@teacher_cwvalues.resource
class TCWValueList(crudmgo.ListAPI):
    readonly = True
    limit = 0
    method_decorators = [acl.requires_role("teacher")]


@teacher_cwvalues.resource
class TCWValueItem(crudmgo.ItemAPI):
    readonly = True
    method_decorators = [acl.requires_role("teacher")]


@admin_lessons.resource
class LessonList(crudmgo.ListAPI):
    limit = 0
    method_decorators = [acl.requires_role("administrator")]
    order = "no"

    def get(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()

        self.filter_by = {"lang": args.get("lang") or "en"}

        return super(LessonList, self).get()

    def _setfilter(self, item):
        item = super(LessonList, self)._setfilter(item)
        lid = item.get("_id") or ObjectId()
        item["_id"] = lid
        return save_lesson_file(lid, item)


@admin_lessons.resource
class LessonItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("administrator")]

    def _updateitem(self, itemid, data, item=None):
        item, err = super(LessonItem, self)._updateitem(itemid, data, item)
        if not err:
            item = save_lesson_file(item["_id"], item)
        return item, err


@admin_lessons.resource
class LessonTeachList(crudmgo.ListAPI):
    limit = 0
    method_decorators = [acl.requires_role("teacher")]
    order = "no"
    readonly = True

    def get(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()

        self.filter_by = {"lang": args.get("lang") or "en"}

        return super(LessonTeachList, self).get()


@admin_lessons.resource
class LessonTeachItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("teacher")]
    readonly = True


def save_lesson_file(lid, item):
    if item:
        if "pdf" in request.files and \
                request.files["pdf"].filename != "" and \
                request.files["pdf"].filename.lower().endswith(".pdf"):
            f = request.files["pdf"]
            filename = str(lid) + "-" + secure_filename(f.filename)
            f.save(os.path.join(current_app.config.get("UPLOAD_FOLDER", "uploads"), "lessons", filename))
            item["pdf"] = filename
        if "ppt" in request.files and \
                request.files["ppt"].filename != "" and \
                (request.files["ppt"].filename.lower().endswith(".ppt") or request.files["ppt"].filename.lower().endswith(".pptx")):
            f = request.files["ppt"]
            filename = str(lid) + "-" + secure_filename(f.filename)
            f.save(os.path.join(current_app.config.get("UPLOAD_FOLDER", "uploads"), "lessons", filename))
            item["ppt"] = filename
    return item


api = restful.Api(admin_powers)
api.add_resource(PowerList, "", endpoint="powers")
api.add_resource(PowerList, "/", endpoint="powers_slash")
api.add_resource(PowerItem, "/item/<itemid>", endpoint="power")

api = restful.Api(admin_missions)
api.add_resource(MissionList, "", endpoint="missions")
api.add_resource(MissionList, "/", endpoint="missions_slash")
api.add_resource(MissionItem, "/item/<itemid>", endpoint="mission")

api = restful.Api(admin_competencies)
api.add_resource(CompetencyList, "", endpoint="competencies")
api.add_resource(CompetencyList, "/", endpoint="competencies_slash")
api.add_resource(CompetencyItem, "/item/<itemid>", endpoint="competency")

api = restful.Api(admin_cwtopics)
api.add_resource(CWTopicList, "", endpoint="topics")
api.add_resource(CWTopicList, "/", endpoint="topics_slash")
api.add_resource(CWTopicItem, "/item/<itemid>", endpoint="topic")

api = restful.Api(admin_cwvalues)
api.add_resource(CWValueList, "", endpoint="values")
api.add_resource(CWValueList, "/", endpoint="values_slash")
api.add_resource(CWValueItem, "/item/<itemid>", endpoint="value")

api = restful.Api(admin_lessons)
api.add_resource(LessonList, "", endpoint="lessons")
api.add_resource(LessonList, "/", endpoint="lessons_slash")
api.add_resource(LessonItem, "/item/<itemid>", endpoint="lesson")
api.add_resource(LessonTeachList, "/teacher", endpoint="tlessons")
api.add_resource(LessonTeachList, "/teacher/", endpoint="tlessons_slash")
api.add_resource(LessonTeachItem, "/teacher/item/<itemid>", endpoint="tlesson")


api = restful.Api(teacher_powers)
api.add_resource(TPowerList, "", endpoint="powers")
api.add_resource(TPowerList, "/", endpoint="powers_slash")
api.add_resource(TPowerItem, "/item/<itemid>", endpoint="power")

api = restful.Api(teacher_missions)
api.add_resource(TMissionList, "", endpoint="missions")
api.add_resource(TMissionList, "/", endpoint="missions_slash")
api.add_resource(TMissionItem, "/item/<itemid>", endpoint="mission")

api = restful.Api(teacher_competencies)
api.add_resource(TCompetencyList, "", endpoint="competencies")
api.add_resource(TCompetencyList, "/", endpoint="competencies_slash")
api.add_resource(TCompetencyItem, "/item/<itemid>", endpoint="competency")

api = restful.Api(teacher_cwtopics)
api.add_resource(TCWTopicList, "", endpoint="topics")
api.add_resource(TCWTopicList, "/", endpoint="topics_slash")
api.add_resource(TCWTopicItem, "/item/<itemid>", endpoint="topic")

api = restful.Api(teacher_cwvalues)
api.add_resource(TCWValueList, "", endpoint="values")
api.add_resource(TCWValueList, "/", endpoint="values_slash")
api.add_resource(TCWValueItem, "/item/<itemid>", endpoint="value")
