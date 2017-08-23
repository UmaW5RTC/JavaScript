# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask.ext import restful
from flask import jsonify
from rest import crud
from mod_auth import acl
from . import util

admin_presurvey = crud.CrudBlueprint("admin_presurvey", __name__, model="survey")
admin_postsurvey = crud.CrudBlueprint("admin_postsurvey", __name__, model="survey")


@admin_presurvey.resource
class PreSurveyList(crud.ListAPI):
    readonly = True
    filter_by = {"surveyid": 1, "status": -1}
    method_decorators = [acl.requires_role("administrator")]


@admin_presurvey.resource
class PreSurveyItem(crud.ItemAPI):
    readonly = True
    filter_by = {"surveyid": 1, "status": -1}
    method_decorators = [acl.requires_role("administrator")]

    def get(self, itemid):
        data = self._getitem(itemid)
        if data is None:
            return jsonify({})
        data = crud.model_to_json(data, is_single=True)
        s = []

        for q in data["answers"]:
            qns = util.get_pre_question(q["qns"])
            ans = util.get_pre_answer(q["qns"], q["ansnum"], q["anstext"])
            choice = util.get_pre_choice(q["qns"], q["ansnum"])
            qns = append_surveyheader(s, qns)
            append_surveyqns(s, q, qns, ans, choice)

        data["survey"] = s
        del(data["answers"])
        return jsonify(data)


@admin_postsurvey.resource
class PostSurveyList(crud.ListAPI):
    readonly = True
    filter_by = {"surveyid": 2, "status": -1}
    method_decorators = [acl.requires_role("administrator")]


@admin_postsurvey.resource
class PostSurveyItem(crud.ItemAPI):
    readonly = True
    filter_by = {"surveyid": 2, "status": -1}
    method_decorators = [acl.requires_role("administrator")]

    def get(self, itemid):
        data = self._getitem(itemid)
        if data is None:
            return jsonify({})
        data = crud.model_to_json(data, is_single=True)
        s = []

        for q in data["answers"]:
            qns = util.get_post_question(q["qns"])
            ans = util.get_post_answer(q["qns"], q["ansnum"], q["anstext"])
            choice = util.get_post_choice(q["qns"], q["ansnum"])
            qns = append_surveyheader(s, qns)
            append_surveyqns(s, q, qns, ans, choice)

        data["survey"] = s
        del(data["answers"])
        return jsonify(data)


preapi = restful.Api(admin_presurvey)
preapi.add_resource(PreSurveyList, '/', endpoint='surveys')
preapi.add_resource(PreSurveyItem, '/item/<int:itemid>', endpoint='survey')

postapi = restful.Api(admin_postsurvey)
postapi.add_resource(PostSurveyList, '/', endpoint='surveys')
postapi.add_resource(PostSurveyItem, '/item/<int:itemid>', endpoint='survey')


def append_surveyheader(s, qns):
    if isinstance(qns, dict):
        if isinstance(qns["h"], tuple):
            for i in xrange(len(qns["h"])):
                s.append({"no": None, "qns": qns["h"][i], "ans": None, "choice": None})
        else:
            s.append({"no": None, "qns": qns["h"], "ans": None, "choice": None})
        qns = qns["q"]
    return qns


def append_surveyqns(s, q, qns, ans, choice):
    if isinstance(qns, tuple):
        for i in xrange(len(qns)):
            s.append({"no": q["qns"],
                      "qns": qns[i],
                      "ans": ans[i],
                      "choice": choice[i]})
    else:
        s.append({"no": q["qns"], "qns": qns, "ans": ans, "choice": choice})