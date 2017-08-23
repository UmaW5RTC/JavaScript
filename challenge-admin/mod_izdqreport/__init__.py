# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify, make_response
from flask.ext.restful import Api, Resource, reqparse
from mod_auth import acl
from rest import crudmgo, exportmgo
from bson import ObjectId
from dateutil import parser
import datetime

dqresult_rcode = crudmgo.CrudMgoBlueprint("dq_rcode", __name__, model="PreDQResult")


@dqresult_rcode.resource
class PretestDQList(crudmgo.ListAPI):
    method_decorators = [acl.requires_role("administrator")]
    sendcount = True

    def post(self):
        pr = reqparse.RequestParser()
        pr.add_argument("username", type=unicode, store_missing=False)
        args = pr.parse_args()
        username = args.get("username")
        if not username:
            return jsonify(success=False, error="no username")

        user = self.db["IZHero"].find_one({"username": username.lower()})

        if not user:
            return jsonify(success=False, error="user not found")

        r = self.model.get_dqresult(user)
        return jsonify(success=r is not None)

    def delete(self):
        pr = reqparse.RequestParser()
        pr.add_argument("id", type=str, action='append', store_missing=False)
        args = pr.parse_args()
        ids = args.get("id", [])

        if ids:
            for i in xrange(len(ids)):
                if ObjectId.is_valid(ids[i]):
                    ids[i] = ObjectId(ids[i])
            filter_by = {"_id": {"$in": ids}}
            self.model.collection.remove(filter_by)
        return jsonify(success=True)


