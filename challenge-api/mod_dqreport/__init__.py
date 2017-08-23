# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify
from flask.ext.restful import Api, Resource
from mod_auth import current_user, acl
from rest import crudmgo

survey_rcode = crudmgo.CrudMgoBlueprint("test_rcode", __name__, model="PreDQResult")


@survey_rcode.resource
class Pretest(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self, surveyid=None):
        usr = current_user._get_current_object()
        if not self.model.has_dqresult(usr) or not surveyid:
            res = self.model.get_dqresult(usr)
        else:
            res = self.model()
            res.calc_dqscore(usr.id, surveyid)
        return jsonify(res.get_dqscores() if res else {})


@survey_rcode.resource
class ScreenTime(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self):
        usr = current_user._get_current_object()
        res = self.db["ScreentimeDQResult"].get_dqresult(usr)
        return jsonify(res.get_dqscores() if res else {})


@survey_rcode.resource
class Privacy(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self):
        usr = current_user._get_current_object()
        res = self.db["PrivacyDQResult"].get_dqresult(usr)
        return jsonify(res.get_dqscores() if res else {})


@survey_rcode.resource
class Cyberbullying(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self):
        usr = current_user._get_current_object()
        res = self.db["CyberbullyingDQResult"].get_dqresult(usr)
        return jsonify(res.get_dqscores() if res else {})


@survey_rcode.resource
class DigitalCitizens(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self):
        usr = current_user._get_current_object()
        res = self.db["DigitalcitizensDQResult"].get_dqresult(usr)
        return jsonify(res.get_dqscores() if res else {})


@survey_rcode.resource
class DigitalFootprint(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self):
        usr = current_user._get_current_object()
        res = self.db["DigitalfootprintDQResult"].get_dqresult(usr)
        return jsonify(res.get_dqscores() if res else {})


@survey_rcode.resource
class Security(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self):
        usr = current_user._get_current_object()
        res = self.db["SecurityDQResult"].get_dqresult(usr)
        return jsonify(res.get_dqscores() if res else {})


@survey_rcode.resource
class CriticalThinking(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self):
        usr = current_user._get_current_object()
        res = self.db["CriticalthinkingDQResult"].get_dqresult(usr)
        return jsonify(res.get_dqscores() if res else {})


@survey_rcode.resource
class Empathy(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self):
        usr = current_user._get_current_object()
        res = self.db["EmpathyDQResult"].get_dqresult(usr)
        return jsonify(res.get_dqscores() if res else {})


@survey_rcode.resource
class DQScore(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self):
        usr = current_user._get_current_object()
        d = {}

        res = self.db["ScreentimeDQResult"].get_dqresult(usr, True)
        if res:
            d["sc_mgmt_score"] = res.get("sc_mgmt_score")

        res = self.db["PrivacyDQResult"].get_dqresult(usr, True)
        if res:
            d["pri_pi_mgmt_score"] = res.get("pri_pi_mgmt_score")

        res = self.db["CyberbullyingDQResult"].get_dqresult(usr, True)
        if res:
            d["cb_score"] = res.get("cb_score")

        res = self.db["DigitalcitizensDQResult"].get_dqresult(usr, True)
        if res:
            d["dc_identity_score"] = res.get("dc_identity_score")

        res = self.db["DigitalfootprintDQResult"].get_dqresult(usr, True)
        if res:
            d["df_mgmt_score"] = res.get("df_mgmt_score")

        res = self.db["SecurityDQResult"].get_dqresult(usr, True)
        if res:
            d["sec_score"] = res.get("sec_score")

        res = self.db["CriticalthinkingDQResult"].get_dqresult(usr, True)
        if res:
            d["ct_score"] = res.get("ct_score")

        res = self.db["EmpathyDQResult"].get_dqresult(usr, True)
        if res:
            d["emp_de_score"] = res.get("emp_de_score")

        return jsonify(d)


api_surveyr = Api(survey_rcode)
api_surveyr.add_resource(Pretest, "/pretest", endpoint="pretest_r")
api_surveyr.add_resource(Pretest, "/pretest/<surveyid>", endpoint="pretest_r_sid")
api_surveyr.add_resource(ScreenTime, "/screentime", endpoint="screentime_r")
api_surveyr.add_resource(Privacy, "/privacy", endpoint="privacy_r")
api_surveyr.add_resource(Cyberbullying, "/cyberbullying", endpoint="cyberbullying_r")
api_surveyr.add_resource(DigitalCitizens, "/digitalcitizens", endpoint="digitalcitizens_r")
api_surveyr.add_resource(DigitalFootprint, "/digitalfootprint", endpoint="digitalfootprint_r")
api_surveyr.add_resource(Security, "/security", endpoint="security_r")
api_surveyr.add_resource(CriticalThinking, "/criticalthinking", endpoint="criticalthinking_r")
api_surveyr.add_resource(Empathy, "/empathy", endpoint="empathy_r")
api_surveyr.add_resource(DQScore, "/score", endpoint="score_r")
