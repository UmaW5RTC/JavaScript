# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask.ext import restful
from rest import crudmgo
from mod_auth import acl
from flask import abort, request, jsonify
from bson import ObjectId


admin_survey = crudmgo.CrudMgoBlueprint("admin_survey", __name__, model="Survey")
admin_answer = crudmgo.CrudMgoBlueprint("admin_answer", __name__, model="SurveyAnswer")


@admin_survey.resource
class SurveyList(crudmgo.ListAPI):
    method_decorators = [acl.requires_role("administrator")]


@admin_survey.resource
class SurveyItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("administrator")]

    def _updateitem(self, itemid, data, item=None):
        if item is None:
            item = self._getitem(itemid)
        if item is None:
            return None, "Item not found."
        if isinstance(item.get("meta"), dict) and item["meta"].get("locked"):
            return None, "Survey locked"
        return super(SurveyItem, self)._updateitem(itemid, data, item)


@admin_survey.resource
class SurveyQns(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("administrator"), lambda x:ObjectId(x) if ObjectId.is_valid(x) else abort(404)]

    def post(self, itemid):
        q = self.question()
        if q["qns"] != "" and q["typ"] != "":
            self.model.collection.update({"_id": itemid, "meta.locked": {"$ne": True}},
                                         {"questions": {"$push": q}})
            return jsonify(q)
        return jsonify()

    def _put(self, itemid):
        item = self.model.find_one({"questions.qid": itemid}, fields={"questions.$": 1})
        if item is None:
            return {"success": False, "error": "Item not found."}
        if isinstance(item.get("meta"), dict) and item["meta"].get("locked"):
            return {"success": False, "error": "Survey locked"}

        q = item["questions"][0]
        q = self.question(q)

        self.model.collection.update({"questions.qid": itemid}, {"$set": {"questions.$": q}})
        return q

    def delete(self, itemid):
        self.model.collection.update({"questions.qid": itemid, "meta.locked": {"$ne": True}},
                                     {"$pull": {"questions": {"qid": itemid}}})
        return jsonify(success=True)

    @staticmethod
    def question(q=None):
        if q is None:
            q = {"qid": ObjectId, "qns": "", "typ": "", "opt": {}, "meta": {}}
        else:
            q = q.copy()

        json = request.json
        qns = unicode(json.get("qns", ""))
        typ = str(json.get("typ", ""))
        opt = json.get("opt")
        if qns != "":
            q["qns"] = qns
        if typ != "":
            q["typ"] = typ
        if isinstance(opt, dict) and len(opt) > 0:
            q["opt"] = opt
        return q


@admin_survey.resource
class SurveyQnsMv(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("administrator"), lambda x:ObjectId(x) if ObjectId.is_valid(x) else abort(404)]

    def post(self, itemid):
        item = self.model.find_one({"questions.qid": itemid, "meta.locked": {"$ne": True}}, fields={"questions": 1})
        if item is None:
            abort(404)

        l = len(item["questions"])
        moved = False
        for i in xrange(l):
            if item["questions"][i] == itemid and i < l-1:
                q = item["questions"][i]
                item["questions"][i] = item["questions"][i+1]
                item["questions"][i+1] = q
                self.model.collection.update({"questions.qid": itemid, "meta.locked": {"$ne": True}},
                                             {"$set": {"questions": item["questions"]}})
                moved = True
                break
        return jsonify(success=moved)

    def put(self, itemid):
        item = self.model.find_one({"questions.qid": itemid, "meta.locked": {"$ne": True}}, fields={"questions": 1})
        if item is None:
            abort(404)

        l = len(item["questions"])
        moved = False

        try:
            pos = int(request.json.get("pos"))
        except (ValueError, TypeError):
            return jsonify(success=False)

        if pos < 0 or pos >= l:
            return jsonify(success=False)

        for i in xrange(l):
            if item["questions"][i] == itemid and pos != i:
                q = item["questions"][i]
                item["questions"][i] = item["questions"][pos]
                item["questions"][pos] = q
                self.model.collection.update({"questions.qid": itemid, "meta.locked": {"$ne": True}},
                                             {"$set": {"questions": item["questions"]}})
                moved = True
                break
        return jsonify(success=moved)

    def delete(self, itemid):
        item = self.model.find_one({"questions.qid": itemid, "meta.locked": {"$ne": True}}, fields={"questions": 1})
        if item is None:
            abort(404)

        l = len(item["questions"])
        moved = False
        for i in xrange(l):
            if item["questions"][i] == itemid and i > 0:
                q = item["questions"][i]
                item["questions"][i] = item["questions"][i-1]
                item["questions"][i-1] = q
                self.model.collection.update({"questions.qid": itemid, "meta.locked": {"$ne": True}},
                                             {"$set": {"questions": item["questions"]}})
                moved = True
                break
        return jsonify(success=moved)


@admin_answer.resource
class SurveyAnswerList(crudmgo.ListAPI):
    method_decorators = [acl.requires_role("administrator")]

    def get(self, surveyid=None):
        if surveyid is None or not ObjectId.is_valid(surveyid):
            return abort(404)

        self.filter_by = {"surveyid": ObjectId(surveyid)}
        return super(SurveyAnswerList, self).get()


survey = restful.Api(admin_survey)