@dqresult_rcode.resource
class PretestDQExport(exportmgo.MgoExcelAPI):
    method_decorators = [acl.requires_role("administrator")]
    sheet_name = "users DQ"
    fields = [("username", "Username", 25),
              ("demo_name_first", "demo_name_first", 20),
              ("demo_name_last", "demo_name_last", 20),
              ("demo_gender", "demo_gender", 10),
              ("demo_birthyear", "demo_birthyear", 10),
              ("demo_country", "demo_country", 10),
              ("pri_pi_beh_pre_1", "pri_pi_beh_pre_1", 10),
              ("pri_pi_beh_pre_2", "pri_pi_beh_pre_2", 10),
              ("pri_pi_beh_pre_3", "pri_pi_beh_pre_3", 10),
              ("pri_pi_beh_pre_4", "pri_pi_beh_pre_4", 10),
              ("pri_pi_beh_pre_5", "pri_pi_beh_pre_5", 10),
              ("pri_pi_beh_pre_6", "pri_pi_beh_pre_6", 10),
              ("pri_pi_beh_pre_7", "pri_pi_beh_pre_7", 10),
              ("pri_pi_beh_pre_8", "pri_pi_beh_pre_8", 10),
              ("pri_pi_beh_pre_9", "pri_pi_beh_pre_9", 10),
              ("pri_pi_beh_pre_10", "pri_pi_beh_pre_10", 10),
              ("pri_pi_beh_pre_11", "pri_pi_beh_pre_11", 10),
              ("pri_pi_beh_pre_12", "pri_pi_beh_pre_12", 10),
              ("pri_pi_beh_pre_13", "pri_pi_beh_pre_13", 10),
              ("pri_decide_pre", "pri_decide_pre", 10),
              ("pri_pri_skill_pre_1", "pri_pri_skill_pre_1", 10),
              ("pri_pri_skill_pre_2", "pri_pri_skill_pre_2", 10),
              ("pri_pri_skill_pre_3", "pri_pri_skill_pre_3", 10),
              ("pri_pri_skill_pre_4", "pri_pri_skill_pre_4", 10),
              ("pri_pri_skill_pre_5", "pri_pri_skill_pre_5", 10),
              ("df_beh_pre_1", "df_beh_pre_1", 10),
              ("df_beh_pre_2", "df_beh_pre_2", 10),
              ("df_beh_pre_3", "df_beh_pre_3", 10),
              ("df_beh_pre_4", "df_beh_pre_4", 10),
              ("df_beh_pre_5", "df_beh_pre_5", 10),
              ("df_beh_pre_6", "df_beh_pre_6", 10),
              ("df_beh_pre_7", "df_beh_pre_7", 10),
              ("df_beh_pre_8", "df_beh_pre_8", 10),
              ("df_beh_pre_9", "df_beh_pre_9", 10),
              ("df_beh_pre_10", "df_beh_pre_10", 10),
              ("df_dp_quiz_pre_1_1", "df_dp_quiz_pre_1_1", 10),
              ("df_dp_quiz_pre_1_2", "df_dp_quiz_pre_1_2", 10),
              ("df_dp_quiz_pre_1_3", "df_dp_quiz_pre_1_3", 10),
              ("df_dp_quiz_pre_1_4", "df_dp_quiz_pre_1_4", 10),
              ("df_dp_quiz_pre_12_1", "df_dp_quiz_pre_12_1", 10),
              ("df_dp_quiz_pre_12_2", "df_dp_quiz_pre_12_2", 10),
              ("df_dp_quiz_pre_12_3", "df_dp_quiz_pre_12_3", 10),
              ("df_dp_quiz_pre_12_4", "df_dp_quiz_pre_12_4", 10),
              ("df_dp_quiz_pre_12_5", "df_dp_quiz_pre_12_5", 10),
              ("df_dp_quiz_pre_12_6", "df_dp_quiz_pre_12_6", 10),
              ("dc_dt_du_1", "dc_dt_du_1", 10),
              ("dc_dt_du_2", "dc_dt_du_2", 10),
              ("dc_dt_du_3", "dc_dt_du_3", 10),
              ("dc_dt_du_4", "dc_dt_du_4", 10),
              ("dc_dt_du_5", "dc_dt_du_5", 10),
              ("dc_dt_du_6", "dc_dt_du_6", 10),
              ("dc_dt_du_7", "dc_dt_du_7", 10),
              ("dc_dt_du_8", "dc_dt_du_8", 10),
              ("dc_dt_du_9", "dc_dt_du_9", 10),
              ("dt_cong_1_p", "dt_cong_1_p", 10),
              ("dc_citizen_quiz_pre_4_1", "dc_citizen_quiz_pre_4_1", 10),
              ("dc_citizen_quiz_pre_4_2", "dc_citizen_quiz_pre_4_2", 10),
              ("dc_citizen_quiz_pre_4_3", "dc_citizen_quiz_pre_4_3", 10),
              ("dc_citizen_quiz_pre_4_4", "dc_citizen_quiz_pre_4_4", 10),
              ("ct_risk_beh_pre_1", "ct_risk_beh_pre_1", 10),
              ("ct_risk_beh_pre_2", "ct_risk_beh_pre_2", 10),
              ("ct_risk_beh_pre_3", "ct_risk_beh_pre_3", 10),
              ("ct_risk_beh_pre_4", "ct_risk_beh_pre_4", 10),
              ("ct_block_a_pre_1", "ct_block_a_pre_1", 10),
              ("ct_block_a_pre_2", "ct_block_a_pre_2", 10),
              ("ct_block_a_pre_3", "ct_block_a_pre_3", 10),
              ("ct_block_a_pre_4", "ct_block_a_pre_4", 10),
              ("ct_block_a_pre_5", "ct_block_a_pre_5", 10),
              ("ct_block_a_pre_6", "ct_block_a_pre_6", 10),
              ("ct_block_a_pre_7", "ct_block_a_pre_7", 10),
              ("ct_block_a_pre_8", "ct_block_a_pre_8", 10),
              ("ct_literacy_pre_1", "ct_literacy_pre_1", 10),
              ("ct_literacy_pre_2", "ct_literacy_pre_2", 10),
              ("ct_literacy_pre_3", "ct_literacy_pre_3", 10),
              ("cb_risk_pre", "cb_risk_pre", 10),
              ("cb_cbmgmt_pre_1", "cb_cbmgmt_pre_1", 10),
              ("cb_cbmgmt_pre_2", "cb_cbmgmt_pre_2", 10),
              ("cb_cbmgmt_pre_3", "cb_cbmgmt_pre_3", 10),
              ("cb_cbmgmt_pre_4", "cb_cbmgmt_pre_4", 10),
              ("cb_cbmgmt_pre_5", "cb_cbmgmt_pre_5", 10),
              ("cb_cbmgmt_pre_6", "cb_cbmgmt_pre_6", 10),
              ("cb_cbmgmt_pre_7", "cb_cbmgmt_pre_7", 10),
              ("cb_cbmgmt_pre_8", "cb_cbmgmt_pre_8", 10),
              ("cb_cbmgmt_pre_9", "cb_cbmgmt_pre_9", 10),
              ("cb_cbmgmt_pre_10", "cb_cbmgmt_pre_10", 10),
              ("cb_cbatt_pre", "cb_cbatt_pre", 10),
              ("cb_beh_pre", "cb_beh_pre", 10),
              ("emp_emp_6_p", "emp_emp_6_p", 10),
              ("emp_emp_8_p", "emp_emp_8_p", 10),
              ("sec_pwd_act_pre", "sec_pwd_act_pre", 10),
              ("sec_pwd_skill_pre_1", "sec_pwd_skill_pre_1", 10),
              ("sec_pwd_skill_pre_2", "sec_pwd_skill_pre_2", 10),
              ("sec_pwd_skill_pre_3", "sec_pwd_skill_pre_3", 10),
              ("sec_pwd_skill_pre_4", "sec_pwd_skill_pre_4", 10),
              ("sec_popup_pre", "sec_popup_pre", 10),
              ("bst_ga_pre_1", "bst_ga_pre_1", 10),
              ("bst_ga_pre_2", "bst_ga_pre_2", 10),
              ("bst_ga_pre_3", "bst_ga_pre_3", 10),
              ("bst_ga_pre_4", "bst_ga_pre_4", 10),
              ("dc_pm_pre_2", "dc_pm_pre_2", 10),
              ("bst_sr_pre", "bst_sr_pre", 10),
              ("preDQ_pri", "preDQ_pri", 10),
              ("preDQ_df", "preDQ_df", 10),
              ("preDQ_dc", "preDQ_dc", 10),
              ("preDQ_ct", "preDQ_ct", 10),
              ("preDQ_cb", "preDQ_cb", 10),
              ("preDQ_emp", "preDQ_emp", 10),
              ("preDQ_sec", "preDQ_sec", 10),
              ("preDQ_bst", "preDQ_bst", 10)]


@dqresult_rcode.resource
class DQResultCalc(crudmgo.ListAPI):
    method_decorators = [acl.requires_role("administrator")]
    sendcount = True

    def get(self, t=None):
        """db.izheroes.find({'dq_progress.screentimebadge':{$exists:true},'dq_progress.privacybadge':{$exists:true},
                  'dq_progress.cyberbullyingbadge':{$exists:true},'dq_progress.digitalcitizensbadge':{$exists:true},
                  'dq_progress.digitalfootprintbadge':{$exists:true},'dq_progress.securitybadge':{$exists:true},
                  'dq_progress.criticalthinkingbadge':{$exists:true},'dq_progress.empathybadge':{$exists:true},
                  'created': {$gte: ISODate('2016-08-23T00:00:00+0800')}}).count()"""
        heroes = self.db["IZHero"].find({
                    'dq_progress.screentimebadge': {'$exists': True},
                    'dq_progress.privacybadge': {'$exists': True},
                    'dq_progress.cyberbullyingbadge': {'$exists': True},
                    'dq_progress.digitalcitizensbadge': {'$exists': True},
                    'dq_progress.digitalfootprintbadge': {'$exists': True},
                    'dq_progress.securitybadge': {'$exists': True},
                    'dq_progress.criticalthinkingbadge': {'$exists': True},
                    'dq_progress.empathybadge': {'$exists': True},
                    'created': {'$gte': parser.parse('2016-08-23T00:00:00+0800')}
        })
        l = []
        data = ""

        for u in heroes:
            pd = self.model.get_dqresult(u)
            st = self.db["ScreentimeDQResult"].get_dqresult(u, True)
            pr = self.db["PrivacyDQResult"].get_dqresult(u, True)
            cb = self.db["CyberbullyingDQResult"].get_dqresult(u, True)
            dc = self.db["DigitalcitizensDQResult"].get_dqresult(u, True)
            df = self.db["DigitalfootprintDQResult"].get_dqresult(u, True)
            se = self.db["SecurityDQResult"].get_dqresult(u, True)
            ct = self.db["CriticalthinkingDQResult"].get_dqresult(u, True)
            em = self.db["EmpathyDQResult"].get_dqresult(u, True)
            re = self.db["RiskEnvPersonalDQResult"].get_dqresult(u, True)

            if pd and st and pr and cb and dc and df and se and ct and em and re:
                if t:
                    st = st.transform_vars()
                    pr = pr.transform_vars()
                    cb = cb.transform_vars()
                    dc = dc.transform_vars()
                    df = df.transform_vars()
                    se = se.transform_vars()
                    ct = ct.transform_vars()
                    em = em.transform_vars()
                    re = re.transform_vars()

                d = {"0username": u["username"],
                     "demo_name_first": u.get("givenname") or "",
                     "demo_name_last": u.get("familyname") or "",
                     "demo_gender": 1 if u.get("gender", "m") == "m" else 2,
                     "demo_birthyear": (isinstance(u.get("dob"), datetime.datetime) and u["dob"].year) or "",
                     "demo_country": u.get("country") or "Singapore",
                     "demo_schoolcode": u.get("school") or ""}
                for k, v in pd.iteritems():
                    if k in ("created", "userid", "meta", "_id", "username"):
                        continue
                    d[k] = v
                for k, v in st.iteritems():
                    if k in ("created", "userid", "meta", "_id"):
                        continue
                    d[k] = v
                for k, v in pr.iteritems():
                    if k in ("created", "userid", "meta", "_id"):
                        continue
                    d[k] = v
                for k, v in cb.iteritems():
                    if k in ("created", "userid", "meta", "_id"):
                        continue
                    d[k] = v
                for k, v in dc.iteritems():
                    if k in ("created", "userid", "meta", "_id"):
                        continue
                    d[k] = v
                for k, v in df.iteritems():
                    if k in ("created", "userid", "meta", "_id"):
                        continue
                    d[k] = v
                for k, v in se.iteritems():
                    if k in ("created", "userid", "meta", "_id"):
                        continue
                    d[k] = v
                for k, v in ct.iteritems():
                    if k in ("created", "userid", "meta", "_id"):
                        continue
                    d[k] = v
                for k, v in em.iteritems():
                    if k in ("created", "userid", "meta", "_id"):
                        continue
                    d[k] = v
                for k, v in re.iteritems():
                    if k in ("created", "userid", "meta", "_id"):
                        continue
                    d[k] = v
                l.append(d)

        count = len(l)

        if count:
            d = l[0]
            keys = sorted(d.keys())
            for k in keys:
                data += k + ","
            data = data[:-1] + "\r\n"
            for i in xrange(count):
                for k in keys:
                    data += unicode(l[i].get(k, 0)).replace(",", " ") + ","
                data = data[:-1] + "\r\n"

        response = make_response(data)
        response.headers["Content-Disposition"] = "attachment; filename=%s" % ("DQ_Y.csv" if t else "DQ_X.csv")
        return response

    def post(self, t=None):
        l = crudmgo.to_flat_value(self.db["DQY"].makeall() if t else self.db["DQX"].makeall())
        return jsonify(results=l, count=len(l))

api_dqresult = Api(dqresult_rcode)
api_dqresult.add_resource(PretestDQList, "", endpoint="dqresults")
api_dqresult.add_resource(PretestDQList, "/", endpoint="dqresults_slash")
api_dqresult.add_resource(PretestDQExport, "/export", endpoint="export")
api_dqresult.add_resource(DQResultCalc, "/calc", endpoint="calc")
api_dqresult.add_resource(DQResultCalc, "/calc/<t>", endpoint="calc_t")
