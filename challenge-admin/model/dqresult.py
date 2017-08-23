__author__ = 'n2m'

from flask import current_app
from rest import crudmgo
from mod_auth import current_user
from bson import ObjectId
from pyper import R
from dqalgo import screentime, privacy, cyberbullying, digitalcitizens, digitalfootprint, security, \
                   criticalthinking, empathy, util
from dateutil import parser
import datetime
import pymongo


class PreDQResult(crudmgo.RootDocument):
    __crud_searchfield__ = ("username", "demo_name_first", "demo_name_last", "demo_country")
    __collection__ = "predqresults"

    structure = {
        "userid": ObjectId,
        "username": basestring,
        "Q1": int,
        "Q1_1": int,
        "Q1_2": int,
        "Q1_3": int,
        "Q1_4": int,
        "Q1_5": int,
        "Q1_6": int,
        "Q1_7": int,
        "Q1_8": int,
        "Q1_9": int,
        "Q1_10": int,
        "Q1_11": int,
        "Q1_12": int,
        "Q1_13": int,
        "Q2_1": int,
        "Q2_2": int,
        "Q2_3": int,
        "Q3": int,
        "Q3_1": int,
        "Q3_2": int,
        "Q3_3": int,
        "Q3_4": int,
        "Q3_5": int,
        "Q4_1": int,
        "Q4_2": int,
        "Q4_3": int,
        "Q4_4": int,
        "Q4_5": int,
        "Q5_ct": int,
        "Q5_cb": int,
        "Q5_1": int,
        "Q5_2": int,
        "Q5_3": int,
        "Q5_4": int,
        "Q5_5": int,
        "Q5_6": int,
        "Q6": int,
        "Q7": float,
        "Q7_1": int,
        "Q7_2": int,
        "Q7_3": int,
        "Q7_4": int,
        "Q7_5": int,
        "Q7_6": int,
        "Q7_7": int,
        "Q7_8": int,
        "Q8": int,
        "Q9_1": int,
        "Q9_2": int,
        "Q9_3": int,
        "Q10": int,
        "Q11": int,
        "Q11_1": int,
        "Q11_2": int,
        "Q11_3": int,
        "Q11_4": int,
        "Q11_5": int,
        "preDQ_pri": float,
        "preDQ_df": float,
        "preDQ_dc": float,
        "preDQ_ct": float,
        "preDQ_cb": float,
        "preDQ_emp": float,
        "preDQ_sec": float,
        "preDQ_bst": float,
        "created": {
            "by": basestring,
            "on": datetime.datetime,
            "username": basestring
        },
        "meta": {}
    }
    indexes = [
        {"fields": "created.by",
         "check": False}
    ]
    default_values = {"created.by": lambda: current_user.id, "created.on": crudmgo.localtime,
                      "created.username": lambda: current_user.get_username(), "meta": {}}

    def get_dqresult(self, user):
        if not user:
            return None

        r = self.find_one({"userid": user.id})
        if not r:
            r = self()
            r["userid"] = user.id
            r["username"] = user.get("username", "")
            # r["demo_name_first"] = user.get("givenname", "")
            # r["demo_name_last"] = user.get("familyname", "")
            # r["demo_gender"] = user.get("gender", "")
            # r["demo_birthyear"] = (isinstance(user.get("dob"), datetime.datetime) and user["dob"].year) or None
            # r["demo_country"] = user.get("country", "")
            if r.calc_dqscore():
                r.save()
            else:
                r = None
        return r

    def has_dqresult(self, user):
        if not user:
            return None

        r = self.find_one({"userid": user.id})
        return r is not None

    def calc_dqscore(self, userid=None, usersurveyid=None):
        if not ObjectId.is_valid(userid):
            userid = None

        if userid:
            userid = ObjectId(userid)
        elif self.get("userid") and isinstance(self["userid"], ObjectId):
            userid = self["userid"]
        else:
            return False

        cfg = {}

        d = self
        r = None
        db = self.collection.database
        model = db["SurveyDQAnswer"]

        if current_app.config.get('R_RCMD'):
            cfg['RCMD'] = current_app.config['R_RCMD']

        try:
            if usersurveyid and ObjectId.is_valid(usersurveyid):
                s_pretest = model.find_one({"_id": ObjectId(usersurveyid),
                                            "created.by": userid})
            else:
                s_pretest = db["SurveyDQ"].find_one({"name": "pretest-full.v2"})
                if not s_pretest:
                    return False

                s_pretest = model.find_one({"surveyid": s_pretest["_id"],
                                            "created.by": userid},
                                           sort=[("_id", pymongo.ASCENDING)])
            if not s_pretest or not self.assign_values(d, s_pretest):
                return False

            r = R(**cfg)
            newd = self.transform_values(d)
            for k, v in newd.iteritems():
                if isinstance(v, (int, float)):
                    r.assign(k, v)

            r(pretest_rsource)

            score = [
                "Q1",
                "Q3",
                "Q5_ct",
                "Q5_cb",
                "Q7",
                "Q11",
                "preDQ_pri",
                "preDQ_df",
                "preDQ_dc",
                "preDQ_ct",
                "preDQ_cb",
                "preDQ_emp",
                "preDQ_sec",
                "preDQ_bst"
            ]

            for k in score:
                self[k] = r.get(k)

            # predq_risk = newd.get("cyber_risk")
            # if isinstance(predq_risk, (int, float)):
            #     self["preDQ_risk"] = predq_risk
            # elif predq_risk is not None and hasattr(predq_risk, "tolist"):
            #     self["preDQ_risk"] = predq_risk.tolist()[0]

            p = r.prog
            r = None
            p.terminate()
        except Exception as e:
            if r and hasattr(r, "prog") and hasattr(r.prog, "terminate"):
                r.prog.terminate()
            return False

        return True

    def get_dqscores(self):
        return {
            "preDQ_pri": self.get("preDQ_pri", 0),
            "preDQ_df": self.get("preDQ_df", 0),
            "preDQ_dc": self.get("preDQ_dc", 0),
            "preDQ_ct": self.get("preDQ_ct", 0),
            "preDQ_cb": self.get("preDQ_cb", 0),
            "preDQ_emp": self.get("preDQ_emp", 0),
            "preDQ_sec": self.get("preDQ_sec", 0),
            "preDQ_bst": self.get("preDQ_bst", 0),
        }

    @staticmethod
    def assign_values(d, s_pretest):
        name = "Q1_"
        for x in xrange(13):
            d[name + str(x+1)] = 0

        d['Q2_1'] = 2
        d['Q2_2'] = 2
        d['Q2_3'] = 2

        name = "Q3_"
        for x in xrange(5):
            d[name + str(x+1)] = 0

        d['Q4_1'] = 0
        d['Q4_2'] = 0
        d['Q4_3'] = 0
        d['Q4_4'] = 0
        d['Q4_5'] = 0

        name = "Q5_"
        for x in xrange(6):
            d[name + str(x+1)] = 0

        d["Q6"] = 0

        name = "Q7_"
        for x in xrange(8):
            d[name + str(x+1)] = 0

        d["Q8"] = 1
        d["Q9_1"] = 1
        d["Q9_2"] = 1
        d["Q9_3"] = 1
        d["Q10"] = 1
        d["Q11_1"] = 1
        d["Q11_2"] = 1
        d["Q11_3"] = 1
        d["Q11_4"] = 1
        d["Q11_5"] = 1

        for i in s_pretest["answers"]:
            if i["no"] == 0:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "Q1_"
                for x in xrange(13):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 1:
                v = int(i.get("ansval") or 0)
                if v == 1:
                    d["Q2_1"] = 0
                elif v == 0:
                    d["Q2_1"] = 1
                else:
                    d["Q2_1"] = 2
            elif i["no"] == 2:
                v = int(i.get("ansval") or 0)
                if v == 1:
                    d["Q2_2"] = 0
                elif v == 0:
                    d["Q2_2"] = 1
                else:
                    d["Q2_2"] = 2
            elif i["no"] == 3:
                v = int(i.get("ansval") or 0)
                if v == 1:
                    d["Q2_3"] = 0
                elif v == 0:
                    d["Q2_3"] = 1
                else:
                    d["Q2_3"] = 2
            elif i["no"] == 4:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "Q3_"
                for x in xrange(5):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 5:
                d['Q4_1'] = int(i.get("ansval") or 0)
            elif i["no"] == 6:
                d['Q4_2'] = int(i.get("ansval") or 0)
            elif i["no"] == 7:
                d['Q4_3'] = int(i.get("ansval") or 0)
            elif i["no"] == 8:
                d['Q4_4'] = int(i.get("ansval") or 0)
            elif i["no"] == 9:
                d['Q4_5'] = int(i.get("ansval") or 0)
            elif i["no"] == 10:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "Q5_"
                for x in xrange(6):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 11:
                d["Q6"] = int(i.get("ansval") or 0)
            elif i["no"] == 12:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "Q7_"
                for x in xrange(8):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 13:
                d["Q8"] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 14:
                d["Q9_1"] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 15:
                d["Q9_2"] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 16:
                d["Q9_3"] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 17:
                d["Q10"] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 18:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "Q11_"
                for x in xrange(5):
                    d[name + str(x+1)] = 1 if x in l else 0
        return True

    @staticmethod
    def transform_values(d):
        newd = d.copy()
        newd["Q2_1"] = 1 if d.get("Q2_1") == 0 else 0
        newd["Q2_2"] = 1 if d.get("Q2_2") == 0 else 0
        newd["Q2_2"] = 1 if d.get("Q2_2") == 0 else 0
        newd["Q4_2"] = 5 - d["Q4_2"] if d.get("Q4_2") > 0 else 0
        newd["Q4_3"] = 5 - d["Q4_3"] if d.get("Q4_3") > 0 else 0
        newd["Q4_4"] = 5 - d["Q4_4"] if d.get("Q4_4") > 0 else 0
        newd["Q8"] = d.get("Q8", 1)
        if d.get("Q8") == 4 or d.get("Q8") == 3:
            newd["Q8"] = 3
        newd["Q10"] = 0
        if d.get("Q10") == 2:
            newd["Q10"] = 3
        elif d.get("Q10") == 3:
            newd["Q10"] = 2
        return newd


class ScreentimeDQResult(crudmgo.RootDocument):
    __collection__ = "screentimedqresults"

    structure = {
        "userid": ObjectId,
        "created": {
            "by": basestring,
            "on": datetime.datetime,
            "username": basestring
        },
        "meta": {}
    }
    indexes = [
        {"fields": "created.by",
         "check": False}
    ]
    default_values = {"created.by": lambda: current_user.id, "created.on": crudmgo.localtime,
                      "created.username": lambda: current_user.get_username(), "meta": {}}

    def get_dqresult(self, user, cacheonly=False):
        if not user:
            return None

        r = self.find_one({"userid": user.id})
        if not r:
            r = self()
            r["userid"] = user.id
            if r.calc_dqscore():
                r.save()
            else:
                r = None
        elif not cacheonly:
            r.calc_dqscore()
            r.save()
        return r

    def has_dqresult(self, user):
        if not user:
            return None

        r = self.find_one({"userid": user.id})
        return r is not None

    def calc_dqscore(self, userid=None):
        if not ObjectId.is_valid(userid):
            userid = None

        if userid:
            userid = ObjectId(userid)
        elif self.get("userid") and isinstance(self["userid"], ObjectId):
            userid = self["userid"]
        else:
            return False

        cfg = {}

        d = self
        r = None
        db = self.collection.database
        model = db["SurveyDQAnswer"]

        if current_app.config.get('R_RCMD'):
            cfg['RCMD'] = current_app.config['R_RCMD']

        try:
            survey = db["SurveyDQ"].find_one({"name": "checkscreen"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or not self.assign_checkscreen(d, survey):
                return False

            survey = db["SurveyDQ"].find_one({"name": "digiworld"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or not self.assign_digiworld(d, survey):
                return False

            survey = db["SurveyDQ"].find_one({"name": "gameaddict"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or not self.assign_gameaddict(d, survey):
                return False

            survey = model.find_one({"surveyname": "selfcontrol-messenger",
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey:
                survey = {"answers": []}
            if not survey or not self.assign_selfcontrol(d, survey):
                return False

            survey = db["SurveyDQ"].find_one({"name": "balancescreen"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or not self.assign_balancescreen(d, survey):
                return False

            survey = db["SurveyDQ"].find_one({"name": "mediarules"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or not self.assign_mediarules(d, survey):
                return False

            survey = db["SurveyDQ"].find_one({"name": "priorities"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or not self.assign_priorities(d, survey):
                return False

            survey = db["SurveyDQ"].find_one({"name": "screentimebadge"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or not self.assign_screentimebadge(d, survey):
                return False

            r = R(**cfg)

            for k, v in d.iteritems():
                if isinstance(v, (int, float)):
                    r.assign(k, v)
            for k, v in self.transform_gameaddict(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_mediarules(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_priorities(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_screentimebadge(d).iteritems():
                r.assign(k, v)

            r(screentime.r_algo)

            self["sc_mgmt_score"] = r.get("sc_mgmt_score")

            p = r.prog
            r = None
            p.terminate()
        except Exception as e:
            if r and hasattr(r, "prog") and hasattr(r.prog, "terminate"):
                r.prog.terminate()
            return False

        return True

    def get_dqscores(self):
        return {
            "sc_mgmt_score": self.get("sc_mgmt_score", 0)
        }

    def transform_vars(self):
        d = {k: v for k, v in self.iteritems()}
        d.update(self.transform_gameaddict(d))
        d.update(self.transform_mediarules(d))
        d.update(self.transform_priorities(d))
        d.update(self.transform_screentimebadge(d))
        return d

    @staticmethod
    def assign_checkscreen(d, survey):
        # pre populate answers
        for i in xrange(24):
            d["bst_screen_video_sd_" + str(i+1)] = 0
            d["bst_screen_video_wd_" + str(i+1)] = 0
            d["bst_screen_game_sd_" + str(i+1)] = 0
            d["bst_screen_game_wd_" + str(i+1)] = 0
            d["bst_screen_sns_sd_" + str(i+1)] = 0
            d["bst_screen_sns_wd_" + str(i+1)] = 0

        for i in survey["answers"]:
            name = None
            if i["no"] == 0:
                name = "bst_screen_video_sd_"
            elif i["no"] == 1:
                name = "bst_screen_video_wd_"
            elif i["no"] == 3:
                name = "bst_screen_game_sd_"
            elif i["no"] == 4:
                name = "bst_screen_game_wd_"
            elif i["no"] == 4:
                name = "bst_screen_sns_sd_"
            elif i["no"] == 4:
                name = "bst_screen_sns_wd_"

            if name:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                for x in xrange(24):
                    d[name + str(x+1)] = 1 if x in l else 0
        return True

    @staticmethod
    def assign_digiworld(d, survey):
        d['dc_dt_du_1'] = 0
        d['dc_dt_du_2'] = 0
        d['dc_dt_du_3'] = 0
        d['dc_dt_du_4'] = 0
        d['dc_dt_du_5'] = 0
        d['dc_dt_du_6'] = 0
        d['dc_dt_du_7'] = 0
        d['dc_dt_du_8'] = 0
        d['dc_dt_du_9'] = 1
        for i in survey["answers"]:
            if i["no"] == 0:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                q = [(1 if x in l else 0) for x in xrange(9)]
                d['dc_dt_du_1'] = q[0]
                d['dc_dt_du_2'] = q[1]
                d['dc_dt_du_3'] = q[2]
                d['dc_dt_du_4'] = q[3]
                d['dc_dt_du_5'] = q[4]
                d['dc_dt_du_6'] = q[5]
                d['dc_dt_du_7'] = q[6]
                d['dc_dt_du_8'] = q[7]
                d['dc_dt_du_9'] = q[8]
        return True

    @staticmethod
    def assign_gameaddict(d, survey):
        for i in xrange(11):
            d["bst_ga_" + str(i+1)] = 0

        for i in survey["answers"]:
            name = None
            if 4 <= i["no"] <= 14:
                name = "bst_ga_" + str(i["no"] - 3)

            if name:
                val = i.get("ansval", 1)
                if val == 0:
                    val = 1
                elif val == 1 or val < 0 or val > 3:
                    val = 0
                d[name] = val
        return True

    @staticmethod
    def assign_selfcontrol(d, survey):
        d["bst_sr_1"] = 1
        d["bst_sr_2"] = 1
        d["bst_sr_3"] = 1
        d["bst_sr_4"] = 1
        d["bst_sr_5"] = 1
        for i in survey["answers"]:
            if i["qns"] == "managetime":
                d["bst_sr_1"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "selfstop":
                a = int(i.get("ansval") or 0)
                if a == 0:
                    d["bst_sr_2"] = 4
                elif a == 1:
                    d["bst_sr_2"] = 3
                elif a == 2:
                    d["bst_sr_2"] = 2
                elif a == 3:
                    d["bst_sr_2"] = 1
            elif i["qns"] == "selfstrategy":
                d["bst_sr_3"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "ideastop":
                d["bst_sr_4"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "seekadvice":
                d["bst_sr_5"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def assign_balancescreen(d, survey):
        name = "bst_gameday_"
        for x in xrange(7):
            d[name + str(x+1)] = 0
        d["bst_gametime_1"] = 1
        name = "bst_gamewhen_"
        for x in xrange(4):
            d[name + str(x+1)] = 0

        for i in survey["answers"]:
            if i["no"] == 0:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "bst_gameday_"
                for x in xrange(7):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 1:
                d["bst_gametime_1"] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 2:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "bst_gamewhen_"
                for x in xrange(4):
                    d[name + str(x+1)] = 1 if x in l else 0
        return True

    @staticmethod
    def assign_mediarules(d, survey):
        d["bst_fmp_0"] = 1
        d["bst_fmp_1"] = 1
        d["bst_fmp_2"] = 1
        d["bst_fmp_3"] = 1
        d["bst_fmp_4"] = 1

        for i in survey["answers"]:
            if i["no"] == 0:
                d["bst_fmp_0"] = 0 if int(i.get("ansval") or 0) else 1
            elif i["no"] == 1:
                d["bst_fmp_1"] = 0 if int(i.get("ansval") or 0) else 1
            elif i["no"] == 2:
                v = int(i.get("ansval") or 0) + 1
                if v == 3:
                    d["bst_fmp_2"] = 2
                elif v == 2:
                    d["bst_fmp_2"] = 3
                else:
                    d["bst_fmp_2"] = 1
            elif i["no"] == 3:
                v = int(i.get("ansval") or 0) + 1
                if v == 3:
                    d["bst_fmp_3"] = 2
                elif v == 2:
                    d["bst_fmp_3"] = 3
                else:
                    d["bst_fmp_3"] = 1
            elif i["no"] == 4:
                v = int(i.get("ansval") or 0) + 1
                if v == 3:
                    d["bst_fmp_4"] = 2
                elif v == 2:
                    d["bst_fmp_4"] = 3
                else:
                    d["bst_fmp_4"] = 1
        return True

    @staticmethod
    def assign_priorities(d, survey):
        d["dc_pri_1"] = 2
        d["dc_pri_2"] = 1
        d["dc_pri_3"] = 1
        d["dc_pri_4"] = 2
        for i in survey["answers"]:
            if i["no"] == 0:
                d["dc_pri_1"] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 1:
                d["dc_pri_2"] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 2:
                d["dc_pri_3"] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 3:
                d["dc_pri_4"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def assign_screentimebadge(d, survey):
        name = "bst_quiz_14_"
        for x in xrange(4):
            d[name + str(x+1)] = 0
        for x in xrange(17):
            if x == 13:
                continue
            d["bst_quiz_" + str(x+1)] = 1

        for i in survey["answers"]:
            if i["no"] == 13:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "bst_quiz_14_"
                for x in xrange(4):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif 0 <= i["no"] <= 16:
                d["bst_quiz_" + str(i["no"]+1)] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def transform_gameaddict(d):
        newd = {}
        for i in xrange(11):
            name = "bst_ga_" + str(i+1)
            val = d.get(name, 0)
            if val == 2:
                val = 0.5
            elif val == 3:
                val = 0
            newd[name] = val
        return newd

    @staticmethod
    def transform_mediarules(d):
        newd = {
            "bst_fmp_0": d.get("bst_fmp_0", 0),
            "bst_fmp_1": d.get("bst_fmp_1", 0)
        }
        for i in xrange(3):
            name = "bst_fmp_" + str(i+2)
            val = d.get(name, 3)
            if val == 3:
                val = 1
            elif val == 1:
                val = 3
            newd[name] = val
        return newd

    @staticmethod
    def transform_priorities(d):
        return {
            "dc_pri_1": 1 if d.get("dc_pri_1", 0) == 1 else 0,
            "dc_pri_2": 1 if d.get("dc_pri_2", 0) == 3 else 0,
            "dc_pri_3": 1 if d.get("dc_pri_3", 0) == 2 else 0,
            "dc_pri_4": 1 if d.get("dc_pri_4", 0) == 1 else 0
        }

    @staticmethod
    def transform_screentimebadge(d):
        return {
            "bst_quiz_1": 1 if d.get("bst_quiz_1", 0) == 1 else 0,
            "bst_quiz_2": 1 if d.get("bst_quiz_2", 0) == 3 else 0,
            "bst_quiz_3": 1 if d.get("bst_quiz_3", 0) == 5 else 0,
            "bst_quiz_4": 1 if d.get("bst_quiz_4", 0) == 3 else 0,
            "bst_quiz_5": 1 if d.get("bst_quiz_5", 0) == 1 else 0,
            "bst_quiz_6": 1 if d.get("bst_quiz_6", 0) == 4 else 0,
            "bst_quiz_7": 1 if d.get("bst_quiz_7", 0) == 5 else 0,
            "bst_quiz_8": 1 if d.get("bst_quiz_8", 0) == 2 else 0,
            "bst_quiz_9": 1 if d.get("bst_quiz_9", 0) == 4 else 0,
            "bst_quiz_10": 1 if d.get("bst_quiz_10", 0) == 4 else 0,
            "bst_quiz_11": 1 if d.get("bst_quiz_11", 0) == 2 else 0,
            "bst_quiz_12": 1 if d.get("bst_quiz_12", 0) == 2 else 0,
            "bst_quiz_13": 1 if d.get("bst_quiz_13", 0) == 2 else 0,
            "bst_quiz_14": 1 if d.get("bst_quiz_14_1", 0) == 1 and d.get("bst_quiz_14_3", 0) == 1 and
                                d.get("bst_quiz_14_2", 0)+d.get("bst_quiz_14_4", 0) == 0 else 0,
            "bst_quiz_15": 1 if d.get("bst_quiz_15", 0) == 2 else 0,
            "bst_quiz_16": 1 if d.get("bst_quiz_16", 0) == 3 else 0,
            "bst_quiz_17": 1 if d.get("bst_quiz_17", 0) == 2 else 0
        }


class PrivacyDQResult(crudmgo.RootDocument):
    __collection__ = "privacydqresults"

    structure = {
        "userid": ObjectId,
        "created": {
            "by": basestring,
            "on": datetime.datetime,
            "username": basestring
        },
        "meta": {}
    }
    indexes = [
        {"fields": "created.by",
         "check": False}
    ]
    default_values = {"created.by": lambda: current_user.id, "created.on": crudmgo.localtime,
                      "created.username": lambda: current_user.get_username(), "meta": {}}

    def get_dqresult(self, user, cacheonly=False):
        if not user:
            return None

        r = self.find_one({"userid": user.id})
        if not r:
            r = self()
            r["userid"] = user.id
            if r.calc_dqscore():
                r.save()
            else:
                r = None
        elif not cacheonly:
            r.calc_dqscore()
            r.save()
        return r

    def has_dqresult(self, user):
        if not user:
            return None

        r = self.find_one({"userid": user.id})
        return r is not None

    def calc_dqscore(self, userid=None, user=None):
        if not ObjectId.is_valid(userid):
            userid = None

        if userid:
            userid = ObjectId(userid)
        elif self.get("userid") and isinstance(self["userid"], ObjectId):
            userid = self["userid"]
        else:
            return False

        cfg = {}

        d = self
        r = None
        db = self.collection.database
        model = db["SurveyDQAnswer"]

        if user is None:
            user = db["IZHero"].find_one({"_id": userid})
            if not user:
                return False

        progress = user.get("dq_progress", {})

        if current_app.config.get('R_RCMD'):
            cfg['RCMD'] = current_app.config['R_RCMD']

        try:
            survey = db["SurveyDQ"].find_one({"name": "privacybadge.v1"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey and "privacybadge" not in progress:
                # self.get_privacybadge_na(d)
                return False
            else:
                self.assign_privacybadge(d, survey)

            survey = db["SurveyDQ"].find_one({"name": "pinfo.v1"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "pinfo" not in progress:
                # self.get_pinfo_na(d)
                # self.get_pinfo_messenger_na(d)
                return False
            else:
                self.assign_pinfo(d, survey)

            survey = model.find_one({"surveyname": "pinfo-messenger",
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if "pinfo" in progress:
                if not survey:
                    survey = {"answers": []}
                if not survey or not self.assign_pinfo_messenger(d, survey):
                    return False

            survey = db["SurveyDQ"].find_one({"name": "spinfo"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "spinfo" not in progress:
                # self.get_spinfo_na(d)
                return False
            else:
                self.assign_spinfo(d, survey)

            survey = db["SurveyDQ"].find_one({"name": "snsprivacy.v2"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "snsprivacy" not in progress:
                # self.get_snsprivacy_na(d)
                return False
            else:
                self.assign_snsprivacy(d, survey)

            survey = db["SurveyDQ"].find_one({"name": "protectinfo"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "protectinfo" not in progress:
                # self.get_protectinfo_na(d)
                return False
            else:
                self.assign_protectinfo(d, survey)

            r = R(**cfg)

            for k, v in d.iteritems():
                if isinstance(v, (int, float)):
                    r.assign(k, v)
            for k, v in self.transform_privacybadge(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_protectinfo(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_pinfo_messenger(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_spinfo(d).iteritems():
                r.assign(k, v)

            r(util.r_sc_func)
            r(privacy.r_algo)

            self["pri_pi_mgmt_score"] = r.get("pri_pi_mgmt_score")

            p = r.prog
            r = None
            p.terminate()
        except Exception as e:
            if r and hasattr(r, "prog") and hasattr(r.prog, "terminate"):
                r.prog.terminate()
            return False

        return True

    def get_dqscores(self):
        return {
            "pri_pi_mgmt_score": self.get("pri_pi_mgmt_score", 0)
        }

    def transform_vars(self):
        d = {k: v for k, v in self.iteritems()}
        d.update(self.transform_pinfo_messenger(d))
        d.update(self.transform_privacybadge(d))
        d.update(self.transform_protectinfo(d))
        d.update(self.transform_spinfo(d))
        return d

    @staticmethod
    def get_privacybadge_na(d):
        d["pri_quiz_2"] = "NA"
        name = "pri_quiz_3_"
        for x in xrange(4):
            d[name + str(x+1)] = "NA"
        name = "pri_quiz_4_"
        for x in xrange(3):
            d[name + str(x+1)] = "NA"
        name = "pri_quiz_13_"
        for x in xrange(5):
            d[name + str(x+1)] = "NA"
        d["pri_quiz_1"] = "NA"
        d["pri_quiz_5"] = "NA"
        d["pri_quiz_6"] = "NA"
        d["pri_quiz_8"] = "NA"
        d["pri_quiz_9"] = "NA"
        d["pri_quiz_10"] = "NA"
        d["pri_quiz_11"] = "NA"
        d["pri_quiz_12"] = "NA"
        d["pri_quiz_13"] = "NA"
        d["pri_quiz_14"] = "NA"
        d["pri_quiz_15"] = "NA"
        d["pri_quiz_16"] = "NA"

    @staticmethod
    def assign_privacybadge(d, survey):
        d["pri_quiz_2"] = 0
        name = "pri_quiz_3_"
        for x in xrange(4):
            d[name + str(x+1)] = 0
        name = "pri_quiz_4_"
        for x in xrange(3):
            d[name + str(x+1)] = 0
        name = "pri_quiz_13_"
        for x in xrange(5):
            d[name + str(x+1)] = 0
        d["pri_quiz_1"] = 1
        d["pri_quiz_5"] = 1
        d["pri_quiz_6"] = 1
        d["pri_quiz_8"] = 1
        d["pri_quiz_9"] = 1
        d["pri_quiz_10"] = 1
        d["pri_quiz_11"] = 3
        d["pri_quiz_12"] = 1
        d["pri_quiz_13"] = 1
        d["pri_quiz_14"] = 1
        d["pri_quiz_15"] = 1
        d["pri_quiz_16"] = 1

        for i in survey["answers"]:
            if i["no"] == 1:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                d["pri_quiz_2"] = 0
                if l == [3]:
                    d["pri_quiz_2"] = 4
                elif len(l) > 0:
                    d["pri_quiz_2"] = l[1]+1 if l[0] == 3 else l[0]+1
            elif i["no"] == 2:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "pri_quiz_3_"
                for x in xrange(4):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 3:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "pri_quiz_4_"
                for x in xrange(3):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 9:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                d["pri_quiz_11"] = 0
                if l == [2]:
                    d["pri_quiz_11"] = 3
                elif len(l) > 0:
                    d["pri_quiz_11"] = l[1]+1 if l[0] == 2 else l[0]+1
            elif i["no"] == 11:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "pri_quiz_13_"
                for x in xrange(5):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif 0 <= i["no"] <= 14:
                d["pri_quiz_" + str(i["no"]+(2 if i["no"] >= 6 else 1))] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_pinfo_na(d):
        for x in xrange(13):
            d['pri_pi_beh_' + str(x+1)] = "NA"

    @staticmethod
    def assign_pinfo(d, survey):
        for x in xrange(13):
            d['pri_pi_beh_' + str(x+1)] = 0

        for i in survey["answers"]:
            if i["no"] == 0:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                q = [(1 if x in l else 0) for x in xrange(13)]
                d['pri_pi_beh_1'] = q[0]
                d['pri_pi_beh_2'] = q[1]
                d['pri_pi_beh_3'] = q[2]
                d['pri_pi_beh_4'] = q[3]
                d['pri_pi_beh_5'] = q[4]
                d['pri_pi_beh_6'] = q[5]
                d['pri_pi_beh_7'] = q[6]
                d['pri_pi_beh_8'] = q[7]
                d['pri_pi_beh_9'] = q[8]
                d['pri_pi_beh_10'] = q[9]
                d['pri_pi_beh_11'] = q[10]
                d['pri_pi_beh_12'] = q[11]
                d['pri_pi_beh_13'] = q[12]
        return True

    @staticmethod
    def get_pinfo_messenger_na(d):
        for x in xrange(8):
            d["pri_other_pwd_a_" + str(x+1)] = "NA"
        d["sec_pwd_share_d"] = "NA"
        d["sec_pwd_share_e"] = "NA"
        d["sec_pwd_share_f"] = "NA"
        for x in xrange(8):
            d["pri_other_pwd_a_" + str(x+1)] = "NA"

    @staticmethod
    def assign_pinfo_messenger(d, survey):
        for x in xrange(8):
            d["pri_other_pwd_a_" + str(x+1)] = 0
        d["sec_pwd_share_d"] = 0
        d["sec_pwd_share_e"] = 0
        d["sec_pwd_share_f"] = 0
        for x in xrange(8):
            d["pri_other_pwd_a_" + str(x+1)] = 0

        for i in survey["answers"]:
            if i["qns"] == "havepwd":
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "pri_other_pwd_a_"
                for x in xrange(8):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["qns"] == "login":
                d["sec_pwd_share_d"] = 1 if int(i.get("ansval") or 0) == 0 else 0
            elif i["qns"] == "loginreason":
                d["sec_pwd_share_e"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "upset":
                v = int(i.get("ansval") or 0)
                if v == 0:
                    d["sec_pwd_share_f"] = 1
                elif v == 1:
                    d["sec_pwd_share_f"] = 0
                else:
                    d["sec_pwd_share_f"] = 2
        return True

    @staticmethod
    def get_spinfo_na(d):
        d["pri_freeapp"] = "NA"
        d["pri_pi_att_2"] = "NA"
        d["pri_pi_att_3"] = "NA"

    @staticmethod
    def assign_spinfo(d, survey):
        d["pri_freeapp"] = 4
        d["pri_pi_att_2"] = 1
        d["pri_pi_att_3"] = 1

        for i in survey["answers"]:
            if 0 <= i["no"] <= 1:
                d["pri_pi_att_" + str(i["no"]+2)] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 2:
                d["pri_freeapp"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_snsprivacy_na(d):
        for x in xrange(6):
            d["pri_pi_skill_" + str(x+1)] = "NA"

    @staticmethod
    def assign_snsprivacy(d, survey):
        for x in xrange(6):
            d["pri_pi_skill_" + str(x+1)] = 0

        for i in survey["answers"]:
            if 4 <= i["no"] <= 9:
                d["pri_pi_skill_" + str(i["no"]-3)] = int(i.get("ansval") or 0) + 1
                if d["pri_pi_skill_" + str(i["no"]-3)] == 6:
                    d["pri_pi_skill_" + str(i["no"]-3)] = 0
        return True

    @staticmethod
    def get_protectinfo_na(d):
        d["pri_other_post_1"] = "NA"
        d["pri_other_post_2"] = "NA"

    @staticmethod
    def assign_protectinfo(d, survey):
        d["pri_other_post_1"] = 1
        d["pri_other_post_2"] = 1

        for i in survey["answers"]:
            if i["no"] == 0:
                d["pri_other_post_1"] = 1 if int(i.get("ansval") or 0) == 0 else 0
            elif i["no"] == 1:
                d["pri_other_post_2"] = int(i.get("ansval") or 0)+1
        return True

    @staticmethod
    def transform_privacybadge(d):
        if d.get("pri_quiz_1") == "NA":
            return {"pri_quiz_" + str(x + 1): "NA" for x in xrange(16) if x != 6}

        return {
            "pri_quiz_1": 1 if d.get("pri_quiz_1", 0) == 1 else 0,
            "pri_quiz_2": 1 if d.get("pri_quiz_2", 0) == 4 else 0,
            "pri_quiz_3": 0 if d.get("pri_quiz_3_1", 0)+d.get("pri_quiz_3_3", 0) > 0
                          else (d.get("pri_quiz_3_2", 0)+d.get("pri_quiz_3_4", 0))/2.0,
            "pri_quiz_4": 0 if d.get("pri_quiz_4_1", 0) > 0
                          else (d.get("pri_quiz_4_2", 0)+d.get("pri_quiz_4_3", 0))/2.0,
            "pri_quiz_5": 1 if d.get("pri_quiz_5", 0) == 1 else 0,
            "pri_quiz_6": 1 if d.get("pri_quiz_6", 0) == 3 else 0,
            # "pri_quiz_7": 1 if d.get("pri_quiz_7", 0) == 1 else 0,
            "pri_quiz_8": 1 if d.get("pri_quiz_8", 0) == 4 else 0,
            "pri_quiz_9": 1 if d.get("pri_quiz_9", 0) == 2 else 0,
            "pri_quiz_10": 1 if d.get("pri_quiz_10", 0) == 4 else 0,
            "pri_quiz_11": 1 if d.get("pri_quiz_11", 0) == 3 else 0,
            "pri_quiz_12": 1 if d.get("pri_quiz_12", 0) == 2 else 0,
            "pri_quiz_13": 0 if d.get("pri_quiz_13_2", 0)+d.get("pri_quiz_13_5", 0) > 0
                          else (d.get("pri_quiz_13_1", 0)+d.get("pri_quiz_13_3", 0)+d.get("pri_quiz_13_4", 0))/3.0,
            "pri_quiz_14": 1 if d.get("pri_quiz_14", 0) == 2 else 0,
            "pri_quiz_15": 1 if d.get("pri_quiz_15", 0) == 4 else 0,
            "pri_quiz_16": 1 if d.get("pri_quiz_16", 0) == 3 else 0
        }

    @staticmethod
    def transform_spinfo(d):
        if d.get("pri_pi_att_2") == "NA":
            return {"pri_pi_att_2": "NA",
                    "pri_pi_att_3": "NA"}

        return {
            "pri_pi_att_2": 6 - d.get("pri_pi_att_2", 1),
            "pri_pi_att_3": d.get("pri_pi_att_3", 1)
        }

    @staticmethod
    def transform_pinfo_messenger(d):
        if d.get("pri_other_pwd_a_1") == "NA":
            return {
                "pri_other_pwd_a_1": "NA",
                "pri_other_pwd_a_2": "NA",
                "pri_other_pwd_a_3": "NA",
                "pri_other_pwd_a_4": "NA",
                "pri_other_pwd_a_5": "NA",
                "pri_other_pwd_a_6": "NA",
                "pri_other_pwd_a_7": "NA",
                "pri_other_pwd_a_8": "NA",
                "sec_pwd_share_d": "NA",
                "sec_pwd_share_e": "NA",
                "sec_pwd_share_f": "NA"
            }

        newd = {
            "pri_other_pwd_a_1": (0 - d.get("pri_other_pwd_a_1", 0)),
            "pri_other_pwd_a_2": (0 - d.get("pri_other_pwd_a_2", 0)),
            "pri_other_pwd_a_3": (0 - d.get("pri_other_pwd_a_3", 0)) * 2,
            "pri_other_pwd_a_4": (0 - d.get("pri_other_pwd_a_4", 0)) * 2,
            "pri_other_pwd_a_5": (0 - d.get("pri_other_pwd_a_5", 0)) * 3,
            "pri_other_pwd_a_6": (0 - d.get("pri_other_pwd_a_6", 0)) * 3,
            "pri_other_pwd_a_7": (0 - d.get("pri_other_pwd_a_7", 0)) * 4,
            "pri_other_pwd_a_8": d.get("pri_other_pwd_a_8", 0) * 10,
            "sec_pwd_share_d": d.get("sec_pwd_share_d", 0),
        }
        e = d.get("sec_pwd_share_e", 1)
        if e == 1 or e == 2 or e == 3:
            newd["sec_pwd_share_e"] = 3
        elif e == 4:
            newd["sec_pwd_share_e"] = 2
        else:
            newd["sec_pwd_share_e"] = 1

        f = d.get("sec_pwd_share_f", 0)
        if f == 1:
            newd["sec_pwd_share_f"] = 1
        elif f == 2:
            newd["sec_pwd_share_f"] = 0.5
        else:
            newd["sec_pwd_share_f"] = 0.2
        return newd

    @staticmethod
    def transform_protectinfo(d):
        if d.get("pri_other_post_1") == "NA":
            return {
                "pri_other_post_1": "NA",
                "pri_other_post_2": "NA"
            }

        newd = {
            "pri_other_post_1": 2 - d.get("pri_other_post_1", 0),
            "pri_other_post_2": d.get("pri_other_post_2", 1)
        }
        v = d.get("pri_other_post_2", 1)
        if v == 3:
            newd["pri_other_post_2"] = 3
        elif v == 1:
            newd["pri_other_post_2"] = 2
        else:
            newd["pri_other_post_2"] = 1
        return newd


class CyberbullyingDQResult(crudmgo.RootDocument):
    __collection__ = "cyberbullyingdqresults"

    structure = {
        "userid": ObjectId,
        "created": {
            "by": basestring,
            "on": datetime.datetime,
            "username": basestring
        },
        "meta": {}
    }
    indexes = [
        {"fields": "created.by",
         "check": False}
    ]
    default_values = {"created.by": lambda: current_user.id, "created.on": crudmgo.localtime,
                      "created.username": lambda: current_user.get_username(), "meta": {}}

    def get_dqresult(self, user, cacheonly=False):
        if not user:
            return None

        r = self.find_one({"userid": user.id})
        if not r:
            r = self()
            r["userid"] = user.id
            if r.calc_dqscore():
                r.save()
            else:
                r = None
        elif not cacheonly:
            r.calc_dqscore()
            r.save()
        return r

    def has_dqresult(self, user):
        if not user:
            return None

        r = self.find_one({"userid": user.id})
        return r is not None

    def calc_dqscore(self, userid=None, user=None):
        if not ObjectId.is_valid(userid):
            userid = None

        if userid:
            userid = ObjectId(userid)
        elif self.get("userid") and isinstance(self["userid"], ObjectId):
            userid = self["userid"]
        else:
            return False

        cfg = {}

        d = self
        r = None
        db = self.collection.database
        model = db["SurveyDQAnswer"]

        if user is None:
            user = db["IZHero"].find_one({"_id": userid})
            if not user:
                return False

        progress = user.get("dq_progress", {})

        if current_app.config.get('R_RCMD'):
            cfg['RCMD'] = current_app.config['R_RCMD']

        try:
            survey = db["SurveyDQ"].find_one({"name": "involvebully"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "involvebully" not in progress:
                # self.get_involvebully_na(d)
                return False
            else:
                self.assign_involvebully(d, survey)

            survey = db["SurveyDQ"].find_one({"name": "detectbully"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            msurvey = model.find_one({"surveyname": "detectbully-messenger",
                                      "created.by": userid},
                                     sort=[("_id", pymongo.ASCENDING)])
            if "detectbully" in progress:
                if not msurvey:
                    msurvey = {"answers": []}
                if not survey or not msurvey or not self.assign_detectbully(d, survey, msurvey):
                    return False
            else:
                # self.get_detectbully_na(d)
                return False

            survey = db["SurveyDQ"].find_one({"name": "dealbully.v2"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "dealbully" not in progress:
                # self.get_dealbully_na(d)
                return False
            else:
                self.assign_dealbully(d, survey)

            survey = model.find_one({"surveyname": "speakup-messenger",
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if "speakup" in progress:
                if not survey:
                    survey = {"answers": []}
                if not survey or not self.assign_speakup_messenger(d, survey):
                    return False
            else:
                # self.get_speakup_na(d)
                return False

            survey = db["SurveyDQ"].find_one({"name": "snsprivacy.v2"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "snsprivacy" not in progress:
                # self.get_snsprivacy_na(d)
                return False
            else:
                self.assign_snsprivacy(d, survey)

            survey = db["SurveyDQ"].find_one({"name": "cyberbullyingbadge"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey and "cyberbullyingbadge" not in progress:
                # self.get_cyberbullyingbadge_na(d)
                return False
            else:
                self.assign_cyberbullyingbadge(d, survey)

            r = R(**cfg)

            for k, v in d.iteritems():
                if isinstance(v, (int, float)):
                    r.assign(k, v)
            for k, v in self.transform_cyberbullybadge(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_detectbully(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_speakup_messenger(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_snsprivacy(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_involvebully(d).iteritems():
                r.assign(k, v)

            r(util.r_sc_func)
            r(cyberbullying.r_algo)

            self["cb_score"] = r.get("cb_score")

            p = r.prog
            r = None
            p.terminate()
        except Exception as e:
            if r and hasattr(r, "prog") and hasattr(r.prog, "terminate"):
                r.prog.terminate()
            return False

        return True

    def get_dqscores(self):
        return {
            "cb_score": self.get("cb_score", 0)
        }

    def transform_vars(self):
        d = {k: v for k, v in self.iteritems()}
        d.update(self.transform_cyberbullybadge(d))
        d.update(self.transform_detectbully(d))
        d.update(self.transform_involvebully(d))
        d.update(self.transform_snsprivacy(d))
        d.update(self.transform_speakup_messenger(d))
        return d

    @staticmethod
    def get_involvebully_na(d):
        for x in xrange(9):
            d["cb_cbbeh_" + str(x+1)] = "NA"

    @staticmethod
    def assign_involvebully(d, survey):
        for x in xrange(9):
            d["cb_cbbeh_" + str(x+1)] = 1

        for i in survey["answers"]:
            if 0 <= i["no"] <= 8:
                d["cb_cbbeh_" + str(i["no"]+1)] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_detectbully_na(d):
        d["cb_cbatt_1"] = "NA"
        d["cb_cbatt_2"] = "NA"
        d["cb_cbatt_3"] = "NA"
        d["cb_cbatt_4"] = "NA"
        d["cb_cbatt_5"] = "NA"

    @staticmethod
    def assign_detectbully(d, survey, msurvey):
        d["cb_cbatt_1"] = 1
        d["cb_cbatt_2"] = 1
        d["cb_cbatt_3"] = 1
        d["cb_cbatt_4"] = 1
        d["cb_cbatt_5"] = 1

        for i in msurvey["answers"]:
            if i["qns"] == "sendmean":
                d["cb_cbatt_1"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "okmean":
                d["cb_cbatt_4"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "feelbetter":
                d["cb_cbatt_5"] = int(i.get("ansval") or 0) + 1
        for i in survey["answers"]:
            if i["no"] == 0:
                d["cb_cbatt_2"] = int(i["ansval"] or 0) + 1
            if i["no"] == 1:
                d["cb_cbatt_3"] = int(i["ansval"] or 0) + 1
        return True

    @staticmethod
    def get_dealbully_na(d):
        name = "cb_cbmgmt_"
        for x in xrange(10):
            d[name + str(x+1)] = "NA"

    @staticmethod
    def assign_dealbully(d, survey):
        name = "cb_cbmgmt_"
        for x in xrange(10):
            d[name + str(x+1)] = 0

        for i in survey["answers"]:
            if i["no"] == 9:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "cb_cbmgmt_"
                for x in xrange(10):
                    d[name + str(x+1)] = 1 if x in l else 0
        return True

    @staticmethod
    def get_speakup_na(d):
        d["cb_speakup_1"] = "NA"

    @staticmethod
    def assign_speakup_messenger(d, survey):
        d["cb_speakup_1"] = 1

        for i in survey["answers"]:
            if i["qns"] == "seemean":
                d["cb_speakup_1"] = int(i.get("ansval") or 0) + 1
                break
        return True

    @staticmethod
    def get_snsprivacy_na(d):
        d["cb_deal_34"] = "NA"

    @staticmethod
    def assign_snsprivacy(d, survey):
        d["cb_deal_34"] = 0

        for i in survey["answers"]:
            if i["no"] == 13:
                d["cb_deal_34"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_cyberbullyingbadge_na(d):
        for x in xrange(5):
            d["cb_quiz_4_" + str(x+1)] = "NA"
        name = "cb_quiz_12_"
        for x in xrange(4):
            d[name + str(x+1)] = "NA"
        name = "cb_quiz_17_"
        for x in xrange(5):
            d[name + str(x+1)] = "NA"
        d["cb_quiz_1"] = "NA"
        d["cb_quiz_2"] = "NA"
        d["cb_quiz_3"] = "NA"
        d["cb_quiz_5"] = "NA"
        d["cb_quiz_6"] = "NA"
        d["cb_quiz_7"] = "NA"
        d["cb_quiz_8"] = "NA"
        d["cb_quiz_9"] = "NA"
        d["cb_quiz_10"] = "NA"
        d["cb_quiz_11"] = "NA"
        d["cb_quiz_13"] = "NA"
        d["cb_quiz_14"] = "NA"
        d["cb_quiz_15"] = "NA"
        d["cb_quiz_16"] = "NA"

    @staticmethod
    def assign_cyberbullyingbadge(d, survey):
        for x in xrange(5):
            d["cb_quiz_4_" + str(x+1)] = 1
        name = "cb_quiz_12_"
        for x in xrange(4):
            d[name + str(x+1)] = 0
        name = "cb_quiz_17_"
        for x in xrange(5):
            d[name + str(x+1)] = 0
        d["cb_quiz_1"] = 1
        d["cb_quiz_2"] = 1
        d["cb_quiz_3"] = 1
        d["cb_quiz_5"] = 1
        d["cb_quiz_6"] = 1
        d["cb_quiz_7"] = 1
        d["cb_quiz_8"] = 1
        d["cb_quiz_9"] = 1
        d["cb_quiz_10"] = 1
        d["cb_quiz_11"] = 1
        d["cb_quiz_13"] = 1
        d["cb_quiz_14"] = 1
        d["cb_quiz_15"] = 1
        d["cb_quiz_16"] = 1

        for i in survey["answers"]:
            if 3 <= i["no"] <= 7:
                d["cb_quiz_4_" + str(i["no"]-2)] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 15:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "cb_quiz_12_"
                for x in xrange(4):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 20:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "cb_quiz_17_"
                for x in xrange(5):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif 0 <= i["no"] <= 2:
                d["cb_quiz_" + str(i["no"]+1)] = int(i.get("ansval") or 0) + 1
            elif 8 <= i["no"] <= 14 or 16 <= i["no"] <= 19:
                d["cb_quiz_" + str(i["no"]-3)] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def transform_detectbully(d):
        if d.get("cb_cbatt_1") == "NA":
            return {("cb_cbatt_" + str(i + 1)): "NA" for i in xrange(5)}

        return {("cb_cbatt_"+str(i+1)): (6-d.get("cb_cbatt_"+str(i+1), 1)) for i in xrange(5)}

    @staticmethod
    def transform_speakup_messenger(d):
        if d.get("cb_speakup_1") == "NA":
            return {"cb_speakup_1": "NA"}

        newd = {"cb_speakup_1": 5}
        v = d.get("cb_speakup_1", 0)
        if v == 3:
            newd["cb_speakup_1"] = 1
        elif v == 2:
            newd["cb_speakup_1"] = 2
        elif v == 1 or v == 6:
            newd["cb_speakup_1"] = 3
        elif v == 5:
            newd["cb_speakup_1"] = 4
        return newd

    @staticmethod
    def transform_snsprivacy(d):
        if d.get("cb_deal_34") == "NA":
            return {"cb_deal_34": "NA"}

        return {"cb_deal_34": 1 if d.get("cb_deal_34", 0) == 4 else 0}

    @staticmethod
    def transform_cyberbullybadge(d):
        if d.get("cb_quiz_1") == "NA":
            return {("cb_quiz_" + str(i + 1)): "NA" for i in xrange(17)}

        return {
            "cb_quiz_1": 1 if d.get("cb_quiz_1", 0) == 4 else 0,
            "cb_quiz_2": 1 if d.get("cb_quiz_2", 0) == 3 else 0,
            "cb_quiz_3": 1 if d.get("cb_quiz_3", 0) == 4 else 0,
            "cb_quiz_4": (int(d.get("cb_quiz_4_1", 0) == 1) + int(d.get("cb_quiz_4_2", 0) == 2) +
                          int(d.get("cb_quiz_4_3", 0) == 2) + int(d.get("cb_quiz_4_4", 0) == 1) +
                          int(d.get("cb_quiz_4_5", 0) == 3))/5.0,
            "cb_quiz_5": 1 if d.get("cb_quiz_5", 0) == 2 else 0,
            "cb_quiz_6": 1 if d.get("cb_quiz_6", 0) == 1 else 0,
            "cb_quiz_7": 1 if d.get("cb_quiz_7", 0) == 3 else 0,
            "cb_quiz_8": 1 if d.get("cb_quiz_8", 0) == 2 else 0,
            "cb_quiz_9": 1 if d.get("cb_quiz_9", 0) == 2 else 0,
            "cb_quiz_10": 1 if d.get("cb_quiz_10", 0) == 3 else 0,
            "cb_quiz_11": 1 if d.get("cb_quiz_11", 0) == 3 else 0,
            "cb_quiz_12": 0 if d.get("cb_quiz_12_2", 0)+d.get("cb_quiz_12_3", 0) > 0
                          else (d.get("cb_quiz_12_1", 0)+d.get("cb_quiz_12_4", 0))/2.0,
            "cb_quiz_13": 1 if d.get("cb_quiz_13", 0) == 4 else 0,
            "cb_quiz_14": 1 if d.get("cb_quiz_14", 0) == 2 else 0,
            "cb_quiz_15": 1 if d.get("cb_quiz_15", 0) == 3 else 0,
            "cb_quiz_16": 1 if d.get("cb_quiz_16", 0) == 3 else 0,
            "cb_quiz_17": 0 if d.get("cb_quiz_17_2", 0)+d.get("cb_quiz_17_3", 0) > 0
                          else (d.get("cb_quiz_17_1", 0)+d.get("cb_quiz_17_4", 0)+d.get("cb_quiz_17_5", 0))/3.0,
        }

    @staticmethod
    def transform_involvebully(d):
        if d.get("cb_cbbeh_1") == "NA":
            return {("cb_cbbeh_" + str(i + 1)): "NA" for i in xrange(9)}

        newd = {}
        for i in xrange(9):
            v = d.get("cb_cbbeh_" + str(i+1), 1)
            y = 0
            if v == 2:
                y = 1.5
            elif v == 3:
                y = 5
            elif v == 4:
                y = 50
            elif v == 5:
                y = 100
            newd["cb_cbbeh_" + str(i+1)] = y
        return newd


class DigitalcitizensDQResult(crudmgo.RootDocument):
    __collection__ = "digitalcitizensdqresults"

    structure = {
        "userid": ObjectId,
        "created": {
            "by": basestring,
            "on": datetime.datetime,
            "username": basestring
        },
        "meta": {}
    }
    indexes = [
        {"fields": "created.by",
         "check": False}
    ]
    default_values = {"created.by": lambda: current_user.id, "created.on": crudmgo.localtime,
                      "created.username": lambda: current_user.get_username(), "meta": {}}

    def get_dqresult(self, user, cacheonly=False):
        if not user:
            return None

        r = self.find_one({"userid": user.id})
        if not r:
            r = self()
            r["userid"] = user.id
            if r.calc_dqscore():
                r.save()
            else:
                r = None
        elif not cacheonly:
            r.calc_dqscore()
            r.save()
        return r

    def has_dqresult(self, user):
        if not user:
            return None

        r = self.find_one({"userid": user.id})
        return r is not None

    def calc_dqscore(self, userid=None, user=None):
        if not ObjectId.is_valid(userid):
            userid = None

        if userid:
            userid = ObjectId(userid)
        elif self.get("userid") and isinstance(self["userid"], ObjectId):
            userid = self["userid"]
        else:
            return False

        cfg = {}

        d = self
        r = None
        db = self.collection.database
        model = db["SurveyDQAnswer"]

        if user is None:
            user = db["IZHero"].find_one({"_id": userid})
            if not user:
                return False

        progress = user.get("dq_progress", {})

        if current_app.config.get('R_RCMD'):
            cfg['RCMD'] = current_app.config['R_RCMD']

        try:
            survey = model.find_one({"surveyname": "messenger-messenger",
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey:
                survey = {"answers": []}
            if not survey or not self.assign_digiworld_messenger(d, survey):
                return False

            survey = db["SurveyDQ"].find_one({"name": "digiworld"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or not self.assign_digiworld(d, survey):
                return False

            survey = db["SurveyDQ"].find_one({"name": "snsprivacy.v2"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "snsprivacy" not in progress:
                # self.get_snsprivacy_na(d)
                return False
            else:
                self.assign_snsprivacy(d, survey)

            survey = model.find_one({"surveyname": "persona-messenger",
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if "persona" in progress:
                if not survey:
                    survey = {"answers": []}
                if not survey or not self.assign_persona(d, survey):
                    return False
            else:
                # self.get_persona_na(d)
                return False

            survey = model.find_one({"surveyname": "strength-messenger",
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if "strength" in progress:
                if not survey:
                    survey = {"answers": []}
                if not survey or not self.assign_strength(d, survey):
                    return False
            else:
                # self.get_strength_na(d)
                return False

            survey = db["SurveyDQ"].find_one({"name": "onoffline.v1"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "onoffline" not in progress:
                # self.get_onoffline_na(d)
                return False
            else:
                self.assign_onoffline(d, survey)

            survey = db["SurveyDQ"].find_one({"name": "globalcitizens"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "globalcitizens" not in progress:
                # self.get_globalcitizens_na(d)
                return False
            else:
                self.assign_globalcitizens(d, survey)

            # survey = db["SurveyDQ"].find_one({"name": "pretest-full.v2"})
            # survey = model.find_one({"surveyid": survey["_id"],
            #                          "created.by": userid},
            #                         sort=[("_id", pymongo.ASCENDING)])
            # if not survey or not self.assign_pretest(d, survey):
            #    return False

            survey = db["SurveyDQ"].find_one({"name": "digitalcitizensbadge"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey and "digitalcitizensbadge" not in progress:
                # self.get_digitalcitizensbadge_na(d)
                return False
            else:
                self.assign_digitalcitizensbadge(d, survey)

            r = R(**cfg)

            for k, v in d.iteritems():
                if isinstance(v, (int, float)):
                    r.assign(k, v)
            for k, v in self.transform_digiworld(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_onoffline(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_persona(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_strength(d).iteritems():
                r.assign(k, v)
            # for k, v in self.transform_pretest(d).iteritems():
                # r.assign(k, v)
            for k, v in self.transform_digitalcitizensbadge(d).iteritems():
                r.assign(k, v)

            r(digitalcitizens.r_algo)

            self["dc_identity_score"] = r.get("dc_identity_score")

            p = r.prog
            r = None
            p.terminate()
        except Exception as e:
            if r and hasattr(r, "prog") and hasattr(r.prog, "terminate"):
                r.prog.terminate()
            return False

        return True

    def get_dqscores(self):
        return {
            "dc_identity_score": self.get("dc_identity_score", 0)
        }

    def transform_vars(self):
        d = {k: v for k, v in self.iteritems()}
        d.update(self.transform_digitalcitizensbadge(d))
        # d.update(self.transform_pretest(d))
        d.update(self.transform_digiworld(d))
        d.update(self.transform_onoffline(d))
        d.update(self.transform_persona(d))
        d.update(self.transform_strength(d))
        return d

    @staticmethod
    def get_digiworld_messenger_na(d):
        d["dc_dt_acc_1"] = "NA"
        d["dc_dt_acc_2"] = "NA"

    @staticmethod
    def assign_digiworld_messenger(d, survey):
        d["dc_dt_acc_1"] = 1
        d["dc_dt_acc_2"] = 1
        for i in survey["answers"]:
            if i["qns"] == "netaccess":
                d["dc_dt_acc_1"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "howcontact":
                d["dc_dt_acc_2"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_digiworld_na(d):
        d['dc_dt_du_1'] = "NA"
        d['dc_dt_du_2'] = "NA"
        d['dc_dt_du_3'] = "NA"
        d['dc_dt_du_4'] = "NA"
        d['dc_dt_du_5'] = "NA"
        d['dc_dt_du_6'] = "NA"
        d['dc_dt_du_7'] = "NA"
        d['dc_dt_du_8'] = "NA"
        d['dc_dt_du_9'] = "NA"

    @staticmethod
    def assign_digiworld(d, survey):
        d['dc_dt_du_1'] = 0
        d['dc_dt_du_2'] = 0
        d['dc_dt_du_3'] = 0
        d['dc_dt_du_4'] = 0
        d['dc_dt_du_5'] = 0
        d['dc_dt_du_6'] = 0
        d['dc_dt_du_7'] = 0
        d['dc_dt_du_8'] = 0
        d['dc_dt_du_9'] = 1
        for i in survey["answers"]:
            if i["no"] == 0:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                q = [(1 if x in l else 0) for x in xrange(9)]
                d['dc_dt_du_1'] = q[0]
                d['dc_dt_du_2'] = q[1]
                d['dc_dt_du_3'] = q[2]
                d['dc_dt_du_4'] = q[3]
                d['dc_dt_du_5'] = q[4]
                d['dc_dt_du_6'] = q[5]
                d['dc_dt_du_7'] = q[6]
                d['dc_dt_du_8'] = q[7]
                d['dc_dt_du_9'] = q[8]
        return True

    @staticmethod
    def get_snsprivacy_na(d):
        for x in xrange(13):
            d["dc_dt_snsuse_" + str(x+1)] = "NA"
        d["dc_dt_snsuse_14"] = "NA"
        d["dc_dt_snsfriend"] = "NA"
        d["dc_dt_snscheck"] = "NA"

    @staticmethod
    def assign_snsprivacy(d, survey):
        for x in xrange(13):
            d["dc_dt_snsuse_" + str(x+1)] = 0
        d["dc_dt_snsuse_14"] = 1
        d["dc_dt_snsfriend"] = 0
        d["dc_dt_snscheck"] = 0

        for i in survey["answers"]:
            if i["no"] == 0:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "dc_dt_snsuse_"
                for x in xrange(14):
                    d[name + str(x+1)] = 1 if x in l else 0
                d["dc_dt_snsuse_others"] = i.get("ans") or ""
                if d["dc_dt_snsuse_others"] and d["dc_dt_snsuse_13"] == 0:
                    d["dc_dt_snsuse_13"] = 1
            elif i["no"] == 2:
                d["dc_dt_snsfriend"] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 3:
                d["dc_dt_snscheck"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_persona_na(d):
        d["dt_cong_1"] = "NA"
        d["dt_cong_2"] = "NA"
        d["dc_oim_1"] = "NA"

    @staticmethod
    def assign_persona(d, survey):
        d["dt_cong_1"] = 1
        d["dt_cong_2"] = 1
        d["dc_oim_1"] = 1

        for i in survey["answers"]:
            if i["qns"] == "saydo":
                d["dt_cong_1"] = int(i.get("ansval") or 0) + 1
                if d["dt_cong_1"] == 5:
                    d["dt_cong_1"] = 0
            elif i["qns"] == "carefree":
                d["dt_cong_2"] = int(i.get("ansval") or 0) + 1
                if d["dt_cong_2"] == 5:
                    d["dt_cong_2"] = 0
            elif i["qns"] == "identity":
                d["dc_oim_1"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_onoffline_na(d):
        for x in xrange(5):
            d["dt_cong_" + str(x+3)] = "NA"

    @staticmethod
    def assign_onoffline(d, survey):
        for x in xrange(5):
            d["dt_cong_" + str(x+3)] = 1

        for i in survey["answers"]:
            if 0 <= i["no"] <= 4:
                d["dt_cong_" + str(i["no"]+3)] = int(i.get("ansval") or 0) + 1
                if d["dt_cong_" + str(i["no"]+3)] == 5:
                    d["dt_cong_" + str(i["no"] + 3)] = 0
        return True

    @staticmethod
    def get_strength_na(d):
        d["dc_selfefficacy_1"] = "NA"
        d["dc_selfefficacy_2"] = "NA"
        d["dc_selfefficacy_3"] = "NA"
        d["dc_selfefficacy_4"] = "NA"
        d["dc_selfefficacy_5"] = "NA"

    @staticmethod
    def assign_strength(d, survey):
        d["dc_selfefficacy_1"] = 1
        d["dc_selfefficacy_2"] = 1
        d["dc_selfefficacy_3"] = 1
        d["dc_selfefficacy_4"] = 1
        d["dc_selfefficacy_5"] = 1

        for i in survey["answers"]:
            if i["qns"] == "tryhard":
                d["dc_selfefficacy_1"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "oppose":
                d["dc_selfefficacy_2"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "solve":
                d["dc_selfefficacy_3"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "goal":
                d["dc_selfefficacy_4"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "solution":
                d["dc_selfefficacy_5"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_globalcitizens_na(d):
        d["dc_global_3"] = "NA"
        d["dc_global_2"] = "NA"
        d["dc_global_4"] = "NA"
        d["dc_global_5"] = "NA"

    @staticmethod
    def assign_globalcitizens(d, survey):
        d["dc_global_3"] = 1
        d["dc_global_2"] = 1
        d["dc_global_4"] = 1
        d["dc_global_5"] = 1

        for i in survey["answers"]:
            if i["no"] == 0:
                d["dc_global_3"] = int(i.get("ansval") or 0) + 1
            if i["no"] == 1:
                d["dc_global_2"] = int(i.get("ansval") or 0) + 1
            if i["no"] == 2:
                d["dc_global_4"] = int(i.get("ansval") or 0) + 1
            if i["no"] == 3:
                d["dc_global_5"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def assign_pretest(d, survey):
        for x in xrange(8):
            d["Q1_" + str(x+1)] = 0

        for i in survey["answers"]:
            if i["no"] == 0:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "Q1_"
                for x in xrange(8):
                    d[name + str(x+1)] = 1 if x in l else 0
                break
        return True

    @staticmethod
    def get_digitalcitizensbadge_na(d):
        name = "dc_dpi_quiz_2_"
        for x in xrange(4):
            d[name + str(x+1)] = "NA"
        name = "dc_oi_quiz_2_"
        for x in xrange(4):
            d[name + str(x+1)] = "NA"
        name = "dc_citizen_quiz_1_"
        for x in xrange(4):
            d[name + str(x+1)] = "NA"
        name = "dc_citizen_quiz_4_"
        for x in xrange(4):
            d[name + str(x+1)] = "NA"
        name = "dc_oi_quiz_5_"
        for x in xrange(5):
            d[name + str(x+1)] = "NA"
        name = "dc_oi_quiz_6_"
        for x in xrange(4):
            d[name + str(x+1)] = "NA"
        d["dc_dpi_quiz_1"] = "NA"
        d["dc_dpi_quiz_3"] = "NA"
        d["dc_dpi_quiz_4"] = "NA"
        d["dc_dpi_quiz_5"] = "NA"
        d["dc_dpi_quiz_6"] = "NA"
        d["dc_oi_quiz_1"] = "NA"
        d["dc_oi_quiz_3"] = "NA"
        d["dc_oi_quiz_4"] = "NA"
        d["dc_citizen_quiz_2"] = "NA"
        d["dc_citizen_quiz_3"] = "NA"
        d["dc_citizen_quiz_4"] = "NA"
        d["dc_citizen_quiz_5"] = "NA"

    @staticmethod
    def assign_digitalcitizensbadge(d, survey):
        name = "dc_dpi_quiz_2_"
        for x in xrange(4):
            d[name + str(x+1)] = 0
        name = "dc_oi_quiz_2_"
        for x in xrange(4):
            d[name + str(x+1)] = 0
        name = "dc_citizen_quiz_1_"
        for x in xrange(4):
            d[name + str(x+1)] = 0
        name = "dc_citizen_quiz_4_"
        for x in xrange(4):
            d[name + str(x+1)] = 0
        name = "dc_oi_quiz_5_"
        for x in xrange(5):
            d[name + str(x+1)] = 0
        name = "dc_oi_quiz_6_"
        for x in xrange(4):
            d[name + str(x+1)] = 0
        d["dc_dpi_quiz_1"] = 1
        d["dc_dpi_quiz_3"] = 1
        d["dc_dpi_quiz_4"] = 1
        d["dc_dpi_quiz_5"] = 1
        d["dc_dpi_quiz_6"] = 1
        d["dc_oi_quiz_1"] = 1
        d["dc_oi_quiz_3"] = 1
        d["dc_oi_quiz_4"] = 1
        d["dc_citizen_quiz_2"] = 1
        d["dc_citizen_quiz_3"] = 1
        d["dc_citizen_quiz_4"] = 1
        d["dc_citizen_quiz_5"] = 1

        for i in survey["answers"]:
            if i["no"] == 1:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "dc_dpi_quiz_2_"
                for x in xrange(4):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 7:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "dc_oi_quiz_2_"
                for x in xrange(4):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 10:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "dc_citizen_quiz_1_"
                for x in xrange(4):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 13:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "dc_citizen_quiz_4_"
                for x in xrange(4):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 15:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "dc_oi_quiz_5_"
                for x in xrange(5):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 16:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "dc_oi_quiz_6_"
                for x in xrange(4):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif 0 <= i["no"] <= 5:
                d["dc_dpi_quiz_" + str(i["no"]+1)] = int(i.get("ansval") or 0) + 1
            elif 6 <= i["no"] <= 9:
                d["dc_oi_quiz_" + str(i["no"]-5)] = int(i.get("ansval") or 0) + 1
            elif 11 <= i["no"] <= 14:
                d["dc_citizen_quiz_" + str(i["no"]-9)] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def transform_digiworld(d):
        if d.get("dc_dt_acc_1") == "NA":
            return {"dc_dt_acc_1": "NA",
                    "dc_dt_acc_2": "NA"}

        return {"dc_dt_acc_1": 4-d.get("dc_dt_acc_1", 1),
                "dc_dt_acc_2": 4-d.get("dc_dt_acc_2", 1)}

    @staticmethod
    def transform_persona(d):
        if d.get("dt_cong_1") == "NA":
            return {"dt_cong_1": "NA",
                    "dt_cong_2": "NA",
                    "dc_oim_1": "NA"}

        return {"dt_cong_1": 5-d.get("dt_cong_1", 1),
                "dt_cong_2": 5-d.get("dt_cong_2", 1),
                "dc_oim_1": d.get("dc_oim_1", 1) if d.get("dc_oim_1", 1) != 4 else 2}

    @staticmethod
    def transform_onoffline(d):
        if d.get("dt_cong_3") == "NA":
            return {"dt_cong_3": "NA",
                    "dt_cong_4": "NA",
                    "dt_cong_5": "NA",
                    "dt_cong_6": "NA",
                    "dt_cong_7": "NA"}

        return {"dt_cong_3": d.get("dt_cong_3", 1),
                "dt_cong_4": 5-d.get("dt_cong_4", 1),
                "dt_cong_5": d.get("dt_cong_5", 1),
                "dt_cong_6": 5-d.get("dt_cong_6", 1),
                "dt_cong_7": 5-d.get("dt_cong_7", 1)}

    @staticmethod
    def transform_strength(d):
        if d.get("dc_selfefficacy_1") == "NA":
            return {"dc_selfefficacy_1": "NA",
                    "dc_selfefficacy_2": "NA",
                    "dc_selfefficacy_3": "NA",
                    "dc_selfefficacy_4": "NA",
                    "dc_selfefficacy_5": "NA"}

        return {"dc_selfefficacy_1": d.get("dc_selfefficacy_1", 1),
                "dc_selfefficacy_2": d.get("dc_selfefficacy_2", 1),
                "dc_selfefficacy_3": d.get("dc_selfefficacy_3", 1),
                "dc_selfefficacy_4": 5-d.get("dc_selfefficacy_4", 1),
                "dc_selfefficacy_5": d.get("dc_selfefficacy_5", 1)}

    @staticmethod
    def transform_pretest(d):
        return {
            "df_beh_pre": d["Q1_1"] + d["Q1_2"] + d["Q1_3"] + d["Q1_4"] + d["Q1_5"]*3 + d["Q1_6"]*2 + d["Q1_7"] + d["Q1_8"]
        }

    @staticmethod
    def transform_digitalcitizensbadge(d):
        if d.get("dc_dpi_quiz_1") == "NA":
            return {
                "dc_dpi_quiz_1": "NA",
                "dc_dpi_quiz_2": "NA",
                "dc_dpi_quiz_3": "NA",
                "dc_dpi_quiz_4": "NA",
                "dc_dpi_quiz_5": "NA",
                "dc_dpi_quiz_6": "NA",
                "dc_oi_quiz_1": "NA",
                "dc_oi_quiz_2": "NA",
                "dc_oi_quiz_3": "NA",
                "dc_oi_quiz_4": "NA",
                "dc_oi_quiz_5": "NA",
                "dc_oi_quiz_6": "NA",
                "dc_citizen_quiz_1": "NA",
                "dc_citizen_quiz_2": "NA",
                "dc_citizen_quiz_3": "NA",
                "dc_citizen_quiz_4": "NA",
                "dc_citizen_quiz_5": "NA"
            }

        return {
            "dc_dpi_quiz_1": 1 if d.get("dc_dpi_quiz_1", 0) == 1 else 0,
            "dc_dpi_quiz_2": 1 if (int(d.get("dc_dpi_quiz_2_1", 0) == 1) and
                                   int(d.get("dc_dpi_quiz_2_2", 0) == 1)) else 0,
            "dc_dpi_quiz_3": 1 if d.get("dc_dpi_quiz_3", 0) == 2 else 0,
            "dc_dpi_quiz_4": 1 if d.get("dc_dpi_quiz_4", 0) == 3 else 0,
            "dc_dpi_quiz_5": 1 if d.get("dc_dpi_quiz_5", 0) == 1 else 0,
            "dc_dpi_quiz_6": 1 if d.get("dc_dpi_quiz_6", 0) == 1 else 0,
            "dc_oi_quiz_1": 1 if d.get("dc_oi_quiz_1", 0) == 2 else 0,
            "dc_oi_quiz_2": 0 if d.get("dc_oi_quiz_2_4", 0) > 0
                            else (d.get("dc_oi_quiz_2_1", 0)+d.get("dc_oi_quiz_2_2", 0)+d.get("dc_oi_quiz_2_3", 0))/3.0,
            "dc_oi_quiz_3": 1 if d.get("dc_oi_quiz_3", 0) == 1 else 0,
            "dc_oi_quiz_4": 1 if d.get("dc_oi_quiz_4", 0) == 4 else 0,
            "dc_oi_quiz_5": 0 if d.get("dc_oi_quiz_5_3", 0) > 0
                            else (d.get("dc_oi_quiz_5_1", 0)+d.get("dc_oi_quiz_5_2", 0)+d.get("dc_oi_quiz_5_4", 0)+
                                  d.get("dc_oi_quiz_5_5", 0))/4.0,
            "dc_oi_quiz_6": 0 if d.get("dc_oi_quiz_6_1", 0) > 0
                            else (d.get("dc_oi_quiz_6_2", 0)+d.get("dc_oi_quiz_6_3", 0)+d.get("dc_oi_quiz_6_4", 0))/3.0,
            "dc_citizen_quiz_1": 0 if d.get("dc_citizen_quiz_1_1", 0)+d.get("dc_citizen_quiz_1_2", 0) > 0
                                 else (d.get("dc_citizen_quiz_1_3", 0)+d.get("dc_citizen_quiz_1_4", 0))/2.0,
            "dc_citizen_quiz_2": 1 if d.get("dc_citizen_quiz_2", 0) == 2 else 0,
            "dc_citizen_quiz_3": 1 if d.get("dc_citizen_quiz_3", 0) == 1 else 0,
            "dc_citizen_quiz_4": 0 if d.get("dc_citizen_quiz_4_2", 0)+d.get("dc_citizen_quiz_4_4", 0) > 0
                                 else (d.get("dc_citizen_quiz_4_1", 0)+d.get("dc_citizen_quiz_4_3", 0))/2.0,
            "dc_citizen_quiz_5": 1 if d.get("dc_citizen_quiz_5", 0) == 2 else 0,
        }


class DigitalfootprintDQResult(crudmgo.RootDocument):
    __collection__ = "digitalfootprintdqresults"

    structure = {
        "userid": ObjectId,
        "created": {
            "by": basestring,
            "on": datetime.datetime,
            "username": basestring
        },
        "meta": {}
    }
    indexes = [
        {"fields": "created.by",
         "check": False}
    ]
    default_values = {"created.by": lambda: current_user.id, "created.on": crudmgo.localtime,
                      "created.username": lambda: current_user.get_username(), "meta": {}}

    def get_dqresult(self, user, cacheonly=False):
        if not user:
            return None

        r = self.find_one({"userid": user.id})
        if not r:
            r = self()
            r["userid"] = user.id
            if r.calc_dqscore():
                r.save()
            else:
                r = None
        elif not cacheonly:
            r.calc_dqscore()
            r.save()
        return r

    def has_dqresult(self, user):
        if not user:
            return None

        r = self.find_one({"userid": user.id})
        return r is not None

    def calc_dqscore(self, userid=None, user=None):
        if not ObjectId.is_valid(userid):
            userid = None

        if userid:
            userid = ObjectId(userid)
        elif self.get("userid") and isinstance(self["userid"], ObjectId):
            userid = self["userid"]
        else:
            return False

        cfg = {}

        d = self
        r = None
        db = self.collection.database
        model = db["SurveyDQAnswer"]

        if user is None:
            user = db["IZHero"].find_one({"_id": userid})
            if not user:
                return False

        progress = user.get("dq_progress", {})

        if current_app.config.get('R_RCMD'):
            cfg['RCMD'] = current_app.config['R_RCMD']

        try:
            survey = db["SurveyDQ"].find_one({"name": "digifootprint.v1"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "digifootprint" not in progress:
                # self.get_digifootprint_na(d)
                return False
            else:
                self.assign_digifootprint(d, survey)

            survey = db["SurveyDQ"].find_one({"name": "persistfootprint"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "persistfootprint" not in progress:
                # self.get_persistfootprint_na(d)
                return False
            else:
                self.assign_persistfootprint(d, survey)

            survey = db["SurveyDQ"].find_one({"name": "digitalfootprintbadge"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey and "digitalfootprintbadge" not in progress:
                # self.get_digitalfootprintbadge_na(d)
                return False
            else:
                self.assign_digitalfootprintbadge(d, survey)

            survey = model.find_one({"surveyname": "digirep-messenger",
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if "digirep" in progress:
                if not survey:
                    survey = {"answers": []}
                if not survey or not self.assign_digirep(d, survey):
                    return False
            else:
                # self.get_digirep_na(d)
                return False

            r = R(**cfg)

            for k, v in d.iteritems():
                if isinstance(v, (int, float)):
                    r.assign(k, v)
            for k, v in self.transform_digitalfootprintbadge(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_persistfootprint(d).iteritems():
                r.assign(k, v)

            r(digitalfootprint.r_algo)

            self["df_mgmt_score"] = r.get("df_mgmt_score")

            p = r.prog
            r = None
            p.terminate()
        except Exception as e:
            if r and hasattr(r, "prog") and hasattr(r.prog, "terminate"):
                r.prog.terminate()
            return False

        return True

    def get_dqscores(self):
        return {
            "df_mgmt_score": self.get("df_mgmt_score", 0)
        }

    def transform_vars(self):
        d = {k: v for k, v in self.iteritems()}
        d.update(self.transform_digitalfootprintbadge(d))
        d.update(self.transform_persistfootprint(d))
        return d

    @staticmethod
    def get_digifootprint_na(d):
        for x in xrange(13):
            d["df_beh_" + str(x+1)] = "NA"

    @staticmethod
    def assign_digifootprint(d, survey):
        for x in xrange(13):
            d["df_beh_" + str(x+1)] = 0

        for i in survey["answers"]:
            if i["no"] == 2:
                d["df_beh_13"] = int(i.get("ansval") or 0) + 1
            elif 0 <= i["no"] <= 1:
                d["df_beh_" + str(i["no"]+1)] = int(i.get("ansval") or 0) + 1
            elif 3 <= i["no"] <= 12:
                d["df_beh_" + str(i["no"])] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_persistfootprint_na(d):
        for x in xrange(4):
            d["df_nat_q_" + str(x + 1)] = "NA"

    @staticmethod
    def assign_persistfootprint(d, survey):
        for x in xrange(4):
            d["df_nat_q_" + str(x + 1)] = 1

        for i in survey["answers"]:
            if 0 <= i["no"] <= 3:
                d["df_nat_q_" + str(i["no"]+1)] = 0 if int(i.get("ansval") or 0) else 1
        return

    @staticmethod
    def get_digitalfootprintbadge_na(d):
        name = "df_df_quiz_3_"
        for x in xrange(7):
            d[name + str(x+1)] = "NA"
        name = "df_dp_quiz_1_"
        for x in xrange(4):
            d[name + str(x+1)] = "NA"
        name = "df_dp_quiz_4_"
        for x in xrange(4):
            d[name + str(x+1)] = "NA"
        name = "df_dp_quiz_9_"
        for x in xrange(4):
            d[name + str(x+1)] = "NA"
        name = "df_dp_quiz_12_"
        for x in xrange(4):
            d[name + str(x+1)] = "NA"
        name = "df_dp_quiz_2_"
        for x in xrange(5):
            d[name + str(x+1)] = "NA"
        d["df_dp_quiz_3"] = "NA"
        d["df_dp_quiz_5"] = "NA"
        d["df_dp_quiz_6"] = "NA"
        d["df_dp_quiz_7"] = "NA"
        d["df_dp_quiz_8"] = "NA"
        d["df_dp_quiz_10"] = "NA"
        d["df_dp_quiz_11"] = "NA"
        d["df_df_quiz_1"] = "NA"
        d["df_df_quiz_2"] = "NA"
        d["df_df_quiz_4"] = "NA"
        d["df_df_quiz_5"] = "NA"
        d["df_df_quiz_6"] = "NA"

    @staticmethod
    def assign_digitalfootprintbadge(d, survey):
        name = "df_df_quiz_3_"
        for x in xrange(7):
            d[name + str(x+1)] = 0
        name = "df_dp_quiz_1_"
        for x in xrange(4):
            d[name + str(x+1)] = 0
        name = "df_dp_quiz_4_"
        for x in xrange(4):
            d[name + str(x+1)] = 0
        name = "df_dp_quiz_9_"
        for x in xrange(4):
            d[name + str(x+1)] = 0
        name = "df_dp_quiz_12_"
        for x in xrange(4):
            d[name + str(x+1)] = 0
        name = "df_dp_quiz_2_"
        for x in xrange(5):
            d[name + str(x+1)] = 0
        d["df_dp_quiz_3"] = 1
        d["df_dp_quiz_5"] = 1
        d["df_dp_quiz_6"] = 1
        d["df_dp_quiz_7"] = 1
        d["df_dp_quiz_8"] = 1
        d["df_dp_quiz_10"] = 1
        d["df_dp_quiz_11"] = 1
        d["df_df_quiz_1"] = 1
        d["df_df_quiz_2"] = 1
        d["df_df_quiz_4"] = 1
        d["df_df_quiz_5"] = 1
        d["df_df_quiz_6"] = 1

        for i in survey["answers"]:
            if i["no"] == 2:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "df_df_quiz_3_"
                for x in xrange(7):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] in (6, 9, 14, 17):
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "df_dp_quiz_%d_" % (i["no"]-5)
                for x in xrange(4):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 7:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "df_dp_quiz_2_"
                for x in xrange(5):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif 10 <= i["no"] <= 13 or 15 <= i["no"] <= 16 or i["no"] == 8:
                d["df_dp_quiz_" + str(i["no"]-5)] = int(i.get("ansval") or 0) + 1
            elif 0 <= i["no"] <= 1 or 3 <= i["no"] <= 5:
                d["df_df_quiz_" + str(i["no"]+1)] = int(i.get("ansval") or 0) + 1
        return

    @staticmethod
    def get_digirep_na(d):
        d["df_mgmt_1"] = "NA"
        d["df_mgmt_2"] = "NA"
        d["df_mgmt_3"] = "NA"
        d["df_mgmt_4"] = "NA"
        d["df_mgmt_5"] = "NA"

    @staticmethod
    def assign_digirep(d, survey):
        d["df_mgmt_1"] = 1
        d["df_mgmt_2"] = 1
        d["df_mgmt_3"] = 1
        d["df_mgmt_4"] = 1
        d["df_mgmt_5"] = 1

        for i in survey["answers"]:
            if i["qns"] == "google":
                d["df_mgmt_1"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "nophoto":
                d["df_mgmt_2"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "careful":
                d["df_mgmt_3"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "care":
                d["df_mgmt_4"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "nickname":
                d["df_mgmt_5"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def transform_persistfootprint(d):
        if d.get("df_nat_q_1") == "NA":
            return {"df_nat_q_1": "NA",
                    "df_nat_q_2": "NA",
                    "df_nat_q_3": "NA",
                    "df_nat_q_4": "NA"}

        return {"df_nat_q_1": 1-d.get("df_nat_q_1", 1),
                "df_nat_q_2": 1-d.get("df_nat_q_2", 1),
                "df_nat_q_3": 1-d.get("df_nat_q_3", 1),
                "df_nat_q_4": 1-d.get("df_nat_q_4", 1)}

    @staticmethod
    def transform_digitalfootprintbadge(d):
        if d.get("df_df_quiz_1") == "NA":
            return {"df_df_quiz_1": "NA",
                    "df_df_quiz_2": "NA",
                    "df_df_quiz_3": "NA",
                    "df_df_quiz_4": "NA",
                    "df_df_quiz_5": "NA",
                    "df_df_quiz_6": "NA",
                    "df_dp_quiz_1": "NA",
                    "df_dp_quiz_2": "NA",
                    "df_dp_quiz_3": "NA",
                    "df_dp_quiz_4": "NA",
                    "df_dp_quiz_5": "NA",
                    "df_dp_quiz_6": "NA",
                    "df_dp_quiz_7": "NA",
                    "df_dp_quiz_8": "NA",
                    "df_dp_quiz_9": "NA",
                    "df_dp_quiz_10": "NA",
                    "df_dp_quiz_11": "NA",
                    "df_dp_quiz_12": "NA"}

        return {"df_df_quiz_1": 1 if d.get("df_df_quiz_1", 1) == 1 else 0,
                "df_df_quiz_2": 1 if d.get("df_df_quiz_2", 1) == 1 else 0,
                "df_df_quiz_3": 0 if d.get("df_df_quiz_3_7", 0) == 1
                                else (d.get("df_df_quiz_3_1", 0)+d.get("df_df_quiz_3_2", 0)+d.get("df_df_quiz_3_3", 0)
                                +d.get("df_df_quiz_3_4", 0)+d.get("df_df_quiz_3_5", 0)+d.get("df_df_quiz_3_6", 0))/6.0,
                "df_df_quiz_4": 1 if d.get("df_df_quiz_4", 1) == 5 else 0,
                "df_df_quiz_5": 1 if d.get("df_df_quiz_5", 1) == 1 else 0,
                "df_df_quiz_6": 1 if d.get("df_df_quiz_6", 1) == 1 else 0,
                "df_dp_quiz_1": 0 if d.get("df_dp_quiz_1_1", 0)+d.get("df_dp_quiz_1_3", 0) > 0
                                else (d.get("df_dp_quiz_1_2", 0)+d.get("df_dp_quiz_1_4", 0))/2.0,
                "df_dp_quiz_2": 0 if d.get("df_dp_quiz_2_1", 0) > 0
                                else (d.get("df_dp_quiz_2_2", 0)+d.get("df_dp_quiz_2_3", 0)+d.get("df_dp_quiz_2_4", 0)
                                      +d.get("df_dp_quiz_2_5", 0))/4.0,
                "df_dp_quiz_3": 1 if d.get("df_dp_quiz_3", 1) == 3 else 0,
                "df_dp_quiz_4": 0 if d.get("df_dp_quiz_4_4", 0) > 0
                                else (d.get("df_dp_quiz_4_1", 0)+d.get("df_dp_quiz_4_2", 0)
                                      +d.get("df_dp_quiz_4_3", 0))/3.0,
                "df_dp_quiz_5": 1 if d.get("df_dp_quiz_5", 1) == 1 else 0,
                "df_dp_quiz_6": 1 if d.get("df_dp_quiz_6", 1) == 4 else 0,
                "df_dp_quiz_7": 1 if d.get("df_dp_quiz_7", 1) == 4 else 0,
                "df_dp_quiz_8": 1 if d.get("df_dp_quiz_8", 1) == 2 else 0,
                "df_dp_quiz_9": 0 if d.get("df_dp_quiz_9_4", 0) > 0
                                else (d.get("df_dp_quiz_9_1", 0)+d.get("df_dp_quiz_9_2", 0)
                                      +d.get("df_dp_quiz_9_3", 0))/3.0,
                "df_dp_quiz_10": d.get("df_dp_quiz_10", 1)/6.,
                "df_dp_quiz_11": 1 if d.get("df_dp_quiz_11", 1) == 2 else 0,
                "df_dp_quiz_12": 0 if d.get("df_dp_quiz_12_4", 0) > 0
                                else (d.get("df_dp_quiz_12_1", 0)+d.get("df_dp_quiz_12_2", 0)
                                      +d.get("df_dp_quiz_12_3", 0))/3.0}

    @staticmethod
    def transform_persistfootprint(d):
        if d.get("df_mgmt_1") == "NA":
            return {"df_mgmt_1": "NA",
                    "df_mgmt_2": "NA",
                    "df_mgmt_3": "NA",
                    "df_mgmt_4": "NA",
                    "df_mgmt_5": "NA"}

        return {"df_mgmt_1": d.get("df_mgmt_1", 1),
                "df_mgmt_2": d.get("df_mgmt_2", 1),
                "df_mgmt_3": d.get("df_mgmt_3", 1),
                "df_mgmt_4": 6-d.get("df_mgmt_4", 1),
                "df_mgmt_5": d.get("df_mgmt_5", 1)}


class SecurityDQResult(crudmgo.RootDocument):
    __collection__ = "securitydqresults"

    structure = {
        "userid": ObjectId,
        "created": {
            "by": basestring,
            "on": datetime.datetime,
            "username": basestring
        },
        "meta": {}
    }
    indexes = [
        {"fields": "created.by",
         "check": False}
    ]
    default_values = {"created.by": lambda: current_user.id, "created.on": crudmgo.localtime,
                      "created.username": lambda: current_user.get_username(), "meta": {}}

    def get_dqresult(self, user, cacheonly=False):
        if not user:
            return None

        r = self.find_one({"userid": user.id})
        if not r:
            r = self()
            r["userid"] = user.id
            if r.calc_dqscore():
                r.save()
            else:
                r = None
        elif not cacheonly:
            r.calc_dqscore()
            r.save()
        return r

    def has_dqresult(self, user):
        if not user:
            return None

        r = self.find_one({"userid": user.id})
        return r is not None

    def calc_dqscore(self, userid=None, user=None):
        if not ObjectId.is_valid(userid):
            userid = None

        if userid:
            userid = ObjectId(userid)
        elif self.get("userid") and isinstance(self["userid"], ObjectId):
            userid = self["userid"]
        else:
            return False

        cfg = {}

        d = self
        r = None
        db = self.collection.database
        model = db["SurveyDQAnswer"]

        if user is None:
            user = db["IZHero"].find_one({"_id": userid})
            if not user:
                return False

        progress = user.get("dq_progress", {})

        if current_app.config.get('R_RCMD'):
            cfg['RCMD'] = current_app.config['R_RCMD']

        try:
            survey = db["SurveyDQ"].find_one({"name": "securitybadge"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey and "securitybadge" not in progress:
                # self.get_securitybadge_na(d)
                return False
            else:
                self.assign_securitybadge(d, survey)

            survey = db["SurveyDQ"].find_one({"name": "createpwd"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "createpwd" not in progress:
                # self.get_createpwd_na(d)
                return False
            else:
                self.assign_createpwd(d, survey)

            survey = model.find_one({"surveyname": "pwdsafe-messenger",
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if "pwdsafe" in progress:
                if not survey:
                    survey = {"answers": []}
                if not survey or not self.assign_pwdsafe(d, survey):
                    return False
            else:
                # self.get_pwdsafe_na(d)
                return False

            survey = db["SurveyDQ"].find_one({"name": "spamscam"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "spamscam" not in progress:
                # self.get_spamscam_na(d)
                return False
            else:
                self.assign_spamscam(d, survey)

            survey = db["SurveyDQ"].find_one({"name": "snsprivacy.v2"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "snsprivacy" not in progress:
                # self.get_snsprivacy_na(d)
                return False
            else:
                self.assign_snsprivacy(d, survey)

            survey = db["SurveyDQ"].find_one({"name": "mobilesafety"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "mobilesafety" not in progress:
                # self.get_mobilesafety_na(d)
                return False
            else:
                self.assign_mobilesafety(d, survey)

            self.assign_user(d, user)

            r = R(**cfg)

            for k, v in d.iteritems():
                if isinstance(v, (int, float)):
                    r.assign(k, v)
            for k, v in self.transform_mobilesafety(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_pwdsafe(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_securitybadge(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_snsprivacy(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_spamscam(d).iteritems():
                r.assign(k, v)

            r(security.r_algo)

            self["sec_score"] = r.get("sec_score")

            p = r.prog
            r = None
            p.terminate()
        except Exception as e:
            if r and hasattr(r, "prog") and hasattr(r.prog, "terminate"):
                r.prog.terminate()
            return False

        return True

    def get_dqscores(self):
        return {
            "sec_score": self.get("sec_score", 0)
        }

    def transform_vars(self):
        d = {k: v for k, v in self.iteritems()}
        d.update(self.transform_spamscam(d))
        d.update(self.transform_mobilesafety(d))
        d.update(self.transform_pwdsafe(d))
        d.update(self.transform_securitybadge(d))
        d.update(self.transform_snsprivacy(d))
        return d

    @staticmethod
    def get_securitybadge_na(d):
        name = "sec_cyberthreats_quiz_3_"
        for x in xrange(4):
            d[name + str(x+1)] = "NA"
        name = "sec_cyberthreats_quiz_6_"
        for x in xrange(4):
            d[name + str(x+1)] = "NA"
        name = "sec_cyberthreats_quiz_8_"
        for x in xrange(4):
            d[name + str(x+1)] = "NA"
        name = "sec_cyberthreats_quiz_9_"
        for x in xrange(5):
            d[name + str(x+1)] = "NA"
        name = "sec_cyberthreats_quiz_10_"
        for x in xrange(4):
            d[name + str(x+1)] = "NA"
        name = "sec_cyberthreats_quiz_13_"
        for x in xrange(3):
            d[name + str(x+1)] = "NA"
        for x in xrange(6):
            d["sec_pwd_know_" + str(x + 1)] = "NA"

        d["sec_cyberthreats_quiz_1"] = "NA"
        d["sec_cyberthreats_quiz_2"] = "NA"
        d["sec_cyberthreats_quiz_4"] = "NA"
        d["sec_cyberthreats_quiz_5"] = "NA"
        d["sec_cyberthreats_quiz_7"] = "NA"
        d["sec_cyberthreats_quiz_11"] = "NA"

    @staticmethod
    def assign_securitybadge(d, survey):
        name = "sec_cyberthreats_quiz_3_"
        for x in xrange(4):
            d[name + str(x+1)] = 0
        name = "sec_cyberthreats_quiz_6_"
        for x in xrange(4):
            d[name + str(x+1)] = 0
        name = "sec_cyberthreats_quiz_8_"
        for x in xrange(4):
            d[name + str(x+1)] = 0
        name = "sec_cyberthreats_quiz_9_"
        for x in xrange(5):
            d[name + str(x+1)] = 0
        name = "sec_cyberthreats_quiz_10_"
        for x in xrange(4):
            d[name + str(x+1)] = 0
        name = "sec_cyberthreats_quiz_13_"
        for x in xrange(3):
            d[name + str(x+1)] = 0
        for x in xrange(6):
            d["sec_pwd_know_" + str(x + 1)] = 1

        d["sec_cyberthreats_quiz_1"] = 1
        d["sec_cyberthreats_quiz_2"] = 1
        d["sec_cyberthreats_quiz_4"] = 1
        d["sec_cyberthreats_quiz_5"] = 1
        d["sec_cyberthreats_quiz_7"] = 1
        d["sec_cyberthreats_quiz_11"] = 1

        for i in survey["answers"]:
            if i["no"] == 14:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "sec_cyberthreats_quiz_9_"
                for x in xrange(5):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] in (8, 11, 13, 15):
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "sec_cyberthreats_quiz_%d_" % (i["no"]-5)
                for x in xrange(4):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 17:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "sec_cyberthreats_quiz_13_"
                for x in xrange(3):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif 0 <= i["no"] <= 5:
                d["sec_pwd_know_" + str(i["no"]+1)] = int(i.get("ansval") or 0) + 1
            elif 6 <= i["no"] <= 7 or 9 <= i["no"] <= 10 or i["no"] in (12, 16):
                d["sec_cyberthreats_quiz_" + str(i["no"]-5)] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_createpwd_na(d):
        d["sec_pwd_act"] = "NA"

    @staticmethod
    def assign_createpwd(d, survey):
        d["sec_pwd_act"] = 1

        for i in survey["answers"]:
            if i["no"] == 0:
                d["sec_pwd_act"] = len(i["anslist"]) if i["anslist"] else 1
        return True

    @staticmethod
    def get_pwdsafe_na(d):
        d["sec_pwd_skill"] = "NA"
        d["sec_pwd_share_a"] = "NA"
        for x in xrange(7):
            d["sec_pwd_share_b_" + str(x+1)] = "NA"

    @staticmethod
    def assign_pwdsafe(d, survey):
        d["sec_pwd_skill"] = 1
        d["sec_pwd_share_a"] = 0
        for x in xrange(7):
            d["sec_pwd_share_b_" + str(x+1)] = 0

        for i in survey["answers"]:
            if i["qns"] == "keeppwd":
                d["sec_pwd_skill"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "sharepwd":
                d["sec_pwd_share_a"] = 0 if i["ansval"] else 1
                if d["sec_pwd_share_a"] == 0:
                    for x in xrange(7):
                        d["sec_pwd_share_b_" + str(x+1)] = 0
            elif i["qns"] == "sharewith":
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "sec_pwd_share_b_"
                for x in xrange(7):
                    d[name + str(x+1)] = 1 if x in l else 0
        return True

    @staticmethod
    def get_spamscam_na(d):
        for x in xrange(6):
            d["sec_cyberthreats_know_" + str(x+1)] = "NA"

    @staticmethod
    def assign_spamscam(d, survey):
        for x in xrange(6):
            d["sec_cyberthreats_know_" + str(x+1)] = 1

        for i in survey["answers"]:
            if 0 <= i["no"] <= 5:
                d["sec_cyberthreats_know_" + str(i["no"]+1)] = 0 if int(i.get("ansval") or 0) else 1
        return True

    @staticmethod
    def get_snsprivacy_na(d):
        d["sec_scam_34"] = "NA"

    @staticmethod
    def assign_snsprivacy(d, survey):
        d["sec_scam_34"] = 0

        for i in survey["answers"]:
            if i["no"] == 11:
                d["sec_scam_34"] = int(i.get("ansval") or 0) + 1
                break
        return True

    @staticmethod
    def get_mobilesafety_na(d):
        for x in xrange(8):
            d["sec_mob_safe_quiz_" + str(x+1)] = "NA"

    @staticmethod
    def assign_mobilesafety(d, survey):
        for x in xrange(8):
            d["sec_mob_safe_quiz_" + str(x+1)] = 1

        for i in survey["answers"]:
            if 0 <= i["no"] <= 7:
                d["sec_mob_safe_quiz_" + str(i["no"]+1)] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_user_na(d):
        d["sec_scam_act"] = "NA"

    @staticmethod
    def assign_user(d, user):
        d["sec_scam_act"] = user.get("data", {}).get("dfquiz", {}).get("sec_scam_act", 0)
        return True

    @staticmethod
    def transform_securitybadge(d):
        if d.get("sec_pwd_know_1") == "NA":
            return {"sec_pwd_know_1": "NA",
                    "sec_pwd_know_2": "NA",
                    "sec_pwd_know_3": "NA",
                    "sec_pwd_know_4": "NA",
                    "sec_pwd_know_5": "NA",
                    "sec_pwd_know_6": "NA",
                    "sec_cyberthreats_quiz_1": "NA",
                    "sec_cyberthreats_quiz_2": "NA",
                    "sec_cyberthreats_quiz_3": "NA",
                    "sec_cyberthreats_quiz_4": "NA",
                    "sec_cyberthreats_quiz_5": "NA",
                    "sec_cyberthreats_quiz_6": "NA",
                    "sec_cyberthreats_quiz_7": "NA",
                    "sec_cyberthreats_quiz_8": "NA",
                    "sec_cyberthreats_quiz_9": "NA",
                    "sec_cyberthreats_quiz_10": "NA",
                    "sec_cyberthreats_quiz_11": "NA",
                    "sec_cyberthreats_quiz_13": "NA"}

        return {"sec_pwd_know_1": 1 if d.get("sec_pwd_know_1", 1) == 2 else 0,
                "sec_pwd_know_2": 1 if d.get("sec_pwd_know_2", 1) == 1 else 0,
                "sec_pwd_know_3": 1 if d.get("sec_pwd_know_3", 1) == 3 else 0,
                "sec_pwd_know_4": 1 if d.get("sec_pwd_know_4", 1) == 3 else 0,
                "sec_pwd_know_5": 1 if d.get("sec_pwd_know_5", 1) == 3 else 0,
                "sec_pwd_know_6": 1 if d.get("sec_pwd_know_6", 1) == 4 else 0,
                "sec_cyberthreats_quiz_1": 1 if d.get("sec_cyberthreats_quiz_1", 1) == 2 else 0,
                "sec_cyberthreats_quiz_2": 1 if d.get("sec_cyberthreats_quiz_2", 1) == 1 else 0,
                "sec_cyberthreats_quiz_3": 0 if d.get("sec_cyberthreats_quiz_3_2", 0)+d.get("sec_cyberthreats_quiz_3_3") > 0
                                           else (d.get("sec_cyberthreats_quiz_3_1", 0)+d.get("sec_cyberthreats_quiz_3_4", 0))/2.0,
                "sec_cyberthreats_quiz_4": 1 if d.get("sec_cyberthreats_quiz_4", 1) == 3 else 0,
                "sec_cyberthreats_quiz_5": 1 if d.get("sec_cyberthreats_quiz_5", 1) == 4 else 0,
                "sec_cyberthreats_quiz_6": 0 if d.get("sec_cyberthreats_quiz_6_4", 0) > 0
                                           else (d.get("sec_cyberthreats_quiz_6_1", 0)
                                                 +d.get("sec_cyberthreats_quiz_6_2", 0)
                                                 +d.get("sec_cyberthreats_quiz_6_3", 0))/3.0,
                "sec_cyberthreats_quiz_7": 1 if d.get("sec_cyberthreats_quiz_7", 1) == 3 else 0,
                "sec_cyberthreats_quiz_8": 0 if d.get("sec_cyberthreats_quiz_8_4", 0) > 0
                                           else (d.get("sec_cyberthreats_quiz_8_1", 0)
                                                 +d.get("sec_cyberthreats_quiz_8_2", 0)
                                                 +d.get("sec_cyberthreats_quiz_8_3", 0))/3.0,
                "sec_cyberthreats_quiz_9": 1 if d.get("sec_cyberthreats_quiz_9_5", 1) == 1 else 0,
                "sec_cyberthreats_quiz_10": 0 if d.get("sec_cyberthreats_quiz_10_1", 0)+d.get("sec_cyberthreats_quiz_10_2", 0) > 0
                                           else (d.get("sec_cyberthreats_quiz_10_3", 0)
                                                 +d.get("sec_cyberthreats_quiz_10_4", 0))/2.0,
                "sec_cyberthreats_quiz_11": 1 if d.get("sec_cyberthreats_quiz_11", 1) == 3 else 0,
                #  "sec_cyberthreats_quiz_12": 1 if d.get("sec_cyberthreats_quiz_12", 1) == 2 else 0,
                "sec_cyberthreats_quiz_13": 0 if d.get("sec_cyberthreats_quiz_13_1", 0) > 0
                                           else (d.get("sec_cyberthreats_quiz_13_2", 0)
                                                 +d.get("sec_cyberthreats_quiz_13_3", 0))/2.0}

    @staticmethod
    def transform_pwdsafe(d):
        if d.get("sec_pwd_share_a") == "NA":
            return {"sec_pwd_share_a": "NA",
                    "sec_pwd_share_b_1": "NA",
                    "sec_pwd_share_b_2": "NA",
                    "sec_pwd_share_b_3": "NA",
                    "sec_pwd_share_b_4": "NA",
                    "sec_pwd_share_b_5": "NA",
                    "sec_pwd_share_b_6": "NA",
                    "sec_pwd_share_b_7": "NA",
                    "sec_pwd_skill": "NA"}

        newd = {"sec_pwd_share_a": 0 if d.get("sec_pwd_share_a", 0) else 10,
                "sec_pwd_share_b_1": d.get("sec_pwd_share_b_1", 0) * 5,
                "sec_pwd_share_b_2": d.get("sec_pwd_share_b_2", 0) * -1,
                "sec_pwd_share_b_3": d.get("sec_pwd_share_b_3", 0) * -2,
                "sec_pwd_share_b_4": d.get("sec_pwd_share_b_4", 0) * -2,
                "sec_pwd_share_b_5": d.get("sec_pwd_share_b_5", 0) * -3,
                "sec_pwd_share_b_6": d.get("sec_pwd_share_b_6", 0) * -3,
                "sec_pwd_share_b_7": d.get("sec_pwd_share_b_7", 0) * -4}

        v = d.get("sec_pwd_skill", 1)
        if v == 1:
            newd["sec_pwd_skill"] = 3
        elif v == 2:
            newd["sec_pwd_skill"] = 1
        elif v == 3:
            newd["sec_pwd_skill"] = 4
        else:
            newd["sec_pwd_skill"] = 2

        return newd

    @staticmethod
    def transform_spamscam(d):
        if d.get("sec_cyberthreats_know_1") == "NA":
            return {"sec_cyberthreats_know_1": "NA",
                    "sec_cyberthreats_know_2": "NA",
                    "sec_cyberthreats_know_3": "NA",
                    "sec_cyberthreats_know_4": "NA",
                    "sec_cyberthreats_know_5": "NA",
                    "sec_cyberthreats_know_6": "NA"}

        return {"sec_cyberthreats_know_1": 0 if d.get("sec_cyberthreats_know_1", 0) else 1,
                "sec_cyberthreats_know_2": 0 if d.get("sec_cyberthreats_know_2", 0) else 1,
                "sec_cyberthreats_know_3": 0 if d.get("sec_cyberthreats_know_3", 0) else 1,
                "sec_cyberthreats_know_4": 0 if d.get("sec_cyberthreats_know_4", 0) else 1,
                "sec_cyberthreats_know_5": 0 if d.get("sec_cyberthreats_know_5", 0) else 1,
                "sec_cyberthreats_know_6": 0 if d.get("sec_cyberthreats_know_6", 0) else 1}

    @staticmethod
    def transform_snsprivacy(d):
        if d.get("sec_scam_34") == "NA":
            return {"sec_scam_34": "NA"}

        newd = {}

        v = d.get("sec_scam_34", 1)
        if v == 1 or v == 2:
            newd["sec_scam_34"] = 2
        elif v == 3:
            newd["sec_scam_34"] = 4
        else:
            newd["sec_scam_34"] = 1

        return newd

    @staticmethod
    def transform_mobilesafety(d):
        if d.get("sec_mob_safe_quiz_1") == "NA":
            return {"sec_mob_safe_quiz_1": "NA",
                    "sec_mob_safe_quiz_2": "NA",
                    "sec_mob_safe_quiz_3": "NA",
                    "sec_mob_safe_quiz_4": "NA",
                    "sec_mob_safe_quiz_5": "NA",
                    "sec_mob_safe_quiz_6": "NA",
                    "sec_mob_safe_quiz_7": "NA",
                    "sec_mob_safe_quiz_8": "NA"}

        return {"sec_mob_safe_quiz_1": 1 if d.get("sec_mob_safe_quiz_1", 1) == 1 else 0,
                "sec_mob_safe_quiz_2": 1 if d.get("sec_mob_safe_quiz_2", 1) == 2 else 0,
                "sec_mob_safe_quiz_3": 1 if d.get("sec_mob_safe_quiz_3", 1) == 1 else 0,
                "sec_mob_safe_quiz_4": 1 if d.get("sec_mob_safe_quiz_4", 1) == 1 else 0,
                "sec_mob_safe_quiz_5": 1 if d.get("sec_mob_safe_quiz_5", 1) == 3 else 0,
                "sec_mob_safe_quiz_6": 1 if d.get("sec_mob_safe_quiz_6", 1) == 2 else 0,
                "sec_mob_safe_quiz_7": 1 if d.get("sec_mob_safe_quiz_7", 1) == 1 else 0,
                "sec_mob_safe_quiz_8": 1 if d.get("sec_mob_safe_quiz_8", 1) == 3 else 0}


class CriticalthinkingDQResult(crudmgo.RootDocument):
    __collection__ = "criticalthinkingdqresults"

    structure = {
        "userid": ObjectId,
        "created": {
            "by": basestring,
            "on": datetime.datetime,
            "username": basestring
        },
        "meta": {}
    }
    indexes = [
        {"fields": "created.by",
         "check": False}
    ]
    default_values = {"created.by": lambda: current_user.id, "created.on": crudmgo.localtime,
                      "created.username": lambda: current_user.get_username(), "meta": {}}

    def get_dqresult(self, user, cacheonly=False):
        if not user:
            return None

        r = self.find_one({"userid": user.id})
        if not r:
            r = self()
            r["userid"] = user.id
            if r.calc_dqscore():
                r.save()
            else:
                r = None
        elif not cacheonly:
            r.calc_dqscore()
            r.save()
        return r

    def has_dqresult(self, user):
        if not user:
            return None

        r = self.find_one({"userid": user.id})
        return r is not None

    def calc_dqscore(self, userid=None, user=None):
        if not ObjectId.is_valid(userid):
            userid = None

        if userid:
            userid = ObjectId(userid)
        elif self.get("userid") and isinstance(self["userid"], ObjectId):
            userid = self["userid"]
        else:
            return False

        cfg = {}

        d = self
        r = None
        db = self.collection.database
        model = db["SurveyDQAnswer"]

        if user is None:
            user = db["IZHero"].find_one({"_id": userid})
            if not user:
                return False

        progress = user.get("dq_progress", {})

        if current_app.config.get('R_RCMD'):
            cfg['RCMD'] = current_app.config['R_RCMD']

        try:
            survey = db["SurveyDQ"].find_one({"name": "violentcontent"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "violentcontent" not in progress:
                # self.get_violentcontent_na(d)
                return False
            else:
                self.assign_violentcontent(d, survey)

            survey = db["SurveyDQ"].find_one({"name": "inapprocontent"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "inapprocontent" not in progress:
                # self.get_inapprocontent_na(d)
                return False
            else:
                self.assign_inapprocontent(d, survey)

            survey = db["SurveyDQ"].find_one({"name": "criticalthinkingbadge.v1"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey and "criticalthinkingbadge" not in progress:
                # self.get_criticalthinkingbadge_na(d)
                return False
            else:
                self.assign_criticalthinkingbadge(d, survey)

            survey = db["SurveyDQ"].find_one({"name": "contentcritique"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "contentcritique" not in progress:
                # self.get_contentcritique_na(d)
                return False
            else:
                self.assign_contentcritique(d, survey)

            survey = db["SurveyDQ"].find_one({"name": "snsprivacy.v2"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "snsprivacy" not in progress:
                # self.get_snsprivacy_na(d)
                return False
            else:
                self.assign_snsprivacy(d, survey)

            survey = db["SurveyDQ"].find_one({"name": "onlinefriends"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "onlinefriends" not in progress:
                # self.get_onlinefriends_na(d)
                return False
            else:
                self.assign_onlinefriends(d, survey)

            survey = model.find_one({"surveyname": "friendbehavior-messenger",
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if "friendbehavior" in progress:
                if not survey:
                    survey = {"answers": []}
                if not survey or not self.assign_friendsbehavior(d, survey):
                    return False
            else:
                # self.get_friendsbehavior_na(d)
                return False

            survey = db["SurveyDQ"].find_one({"name": "truefalse"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "truefalse" not in progress:
                # self.get_truefalse_na(d)
                return False
            else:
                self.assign_truefalse(d, survey)

            r = R(**cfg)

            for k, v in d.iteritems():
                if isinstance(v, (int, float)):
                    r.assign(k, v)
            for k, v in self.transform_snsprivacy(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_contentcritique(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_criticalthinkingbadge(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_inapprocontent(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_friendsbehavior(d).iteritems():
                r.assign(k, v)

            r(util.r_sc_func)
            r(criticalthinking.r_algo)

            self["ct_score"] = r.get("ct_score")

            p = r.prog
            r = None
            p.terminate()
        except Exception as e:
            if r and hasattr(r, "prog") and hasattr(r.prog, "terminate"):
                r.prog.terminate()
            return False

        return True

    def get_dqscores(self):
        return {
            "ct_score": self.get("ct_score", 0)
        }

    def transform_vars(self):
        d = {k: v for k, v in self.iteritems()}
        d.update(self.transform_inapprocontent(d))
        d.update(self.transform_contentcritique(d))
        d.update(self.transform_criticalthinkingbadge(d))
        d.update(self.transform_friendsbehavior(d))
        d.update(self.transform_snsprivacy(d))
        return d

    @staticmethod
    def get_violentcontent_na(d):
        d["ct_mv_v_1"] = ""
        d["ct_mv_v_b_1"] = ""
        d["ct_mv_g_1"] = ""
        d["ct_mv_g_b_1"] = ""
        for i in xrange(3):
            d["ct_mv_v_" + str(i+2)] = "NA"
        for i in xrange(3):
            d["ct_mv_v_b_" + str(i+2)] = "NA"
        for i in xrange(5):
            d["ct_mv_g_" + str(i+2)] = "NA"
        for i in xrange(5):
            d["ct_mv_g_b_" + str(i+2)] = "NA"

    @staticmethod
    def assign_violentcontent(d, survey):
        d["ct_mv_v_1"] = ""
        d["ct_mv_v_b_1"] = ""
        d["ct_mv_g_1"] = ""
        d["ct_mv_g_b_1"] = ""
        for i in xrange(3):
            d["ct_mv_v_" + str(i+2)] = 1
        for i in xrange(3):
            d["ct_mv_v_b_" + str(i+2)] = 1
        for i in xrange(5):
            d["ct_mv_g_" + str(i+2)] = 1
        for i in xrange(5):
            d["ct_mv_g_b_" + str(i+2)] = 1

        for i in survey["answers"]:
            if 1 <= i["no"] <= 3:
                d["ct_mv_v_" + str(i["no"]+1)] = int(i.get("ansval") or 0) + 1
            elif 5 <= i["no"] <= 7:
                d["ct_mv_v_b_" + str(i["no"]-3)] = int(i.get("ansval") or 0) + 1
            elif 9 <= i["no"] <= 13:
                d["ct_mv_g_" + str(i["no"]-7)] = int(i.get("ansval") or 0) + 1
            elif 15 <= i["no"] <= 19:
                d["ct_mv_g_b_" + str(i["no"]-13)] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 0:
                d["ct_mv_v_1"] = i.get("ans", "")
            elif i["no"] == 4:
                d["ct_mv_v_b_1"] = i.get("ans", "")
            elif i["no"] == 8:
                d["ct_mv_g_1"] = i.get("ans", "")
            elif i["no"] == 14:
                d["ct_mv_g_b_1"] = i.get("ans", "")
        return True

    @staticmethod
    def get_inapprocontent_na(d):
        name = "ct_inapp_"
        for x in xrange(7):
            d[name + str(x+1)] = "NA"
        d["ct_inapp_c"] = "NA"

    @staticmethod
    def assign_inapprocontent(d, survey):
        name = "ct_inapp_"
        for x in xrange(7):
            d[name + str(x+1)] = 0
        d["ct_inapp_c"] = 1

        for i in survey["answers"]:
            if i["no"] == 1:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "ct_inapp_"
                for x in xrange(7):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 2:
                d["ct_inapp_c"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_criticalthinkingbadge_na(d):
        d["ct_content_quiz_1"] = "NA"
        d["ct_content_quiz_3"] = "NA"
        name = "ct_content_quiz_2_"
        for x in xrange(5):
            d[name + str(x+1)] = "NA"
        d["ct_content_quiz_2"] = "NA"
        name = "ct_content_quiz_4_"
        for x in xrange(4):
            d[name + str(x+1)] = "NA"
        d["ct_contact_quiz_2"] = "NA"
        d["ct_contact_quiz_3"] = "NA"
        d["ct_contact_quiz_4"] = "NA"
        d["ct_contact_quiz_5"] = "NA"
        d["ct_ie_quiz_1"] = "NA"
        d["ct_ie_quiz_3"] = "NA"
        d["ct_ie_quiz_5"] = "NA"
        d["ct_ie_quiz_6"] = "NA"
        d["ct_ie_quiz_7"] = "NA"
        d["ct_ie_quiz_8"] = "NA"
        d["ct_ie_quiz_9"] = "NA"
        name = "ct_ie_quiz_10_"
        for x in xrange(5):
            d[name + str(x+1)] = "NA"
        name = "ct_ie_quiz_15_"
        for x in xrange(5):
            d[name + str(x+1)] = "NA"
        name = "ct_contact_quiz_6_"
        for x in xrange(4):
            d[name + str(x+1)] = "NA"
        name = "ct_content_quiz_5_"
        for x in xrange(5):
            d[name + str(x+1)] = "NA"

    @staticmethod
    def assign_criticalthinkingbadge(d, survey):
        d["ct_content_quiz_1"] = 1
        d["ct_content_quiz_3"] = 1
        name = "ct_content_quiz_2_"
        for x in xrange(5):
            d[name + str(x+1)] = 0
        d["ct_content_quiz_2"] = 0
        name = "ct_content_quiz_4_"
        for x in xrange(4):
            d[name + str(x+1)] = 0
        d["ct_contact_quiz_2"] = 1
        d["ct_contact_quiz_3"] = 1
        d["ct_contact_quiz_4"] = 1
        d["ct_contact_quiz_5"] = 1
        d["ct_ie_quiz_1"] = 1
        d["ct_ie_quiz_3"] = 1
        d["ct_ie_quiz_5"] = 1
        d["ct_ie_quiz_6"] = 1
        d["ct_ie_quiz_7"] = 1
        d["ct_ie_quiz_8"] = 1
        d["ct_ie_quiz_9"] = 1
        name = "ct_ie_quiz_10_"
        for x in xrange(5):
            d[name + str(x+1)] = 0
        name = "ct_ie_quiz_15_"
        for x in xrange(5):
            d[name + str(x+1)] = 0
        name = "ct_contact_quiz_6_"
        for x in xrange(4):
            d[name + str(x+1)] = 0
        name = "ct_content_quiz_5_"
        for x in xrange(5):
            d[name + str(x+1)] = 0

        for i in survey["answers"]:
            if i["no"] == 0 or i["no"] == 2:
                d["ct_content_quiz_" + str(i["no"]+1)] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 1:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "ct_content_quiz_2_"
                for x in xrange(5):
                    d[name + str(x+1)] = 1 if x in l else 0

                if len(i["anslist"]) == 0:
                    d["ct_content_quiz_2"] = 0
                elif i["anslist"] == [1]:
                    d["ct_content_quiz_2"] = 2
                elif i["anslist"][0] != 1:
                    d["ct_content_quiz_2"] = i["anslist"][0] + 1
                else:
                    d["ct_content_quiz_2"] = i["anslist"][1] + 1
            elif i["no"] == 3:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "ct_content_quiz_4_"
                for x in xrange(4):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif 4 <= i["no"] <= 7:
                d["ct_contact_quiz_" + str(i["no"]-2)] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 8:
                d["ct_ie_quiz_1"] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 9:
                d["ct_ie_quiz_3"] = int(i.get("ansval") or 0) + 1
            elif 10 <= i["no"] <= 14:
                d["ct_ie_quiz_" + str(i["no"]-5)] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 15:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "ct_ie_quiz_10_"
                for x in xrange(5):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 16:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "ct_ie_quiz_15_"
                for x in xrange(5):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 17:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "ct_contact_quiz_6_"
                for x in xrange(4):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 18:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "ct_content_quiz_5_"
                for x in xrange(5):
                    d[name + str(x+1)] = 1 if x in l else 0
        return True

    @staticmethod
    def get_contentcritique_na(d):
        for x in xrange(7):
            d["ct_block_a_" + str(x+1)] = "NA"

    @staticmethod
    def assign_contentcritique(d, survey):
        for x in xrange(7):
            d["ct_block_a_" + str(x+1)] = 0

        for i in survey["answers"]:
            if 0 <= i["no"] <= 6:
                d["ct_block_a_" + str(i["no"]+1)] = 1 if int(i.get("ansval") or 0) in (1, 2) else 0
        return True

    @staticmethod
    def get_snsprivacy_na(d):
        d["ct_contact_risk"] = "NA"

    @staticmethod
    def assign_snsprivacy(d, survey):
        d["ct_contact_risk"] = 0

        for i in survey["answers"]:
            if i["no"] == 10:
                d["ct_contact_risk"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_onlinefriends_na(d):
        name = "cb_of_a_"
        for x in xrange(7):
            d[name + str(x+1)] = "NA"
        d["ct_ofm_att_2"] = "NA"
        name = "ct_ofm_st_"
        for x in xrange(7):
            d[name + str(x+1)] = "NA"

    @staticmethod
    def assign_onlinefriends(d, survey):
        name = "cb_of_a_"
        for x in xrange(7):
            d[name + str(x+1)] = 0
        d["ct_ofm_att_2"] = 1
        name = "ct_ofm_st_"
        for x in xrange(7):
            d[name + str(x+1)] = 0

        for i in survey["answers"]:
            if i["no"] == 1:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "cb_of_a_"
                for x in xrange(7):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["no"] == 2:
                d["ct_ofm_att_2"] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 3:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "ct_ofm_st_"
                for x in xrange(7):
                    d[name + str(x+1)] = 1 if x in l else 0
        return True

    @staticmethod
    def get_friendsbehavior_na(d):
        d["ct_of_chat_1"] = "NA"
        d["ct_ofm_beh_1"] = "NA"

        for i in xrange(7):
            d["ct_ofm_tell1_" + str(i+1)] = "NA"
        for i in xrange(7):
            d["ct_ofm_bring_" + str(i+1)] = "NA"
        for i in xrange(7):
            d["ct_ofm_tell2_" + str(i+1)] = "NA"

    @staticmethod
    def assign_friendsbehavior(d, survey):
        d["ct_of_chat_1"] = 2
        d["ct_ofm_beh_1"] = 2

        for i in xrange(7):
            d["ct_ofm_tell1_" + str(i+1)] = 0
        for i in xrange(7):
            d["ct_ofm_bring_" + str(i+1)] = 0
        for i in xrange(7):
            d["ct_ofm_tell2_" + str(i+1)] = 0

        for i in survey["answers"]:
            if i["qns"] == "chatonline":
                d["ct_of_chat_1"] = 1 if int(i.get("ansval") or 0) else 2
            elif i["qns"] == "meetoffline":
                d["ct_ofm_beh_1"] = 1 if int(i.get("ansval") or 0) else 2
            elif i["qns"] == "tellpeople":
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "ct_ofm_tell1_"
                for x in xrange(7):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["qns"] == "bringpeople":
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "ct_ofm_bring_"
                for x in xrange(7):
                    d[name + str(x+1)] = 1 if x in l else 0
            elif i["qns"] == "tellafterwards":
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "ct_ofm_tell2_"
                for x in xrange(7):
                    d[name + str(x+1)] = 1 if x in l else 0
        return True

    @staticmethod
    def get_truefalse_na(d):
        for x in xrange(7):
            d["ct_eval_" + str(x + 1)] = "NA"
        for x in xrange(4):
            d["ct_ie_quiz_" + str(x+11)] = "NA"

    @staticmethod
    def assign_truefalse(d, survey):
        for x in xrange(7):
            d["ct_eval_" + str(x + 1)] = 0
        for x in xrange(4):
            d["ct_ie_quiz_" + str(x+11)] = 1

        for i in survey["answers"]:
            if 0 <= i["no"] <= 3:
                d["ct_ie_quiz_" + str(i["no"]+11)] = 1 if int(i.get("ansval") or 0) == 0 else 0
        return True

    @staticmethod
    def transform_inapprocontent(d):
        if d.get("ct_inapp_1") == "NA":
            return {
                "ct_inapp_1": "NA",
                "ct_inapp_2": "NA",
                "ct_inapp_3": "NA",
                "ct_inapp_4": "NA",
                "ct_inapp_5": "NA",
                "ct_inapp_6": "NA",
                "ct_inapp_7": "NA",
                "ct_inapp_c": "NA"
            }

        newd = {}

        for i in xrange(7):
            newd["ct_inapp_" + str(i+1)] = d.get("ct_inapp_" + str(i+1), 0)

        v = d.get("ct_inapp_c", 1)
        if v == 1:
            newd["ct_inapp_c"] = -1
        elif v == 2:
            newd["ct_inapp_c"] = 3
        else:
            newd["ct_inapp_c"] = 0

        return newd

    @staticmethod
    def transform_criticalthinkingbadge(d):
        if d.get("ct_content_quiz_1") == "NA":
            return {"ct_content_quiz_1": "NA",
                    "ct_content_quiz_2": "NA",
                    "ct_content_quiz_3": "NA",
                    "ct_content_quiz_4": "NA",
                    "ct_content_quiz_5": "NA",
                    "ct_contact_quiz_2": "NA",
                    "ct_contact_quiz_3": "NA",
                    "ct_contact_quiz_4": "NA",
                    "ct_contact_quiz_5": "NA",
                    "ct_contact_quiz_6": "NA",
                    "ct_ie_quiz_1": "NA",
                    "ct_ie_quiz_3": "NA",
                    "ct_ie_quiz_5": "NA",
                    "ct_ie_quiz_6": "NA",
                    "ct_ie_quiz_7": "NA",
                    "ct_ie_quiz_8": "NA",
                    "ct_ie_quiz_9": "NA",
                    "ct_ie_quiz_10": "NA",
                    "ct_ie_quiz_11": "NA",
                    "ct_ie_quiz_12": "NA",
                    "ct_ie_quiz_13": "NA",
                    "ct_ie_quiz_14": "NA",
                    "ct_ie_quiz_15": "NA"}

        return {"ct_content_quiz_1": 1 if d.get("ct_content_quiz_1", 1) == 4 else 0,
                "ct_content_quiz_2": 1 if d.get("ct_content_quiz_2", 1) == 2 else 0,
                "ct_content_quiz_3": 1 if d.get("ct_content_quiz_3", 1) == 1 else 0,
                "ct_content_quiz_4": 0 if d.get("ct_content_quiz_4_4", 0) > 0
                                           else (d.get("ct_content_quiz_4_1", 0)
                                                 +d.get("ct_content_quiz_4_2", 0)
                                                 +d.get("ct_content_quiz_4_3", 0))/3.0,
                "ct_content_quiz_5": 0 if d.get("ct_content_quiz_5_1", 0)+d.get("ct_content_quiz_5_2", 0) > 0
                                           else (d.get("ct_content_quiz_5_3", 0)
                                                 +d.get("ct_content_quiz_5_4", 0))/2.0,
                "ct_contact_quiz_2": 1 if d.get("ct_contact_quiz_2", 1) == 4 else 0,
                "ct_contact_quiz_3": 1 if d.get("ct_contact_quiz_3", 1) == 4 else 0,
                "ct_contact_quiz_4": 1 if d.get("ct_contact_quiz_4", 1) == 4 else 0,
                "ct_contact_quiz_5": 1 if d.get("ct_contact_quiz_5", 1) == 4 else 0,
                "ct_contact_quiz_6": 0 if d.get("ct_contact_quiz_6_3", 0)+d.get("ct_contact_quiz_6_4", 0) > 0
                                     else (d.get("ct_contact_quiz_6_1", 0)
                                          +d.get("ct_contact_quiz_6_2", 0))/2.0,
                "ct_ie_quiz_1": 1 if d.get("ct_ie_quiz_1", 1) == 4 else 0,
                "ct_ie_quiz_3": 1 if d.get("ct_ie_quiz_3", 1) == 2 else 0,
                "ct_ie_quiz_5": 1 if d.get("ct_ie_quiz_5", 1) == 3 else 0,
                "ct_ie_quiz_6": 1 if d.get("ct_ie_quiz_6", 1) == 2 else 0,
                "ct_ie_quiz_7": 1 if d.get("ct_ie_quiz_7", 1) == 3 else 0,
                "ct_ie_quiz_8": 1 if d.get("ct_ie_quiz_8", 1) == 4 else 0,
                "ct_ie_quiz_9": 1 if d.get("ct_ie_quiz_9", 1) == 3 else 0,
                "ct_ie_quiz_10": 0 if d.get("ct_ie_quiz_10_4", 0)+d.get("ct_ie_quiz_10_5", 0) > 0
                                     else (d.get("ct_ie_quiz_10_1", 0)
                                          +d.get("ct_ie_quiz_10_2", 0)
                                          +d.get("ct_ie_quiz_10_3", 0))/3.0,
                "ct_ie_quiz_11": 1 if d.get("ct_ie_quiz_11", 1) == 0 else 0,
                "ct_ie_quiz_12": 1 if d.get("ct_ie_quiz_12", 1) == 0 else 0,
                "ct_ie_quiz_13": 1 if d.get("ct_ie_quiz_13", 0) == 1 else 0,
                "ct_ie_quiz_14": 1 if d.get("ct_ie_quiz_14", 1) == 0 else 0,
                "ct_ie_quiz_15": 0 if d.get("ct_ie_quiz_15_2", 0)+d.get("ct_ie_quiz_15_3", 0)+d.get("ct_ie_quiz_15_4", 0) > 0
                                     else (d.get("ct_ie_quiz_15_1", 0)
                                          +d.get("ct_ie_quiz_15_5", 0))/2.0}

    @staticmethod
    def transform_contentcritique(d):
        if d.get("ct_block_a_1") == "NA":
            return {"ct_block_a_1": "NA",
                    "ct_block_a_2": "NA",
                    "ct_block_a_3": "NA",
                    "ct_block_a_4": "NA",
                    "ct_block_a_5": "NA",
                    "ct_block_a_6": "NA",
                    "ct_block_a_7": "NA",
                    "ct_block_a_8": "NA"}

        return {"ct_block_a_1": d.get("ct_block_a_1", 1),
                "ct_block_a_2": 2 if d.get("ct_block_a_2", 1) else 0,
                "ct_block_a_3": 2 if d.get("ct_block_a_3", 1) else 0,
                "ct_block_a_4": 3 if d.get("ct_block_a_4", 1) else 0,
                "ct_block_a_5": d.get("ct_block_a_5", 1),
                "ct_block_a_6": 3 if d.get("ct_block_a_6", 1) else 0,
                "ct_block_a_7": 0 if d.get("ct_block_a_7", 1) else 1,
                "ct_block_a_8": -1 if d.get("ct_block_a_8", 1) else 0}

    @staticmethod
    def transform_snsprivacy(d):
        if d.get("ct_inapp_34") == "NA":
            return {"ct_inapp_34": "NA"}

        newd = {}

        v = d.get("ct_inapp_34", 1)
        if v == 1:
            newd["ct_inapp_34"] = 0
        elif v == 2:
            newd["ct_inapp_34"] = 3
        else:
            newd["ct_inapp_34"] = 1

        return newd

    @staticmethod
    def transform_friendsbehavior(d):
        if d.get("ct_inapp_34") == "NA":
            newd = {"ct_of_chat_1": "NA",
                    "ct_ofm_beh_1": "NA"}
            for i in xrange(7):
                newd["ct_ofm_tell1_" + str(i+1)] = "NA"
            for i in xrange(7):
                newd["ct_ofm_bring_" + str(i+1)] = "NA"
            for i in xrange(7):
                newd["ct_ofm_tell2_" + str(i+1)] = "NA"
            return newd

        newd = {"ct_of_chat_1": 1 if d.get("ct_of_chat_1", 1) == 2 else 0,
                "ct_ofm_beh_1": 1 if d.get("ct_ofm_beh_1", 1) == 2 else 0}

        for i in xrange(7):
            newd["ct_ofm_tell1_" + str(i+1)] = d.get("ct_ofm_tell1_" + str(i+1), 0)
        for i in xrange(7):
            newd["ct_ofm_bring_" + str(i+1)] = d.get("ct_ofm_bring_" + str(i+1), 0)
        for i in xrange(7):
            newd["ct_ofm_tell2_" + str(i+1)] = d.get("ct_ofm_tell2_" + str(i+1), 0)

        return newd


class EmpathyDQResult(crudmgo.RootDocument):
    __collection__ = "empathydqresults"

    structure = {
        "userid": ObjectId,
        "created": {
            "by": basestring,
            "on": datetime.datetime,
            "username": basestring
        },
        "meta": {}
    }
    indexes = [
        {"fields": "created.by",
         "check": False}
    ]
    default_values = {"created.by": lambda: current_user.id, "created.on": crudmgo.localtime,
                      "created.username": lambda: current_user.get_username(), "meta": {}}

    def get_dqresult(self, user, cacheonly=False):
        if not user:
            return None

        r = self.find_one({"userid": user.id})
        if not r:
            r = self()
            r["userid"] = user.id
            if r.calc_dqscore():
                r.save()
            else:
                r = None
        elif not cacheonly:
            r.calc_dqscore()
            r.save()
        return r

    def has_dqresult(self, user):
        if not user:
            return None

        r = self.find_one({"userid": user.id})
        return r is not None

    def calc_dqscore(self, userid=None, user=None):
        if not ObjectId.is_valid(userid):
            userid = None

        if userid:
            userid = ObjectId(userid)
        elif self.get("userid") and isinstance(self["userid"], ObjectId):
            userid = self["userid"]
        else:
            return False

        cfg = {}

        d = self
        r = None
        db = self.collection.database
        model = db["SurveyDQAnswer"]

        if user is None:
            user = db["IZHero"].find_one({"_id": userid})
            if not user:
                return False

        progress = user.get("dq_progress", {})

        if current_app.config.get('R_RCMD'):
            cfg['RCMD'] = current_app.config['R_RCMD']

        try:
            survey = db["SurveyDQ"].find_one({"name": "speakup.v1"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "speakup" not in progress:
                # self.get_speakup_na(d)
                return False
            else:
                self.assign_speakup(d, survey)

            survey = model.find_one({"surveyname": "digiempathy-messenger",
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if "digiempathy" in progress:
                if not survey:
                    survey = {"answers": []}
                if not survey or not self.assign_digiempathy(d, survey):
                    return False
            else:
                # self.get_digiempathy_na(d)
                return False

            survey = model.find_one({"surveyname": "stander-messenger",
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if "stander" in progress:
                if not survey:
                    survey = {"answers": []}
                if not survey or not self.assign_stander(d, survey):
                    return False
            else:
                # self.get_stander_na(d)
                return False

            survey = db["SurveyDQ"].find_one({"name": "avoidjudging"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "avoidjudging" not in progress:
                # self.get_avoidjudging_na(d)
                return False
            else:
                self.assign_avoidjudging(d, survey)

            survey = db["SurveyDQ"].find_one({"name": "empathyfriends"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey or "empathyfriends" not in progress:
                # self.get_empathyfriends_na(d)
                return False
            else:
                self.assign_empathyfriends(d, survey)

            survey = db["SurveyDQ"].find_one({"name": "empathybadge"})
            survey = model.find_one({"surveyid": survey["_id"],
                                     "created.by": userid},
                                    sort=[("_id", pymongo.ASCENDING)])
            if not survey and "empathybadge" not in progress:
                # self.get_empathybadge_na(d)
                return False
            else:
                self.assign_empathybadge(d, survey)

            r = R(**cfg)

            for k, v in d.iteritems():
                if isinstance(v, (int, float)):
                    r.assign(k, v)
            for k, v in self.transform_avoidjudging(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_empathybadge(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_speakup(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_stander(d).iteritems():
                r.assign(k, v)
            for k, v in self.transform_empathyfriends(d).iteritems():
                r.assign(k, v)

            r(empathy.r_algo)

            self["emp_de_score"] = r.get("emp_de_score")

            p = r.prog
            r = None
            p.terminate()
        except Exception as e:
            if r and hasattr(r, "prog") and hasattr(r.prog, "terminate"):
                r.prog.terminate()
            return False

        return True

    def get_dqscores(self):
        return {
            "emp_de_score": self.get("emp_de_score", 0)
        }

    def transform_vars(self):
        d = {k: v for k, v in self.iteritems()}
        d.update(self.transform_avoidjudging(d))
        d.update(self.transform_empathybadge(d))
        d.update(self.transform_empathyfriends(d))
        d.update(self.transform_speakup(d))
        d.update(self.transform_stander(d))
        return d

    @staticmethod
    def get_speakup_na(d):
        d["emp_emp_b_3"] = "NA"
        d["emp_gr"] = "NA"
        d["emp_emp_4"] = "NA"
        d["emp_emp_1"] = "NA"
        d["emp_emp_2"] = "NA"

    @staticmethod
    def assign_speakup(d, survey):
        d["emp_emp_b_3"] = 1
        d["emp_gr"] = 1
        d["emp_emp_4"] = 1
        d["emp_emp_1"] = 1
        d["emp_emp_2"] = 1

        for i in survey["answers"]:
            if i["no"] == 0:
                d["emp_emp_b_3"] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 1:
                d["emp_gr"] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 4:
                d["emp_emp_4"] = int(i.get("ansval") or 0) + 1
            elif 2 <= i["no"] <= 3:
                d["emp_emp_" + str(i["no"]-1)] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_digiempathy_na(d):
        d["emp_emp_5"] = "NA"
        d["emp_emp_6"] = "NA"
        d["emp_emp_7"] = "NA"
        d["emp_emp_8"] = "NA"

    @staticmethod
    def assign_digiempathy(d, survey):
        d["emp_emp_5"] = 1
        d["emp_emp_6"] = 1
        d["emp_emp_7"] = 1
        d["emp_emp_8"] = 1

        for i in survey["answers"]:
            if i["qns"] == "feelthesame":
                d["emp_emp_5"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "stopfight":
                d["emp_emp_6"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "botherme":
                d["emp_emp_7"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "behappy":
                d["emp_emp_8"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_stander_na(d):
        d["emp_emp_b_1"] = "NA"
        d["emp_emp_b_2"] = "NA"

    @staticmethod
    def assign_stander(d, survey):
        d["emp_emp_b_1"] = 2
        d["emp_emp_b_2"] = 1

        for i in survey["answers"]:
            if i["qns"] == "jjleft":
                d["emp_emp_b_1"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "lufeel":
                d["emp_emp_b_2"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_avoidjudging_na(d):
        d["emp_om"] = "NA"

    @staticmethod
    def assign_avoidjudging(d, survey):
        d["emp_om"] = 1

        for i in survey["answers"]:
            if i["no"] == 0:
                d["emp_om"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_empathyfriends_na(d):
        d["cb_up_1"] = "NA"
        d["cb_up_2"] = "NA"

    @staticmethod
    def assign_empathyfriends(d, survey):
        d["cb_up_1"] = 2
        d["cb_up_2"] = 2

        for i in survey["answers"]:
            if 0 <= i["no"] <= 1:
                d["cb_up_" + str(i["no"]+1)] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_empathybadge_na(d):
        d["emp_quiz_1"] = "NA"
        d["emp_quiz_2"] = "NA"
        for x in xrange(11):
            d["emp_quiz_" + str(x + 5)] = "NA"

    @staticmethod
    def assign_empathybadge(d, survey):
        d["emp_quiz_1"] = 1
        d["emp_quiz_2"] = 1
        for x in xrange(11):
            d["emp_quiz_" + str(x + 5)] = 1

        for i in survey["answers"]:
            if 0 <= i["no"] <= 1:
                d["emp_quiz_" + str(i["no"]+1)] = int(i.get("ansval") or 0) + 1
            elif 2 <= i["no"] <= 12:
                d["emp_quiz_" + str(i["no"]+3)] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def transform_stander(d):
        if d.get("emp_emp_b_1") == "NA":
            return {"emp_emp_b_1": "NA",
                    "emp_emp_b_2": "NA"}

        newd = {}
        x = d.get("emp_emp_b_1", 1)
        if x == 2:
            newd["emp_emp_b_1"] = 3
        elif x == 3:
            newd["emp_emp_b_1"] = 2
        else:
            newd["emp_emp_b_1"] = x

        x = d.get("emp_emp_b_2", 1)
        if x == 1:
            newd["emp_emp_b_2"] = 3
        elif x == 3:
            newd["emp_emp_b_2"] = 2
        elif x == 2:
            newd["emp_emp_b_2"] = 1
        return newd

    @staticmethod
    def transform_speakup(d):
        if d.get("emp_emp_b_3") == "NA":
            return {
                "emp_emp_b_3": "NA",
                "emp_gr": "NA",
                "emp_emp_4": "NA",
                "emp_emp": "NA"
            }

        newd = {
            "emp_emp_b_3": d.get("emp_emp_b_3", 1),
            "emp_gr": 5-d.get("emp_gr", 1),
            "emp_emp_4": d.get("emp_emp_4", 1),
            "emp_emp": d.get("emp_emp", 1)
        }

        if newd["emp_emp_b_3"] == 1:
            newd["emp_emp_b_3"] = 3
        elif newd["emp_emp_b_3"] == 3:
            newd["emp_emp_b_3"] = 1

        return newd

    @staticmethod
    def transform_avoidjudging(d):
        if d.get("emp_om") == "NA":
            return {"emp_om": "NA"}

        newd = {
            "emp_om": d.get("emp_om", 1)
        }

        if newd["emp_om"] == 2:
            newd["emp_om"] = 3
        elif newd["emp_om"] == 3:
            newd["emp_om"] = 2
        else:
            newd["emp_om"] = 1

        return newd

    @staticmethod
    def transform_empathyfriends(d):
        if d.get("cb_up_1") == "NA":
            return {
                "cb_up_1": "NA",
                "cb_up_2": "NA"
            }

        newd = {
            "cb_up_1": d.get("cb_up_1", 1),
            "cb_up_2": d.get("cb_up_2", 1)
        }

        if newd["cb_up_1"] == 2:
            newd["cb_up_1"] = 5

        if newd["cb_up_2"] == 2:
            newd["cb_up_2"] = 5

        return newd

    @staticmethod
    def transform_empathybadge(d):
        if d.get("emp_quiz_1") == "NA":
            return {
                "emp_quiz_1": "NA",
                "emp_quiz_2": "NA",
                "emp_quiz_5": "NA",
                "emp_quiz_6": "NA",
                "emp_quiz_7": "NA",
                "emp_quiz_8": "NA",
                "emp_quiz_9": "NA",
                "emp_quiz_10": "NA",
                "emp_quiz_11": "NA",
                "emp_quiz_12": "NA",
                "emp_quiz_13": "NA",
                "emp_quiz_14": "NA",
                "emp_quiz_15": "NA"
            }

        return {
            "emp_quiz_1": 1 if d.get("emp_quiz_1", 0) == 2 else 0,
            "emp_quiz_2": 1 if d.get("emp_quiz_2", 0) == 1 else 0,
            "emp_quiz_5": 1 if d.get("emp_quiz_5", 0) == 2 else 0,
            "emp_quiz_6": 1 if d.get("emp_quiz_6", 0) == 2 else 0,
            "emp_quiz_7": 1 if d.get("emp_quiz_7", 0) == 2 else 0,
            "emp_quiz_8": 1 if d.get("emp_quiz_8", 0) == 3 else 0,
            "emp_quiz_9": 1 if d.get("emp_quiz_9", 0) == 3 else 0,
            "emp_quiz_10": 1 if d.get("emp_quiz_10", 0) == 4 else 0,
            "emp_quiz_11": 1 if d.get("emp_quiz_11", 0) == 1 else 0,
            "emp_quiz_12": 1 if d.get("emp_quiz_12", 0) == 2 else 0,
            "emp_quiz_13": 1 if d.get("emp_quiz_13", 0) == 2 else 0,
            "emp_quiz_14": 1 if d.get("emp_quiz_14", 0) == 2 else 0,
            "emp_quiz_15": 1 if d.get("emp_quiz_15", 0) == 4 else 0
        }


class RiskEnvPersonalDQResult(crudmgo.RootDocument):
    __collection__ = "riskenvpersonaldqresults"

    structure = {
        "userid": ObjectId,
        "created": {
            "by": basestring,
            "on": datetime.datetime,
            "username": basestring
        },
        "meta": {}
    }
    indexes = [
        {"fields": "created.by",
         "check": False}
    ]
    default_values = {"created.by": lambda: current_user.id, "created.on": crudmgo.localtime,
                      "created.username": lambda: current_user.get_username(), "meta": {}}

    def get_dqresult(self, user, cacheonly=False):
        if not user:
            return None

        r = self.find_one({"userid": user.id})
        if not r:
            r = self()
            r["userid"] = user.id
            if r.calc_dqscore():
                r.save()
            else:
                r = None
        elif not cacheonly:
            r.calc_dqscore()
            r.save()
        return r

    def calc_dqscore(self, userid=None, user=None):
        if not ObjectId.is_valid(userid):
            userid = None

        if userid:
            userid = ObjectId(userid)
        elif self.get("userid") and isinstance(self["userid"], ObjectId):
            userid = self["userid"]
        else:
            return False

        d = self
        db = self.collection.database
        model = db["SurveyDQAnswer"]

        if user is None:
            user = db["IZHero"].find_one({"_id": userid})
            if not user:
                return False

        progress = user.get("dq_progress", {})

        survey = db["SurveyDQ"].find_one({"name": "dealbully.v2"})
        survey = model.find_one({"surveyid": survey["_id"],
                                 "created.by": userid},
                                sort=[("_id", pymongo.ASCENDING)])
        if not survey or "dealbully" not in progress:
            # self.get_dealbully_na(d)
            # self.get_dealbully_messenger_na(d)
            return False
        else:
            self.assign_dealbully(d, survey)

        survey = model.find_one({"surveyname": "dealbully-messenger",
                                 "created.by": userid},
                                sort=[("_id", pymongo.ASCENDING)])
        if "dealbully" in progress:
            if not survey:
                survey = {"answers": []}
            if not self.assign_dealbully_messenger(d, survey):
                return False

        survey = model.find_one({"surveyname": "avoidjudging-messenger",
                                 "created.by": userid},
                                sort=[("_id", pymongo.ASCENDING)])
        if "avoidjudging" in progress:
            if not survey:
                survey = {"answers": []}
            if not self.assign_avoidjudging_messenger(d, survey):
                return False
        else:
            # self.get_avoidjudging_messenger_na(d)
            return False

        survey = model.find_one({"surveyname": "messenger-messenger",
                                 "created.by": userid},
                                sort=[("_id", pymongo.ASCENDING)])
        if not survey:
            survey = {"answers": []}
        if not survey or not self.assign_digiworld_messenger(d, survey):
            return False

        survey = db["SurveyDQ"].find_one({"name": "gameaddict"})
        survey = model.find_one({"surveyid": survey["_id"],
                                 "created.by": userid},
                                sort=[("_id", pymongo.ASCENDING)])
        if not survey or "gameaddict" not in progress:
            # self.get_gameaddict_na(d)
            return False
        else:
            self.assign_gameaddict(d, survey)

        survey = db["SurveyDQ"].find_one({"name": "inapprocontent"})
        survey = model.find_one({"surveyid": survey["_id"],
                                 "created.by": userid},
                                sort=[("_id", pymongo.ASCENDING)])
        if not survey or "inapprocontent" not in progress:
            # self.get_inapprocontent_na(d)
            return False
        else:
            self.assign_inapprocontent(d, survey)

        survey = model.find_one({"surveyname": "mediarules-messenger",
                                 "created.by": userid},
                                sort=[("_id", pymongo.ASCENDING)])
        if "mediarules" in progress:
            if not survey:
                survey = {"answers": []}
            if not survey or not self.assign_mediarules_messenger(d, survey):
                return False
        else:
            # self.get_mediarules_messenger_na(d)
            return False

        survey = db["SurveyDQ"].find_one({"name": "onlinefriends"})
        survey = model.find_one({"surveyid": survey["_id"],
                                 "created.by": userid},
                                sort=[("_id", pymongo.ASCENDING)])
        if not survey or "onlinefriends" not in progress:
            # self.get_onlinefriends_na(d)
            return False
        else:
            self.assign_onlinefriends(d, survey)

        survey = db["SurveyDQ"].find_one({"name": "onoffline.v1"})
        survey = model.find_one({"surveyid": survey["_id"],
                                 "created.by": userid},
                                sort=[("_id", pymongo.ASCENDING)])
        if not survey or "onoffline" not in progress:
            # self.get_onoffline_na(d)
            return False
        else:
            self.assign_onoffline(d, survey)

        survey = db["SurveyDQ"].find_one({"name": "snsprivacy.v2"})
        survey = model.find_one({"surveyid": survey["_id"],
                                 "created.by": userid},
                                sort=[("_id", pymongo.ASCENDING)])
        if not survey or "snsprivacy" not in progress:
            # self.get_snsprivacy_na(d)
            return False
        else:
            self.assign_snsprivacy(d, survey)

        survey = model.find_one({"surveyname": "protectinfo-messenger",
                                 "created.by": userid},
                                sort=[("_id", pymongo.ASCENDING)])
        if "protectinfo" in progress:
            if not survey:
                survey = {"answers": []}
            if not survey or not self.assign_protectinfo_messenger(d, survey):
                return False
        else:
            # self.get_protectinfo_messenger_na(d)
            return False

        survey = model.find_one({"surveyname": "selfcontrol-messenger",
                                 "created.by": userid},
                                sort=[("_id", pymongo.ASCENDING)])
        if "selfcontrol" in progress:
            if not survey:
                survey = {"answers": []}
            if not survey or not self.assign_selfcontrol_messenger(d, survey):
                return False
        else:
            # self.get_selfcontrol_messenger_na(d)
            return False

        survey = model.find_one({"surveyname": "strength-messenger",
                                 "created.by": userid},
                                sort=[("_id", pymongo.ASCENDING)])
        if "strength" in progress:
            if not survey:
                survey = {"answers": []}
            if not survey or not self.assign_strength_messenger(d, survey):
                return False
        else:
            # self.get_strength_messenger_na(d)
            return False

        survey = db["SurveyDQ"].find_one({"name": "trustedadults"})
        survey = model.find_one({"surveyid": survey["_id"],
                                 "created.by": userid},
                                sort=[("_id", pymongo.ASCENDING)])
        if not survey or "trustedadults" not in progress:
            # self.get_trustedadults_na(d)
            return False
        else:
            self.assign_trustedadults(d, survey)

        survey = model.find_one({"surveyname": "empathyfriends-messenger",
                                 "created.by": userid},
                                sort=[("_id", pymongo.ASCENDING)])
        if "empathyfriends" in progress:
            if not survey:
                survey = {"answers": []}
            if not survey or not self.assign_empathyfriends_messenger(d, survey):
                return False
        else:
            # self.get_empathyfriends_messenger_na(d)
            return False

        return True

    def transform_vars(self):
        d = {k: v for k, v in self.iteritems()}
        d.update(self.transform_gameaddict(d))
        d.update(self.transform_avoidjudging(d))
        d.update(self.transform_dealbully(d))
        d.update(self.transform_inapprocontent(d))
        d.update(self.transform_trustedadults(d))
        return d

    @staticmethod
    def get_inapprocontent_na(d):
        d["ct_inapp_a"] = "NA"

    @staticmethod
    def assign_inapprocontent(d, survey):
        d["ct_inapp_a"] = 1
        for i in survey["answers"]:
            if i["no"] == 0:
                d["ct_inapp_a"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_dealbully_na(d):
        for x in xrange(9):
            d["cb_cvbeh_" + str(x + 1)] = "NA"

    @staticmethod
    def assign_dealbully(d, survey):
        for x in xrange(9):
            d["cb_cvbeh_" + str(x + 1)] = 1

        for i in survey["answers"]:
            if 0 <= i["no"] <= 8:
                d["cb_cvbeh_" + str(i["no"] + 1)] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_dealbully_messenger_na(d):
        d["cb_cv_offline"] = "NA"
        d["cb_cv_help"] = "NA"
        d["cb_cv_tell"] = "NA"

    @staticmethod
    def assign_dealbully_messenger(d, survey):
        defval = 0
        for x in xrange(9):
            if d.get("cb_cvbeh_" + str(x + 1), 0) > 1:
                defval = 1
                break
        d["cb_cv_offline"] = 4 if defval else 0
        d["cb_cv_help"] = defval
        d["cb_cv_tell"] = defval

        if survey:
            for i in survey["answers"]:
                if i["qns"] == "bullyoffline":
                    d["cb_cv_offline"] = 4 - int(i.get("ansval") or 0)
                elif i["qns"] == "givesupport":
                    d["cb_cv_help"] = 1 - int(i.get("ansval") or 0)
                elif i["qns"] == "telladult":
                    d["cb_cv_tell"] = int(i.get("ansval") or 0) + 1
            if d["cb_cv_tell"] != 4:
                d["cb_cv_help"] = 0
        return True

    @staticmethod
    def get_trustedadults_na(d):
        for x in xrange(10):
            d["cb_trust_" + str(x+1)] = "NA"

    @staticmethod
    def assign_trustedadults(d, survey):
        for x in xrange(10):
            d["cb_trust_" + str(x+1)] = 0

        for i in survey["answers"]:
            if i["no"] == 0:
                l = i["anslist"] if isinstance(i["anslist"], (tuple, list)) else ()
                name = "cb_trust_"
                for x in xrange(10):
                    d[name + str(x+1)] = 1 if x in l else 0
        return True

    @staticmethod
    def get_avoidjudging_messenger_na(d):
        d["emp_lh_1"] = "NA"
        d["emp_lh_6"] = "NA"
        d["emp_lh_2"] = "NA"
        d["emp_lh_5"] = "NA"
        d["emp_lh_4"] = "NA"

    @staticmethod
    def assign_avoidjudging_messenger(d, survey):
        d["emp_lh_1"] = 1
        d["emp_lh_6"] = 1
        d["emp_lh_2"] = 1
        d["emp_lh_5"] = 1
        d["emp_lh_4"] = 1

        for i in survey["answers"]:
            if i["qns"] == "parentsnotice":
                d["emp_lh_1"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "arguments":
                d["emp_lh_6"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "pleasantliving":
                d["emp_lh_2"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "comforthome":
                d["emp_lh_5"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "accepthome":
                d["emp_lh_4"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_selfcontrol_messenger_na(d):
        d["dc_pm_2"] = "NA"
        d["dc_pm_3"] = "NA"
        d["dc_pm_1"] = "NA"

    @staticmethod
    def assign_selfcontrol_messenger(d, survey):
        d["dc_pm_2"] = 1
        d["dc_pm_3"] = 1
        d["dc_pm_1"] = 1
        for i in survey["answers"]:
            if i["qns"] == "haverules":
                d["dc_pm_2"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "parentrules":
                d["dc_pm_3"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "managetime":
                d["dc_pm_1"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_mediarules_messenger_na(d):
        d["dc_pm_4"] = "NA"
        d["dc_pm_5"] = "NA"
        d["dc_pm_6"] = "NA"
        d["dc_pm_8"] = "NA"
        d["dc_pm_9"] = "NA"
        d["dc_pm_10"] = "NA"

    @staticmethod
    def assign_mediarules_messenger(d, survey):
        d["dc_pm_4"] = 1
        d["dc_pm_5"] = 1
        d["dc_pm_6"] = 1
        d["dc_pm_8"] = 1
        d["dc_pm_9"] = 1
        d["dc_pm_10"] = 1

        for i in survey["answers"]:
            if i["qns"] == "needtoknow":
                d["dc_pm_4"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "trustednot":
                d["dc_pm_5"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "shareonline":
                d["dc_pm_6"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "threatens":
                d["dc_pm_8"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "pcscreen":
                d["dc_pm_9"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "webapps":
                d["dc_pm_10"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_digiworld_messenger_na(d):
        d["dc_dt_edu_2"] = "NA"
        d["dc_dt_edu_1"] = "NA"

    @staticmethod
    def assign_digiworld_messenger(d, survey):
        d["dc_dt_edu_2"] = 1
        d["dc_dt_edu_1"] = 1

        for i in survey["answers"]:
            if i["qns"] == "howtouse":
                d["dc_dt_edu_2"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "netsafety":
                d["dc_dt_edu_1"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_snsprivacy_na(d):
        d["dc_dt_snsmost"] = "NA"

    @staticmethod
    def assign_snsprivacy(d, survey):
        d["dc_dt_snsmost"] = 13
        for i in survey["answers"]:
            if i["no"] == 1:
                d["dc_dt_snsmost"] = int(i["ansval"] or 0) + 1
        return True

    @staticmethod
    def get_gameaddict_na(d):
        d["dc_dt_devmost"] = "NA"
        d["bst_often_game"] = "NA"
        d["bst_long_game"] = "NA"

    @staticmethod
    def assign_gameaddict(d, survey):
        d["dc_dt_devmost"] = 0
        d["bst_often_game"] = 8
        d["bst_long_game"] = 0

        for i in survey["answers"]:
            if i["no"] == 1:
                d["dc_dt_devmost"] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 2:
                d["bst_often_game"] = int(i.get("ansval") or 0) + 1
            elif i["no"] == 3:
                d["bst_long_game"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_onlinefriends_na(d):
        d["dt_comf_4"] = "NA"

    @staticmethod
    def assign_onlinefriends(d, survey):
        d["dt_comf_4"] = 1

        for i in survey["answers"]:
            if i["no"] == 0:
                d["dt_comf_4"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_onoffline_na(d):
        d["dt_comf_1"] = "NA"
        d["dt_comf_2"] = "NA"
        d["dt_comf_3"] = "NA"

    @staticmethod
    def assign_onoffline(d, survey):
        d["dt_comf_1"] = 1
        d["dt_comf_2"] = 1
        d["dt_comf_3"] = 1

        for i in survey["answers"]:
            if i["no"] == 5:
                d["dt_comf_1"] = int(i.get("ansval") or 0) + 1
            if i["no"] == 6:
                d["dt_comf_2"] = int(i.get("ansval") or 0) + 1
            if i["no"] == 7:
                d["dt_comf_3"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_protectinfo_messenger_na(d):
        d["emp_rel_1"] = "NA"
        d["emp_rel_2"] = "NA"
        d["emp_rel_3"] = "NA"

    @staticmethod
    def assign_protectinfo_messenger(d, survey):
        d["emp_rel_1"] = 1
        d["emp_rel_2"] = 1
        d["emp_rel_3"] = 1

        for i in survey["answers"]:
            if i["qns"] == "likepeople":
                d["emp_rel_1"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "peoplecare":
                d["emp_rel_2"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "closepeople":
                d["emp_rel_3"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_strength_messenger_na(d):
        d["dc_dream_1"] = "NA"
        d["dc_dream_2"] = "NA"
        d["dc_ae_2"] = "NA"
        d["dc_ae_1"] = "NA"

    @staticmethod
    def assign_strength_messenger(d, survey):
        d["dc_dream_1"] = 1
        d["dc_dream_2"] = 1
        d["dc_ae_2"] = 1
        d["dc_ae_1"] = 1

        for i in survey["answers"]:
            if i["qns"] == "destiny":
                d["dc_dream_1"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "dream":
                d["dc_dream_2"] = int(i.get("ansval") or 0) + 1
            if i["qns"] == "grade":
                d["dc_ae_2"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "succeed":
                d["dc_ae_1"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def get_empathyfriends_messenger_na(d):
        d["emp_er_1"] = "NA"
        d["emp_er_2"] = "NA"
        d["emp_er_3"] = "NA"

    @staticmethod
    def assign_empathyfriends_messenger(d, survey):
        d["emp_er_1"] = 1
        d["emp_er_2"] = 1
        d["emp_er_3"] = 1

        for i in survey["answers"]:
            if i["qns"] == "dealstress":
                d["emp_er_1"] = int(i.get("ansval") or 0) + 1
            elif i["qns"] == "calmdown":
                d["emp_er_2"] = int(i.get("ansval") or 0) + 1
            if i["qns"] == "dealsadness":
                d["emp_er_3"] = int(i.get("ansval") or 0) + 1
        return True

    @staticmethod
    def transform_inapprocontent(d):
        if d.get("ct_inapp_a") == "NA":
            return {"ct_inapp_a": "NA"}

        return {
            "ct_inapp_a": 6-d.get("ct_inapp_a", 1)
        }

    @staticmethod
    def transform_dealbully(d):
        if d.get("cb_cv_help") == "NA":
            return {"cb_cv_help": "NA",
                    "cb_cvbeh_1": "NA",
                    "cb_cvbeh_2": "NA",
                    "cb_cvbeh_3": "NA",
                    "cb_cvbeh_4": "NA",
                    "cb_cvbeh_5": "NA",
                    "cb_cvbeh_6": "NA",
                    "cb_cvbeh_7": "NA",
                    "cb_cvbeh_8": "NA",
                    "cb_cvbeh_9": "NA"}

        newd = {
            "cb_cv_help": 1-d.get("cb_cv_help", 0)
        }
        for i in xrange(9):
            v = d.get("cb_cvbeh_" + str(i+1), 1)
            y = 0
            if v == 2:
                y = 1.5
            elif v == 3:
                y = 5
            elif v == 4:
                y = 50
            elif v == 5:
                y = 100
            newd["cb_cvbeh_" + str(i+1)] = y
        return newd

    @staticmethod
    def transform_trustedadults(d):
        if d.get("cb_trust_1") == "NA":
            return {
                "cb_trust_1": "NA",
                "cb_trust_2": "NA",
                "cb_trust_3": "NA",
                "cb_trust_4": "NA",
                "cb_trust_5": "NA",
                "cb_trust_6": "NA",
                "cb_trust_7": "NA",
                "cb_trust_8": "NA",
                "cb_trust_9": "NA",
                "cb_trust_10": "NA"
            }

        return {
            "cb_trust_1": d.get("cb_trust_1", 0) and 5,
            "cb_trust_2": d.get("cb_trust_2", 0) and 5,
            "cb_trust_3": d.get("cb_trust_3", 0) and 4,
            "cb_trust_4": d.get("cb_trust_4", 0) and 3,
            "cb_trust_5": d.get("cb_trust_5", 0) and 4,
            "cb_trust_6": d.get("cb_trust_6", 0) and 3,
            "cb_trust_7": d.get("cb_trust_7", 0) and 3,
            "cb_trust_8": d.get("cb_trust_8", 0) and 2,
            "cb_trust_9": d.get("cb_trust_9", 0),
            "cb_trust_10": d.get("cb_trust_10", 0)
        }

    @staticmethod
    def transform_avoidjudging(d):
        if d.get("emp_lh_1") == "NA":
            return {
                "emp_lh_1": "NA",
                "emp_lh_6": "NA",
                "emp_lh_2": "NA",
                "emp_lh_5": "NA",
                "emp_lh_4": "NA"
            }

        return {
            "emp_lh_1": d.get("emp_lh_1", 9),
            "emp_lh_6": 5 - d.get("emp_lh_6", 9),
            "emp_lh_2": d.get("emp_lh_2", 9),
            "emp_lh_5": 5 - d.get("emp_lh_5", 9),
            "emp_lh_4": d.get("emp_lh_4", 9)
        }

    @staticmethod
    def transform_gameaddict(d):
        if d.get("dc_dt_devmost") == "NA":
            return {
                "dc_dt_devmost": "NA",
                "bst_often_game": "NA",
                "bst_long_game": "NA"
            }

        return {
            "dc_dt_devmost": d.get("dc_dt_devmost", 0),
            "bst_often_game": 8 - d.get("bst_often_game", 8),
            "bst_long_game": d.get("bst_long_game", 0)
        }


class DQX(crudmgo.RootDocument):
    __collection__ = "dqxresults"

    structure = {
        "userid": ObjectId,
        "username": basestring
    }
    default_values = {"userid": lambda: current_user.id, "username": lambda: current_user.get_username()}

    def make(self, user):
        if not user:
            return None

        d = self.find_one({"userid": user.id})

        if not d:
            d = self()
            d["userid"] = user.id
            d["username"] = user["username"]

            db = self.collection.database
            pd = db["PreDQResult"].get_dqresult(user)
            st = db["ScreentimeDQResult"].get_dqresult(user, True)
            pr = db["PrivacyDQResult"].get_dqresult(user, True)
            cb = db["CyberbullyingDQResult"].get_dqresult(user, True)
            dc = db["DigitalcitizensDQResult"].get_dqresult(user, True)
            df = db["DigitalfootprintDQResult"].get_dqresult(user, True)
            se = db["SecurityDQResult"].get_dqresult(user, True)
            ct = db["CriticalthinkingDQResult"].get_dqresult(user, True)
            em = db["EmpathyDQResult"].get_dqresult(user, True)
            re = db["RiskEnvPersonalDQResult"].get_dqresult(user, True)

            if pd and st and pr and cb and dc and df and se and ct and em and re:
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
                d.save()
            else:
                d = None

        return d

    def makeall(self):
        db = self.collection.database
        heroes = db["IZHero"].find({
            'dq_progress.screentimebadge': {'$exists': True},
            'dq_progress.privacybadge': {'$exists': True},
            'dq_progress.cyberbullyingbadge': {'$exists': True},
            'dq_progress.digitalcitizensbadge': {'$exists': True},
            'dq_progress.digitalfootprintbadge': {'$exists': True},
            'dq_progress.securitybadge': {'$exists': True},
            'dq_progress.criticalthinkingbadge': {'$exists': True},
            'dq_progress.empathybadge': {'$exists': True},
            'created': {'$gte': parser.parse('2016-08-23T00:00:00+0800')}})

        l = []
        for u in heroes:
            d = self.make(u)
            if d:
                l.append(d)
        return l


class DQY(crudmgo.RootDocument):
    __collection__ = "dqyresults"

    structure = {
        "userid": ObjectId,
        "username": basestring
    }
    default_values = {"userid": lambda: current_user.id, "username": lambda: current_user.get_username()}

    def make(self, user):
        if not user:
            return None

        d = self.find_one({"userid": user.id})

        if not d:
            d = self()
            d["userid"] = user.id
            d["username"] = user["username"]

            db = self.collection.database
            pd = db["PreDQResult"].get_dqresult(user)
            st = db["ScreentimeDQResult"].get_dqresult(user, True)
            pr = db["PrivacyDQResult"].get_dqresult(user, True)
            cb = db["CyberbullyingDQResult"].get_dqresult(user, True)
            dc = db["DigitalcitizensDQResult"].get_dqresult(user, True)
            df = db["DigitalfootprintDQResult"].get_dqresult(user, True)
            se = db["SecurityDQResult"].get_dqresult(user, True)
            ct = db["CriticalthinkingDQResult"].get_dqresult(user, True)
            em = db["EmpathyDQResult"].get_dqresult(user, True)
            re = db["RiskEnvPersonalDQResult"].get_dqresult(user, True)

            if pd and st and pr and cb and dc and df and se and ct and em and re:
                st = st.transform_vars()
                pr = pr.transform_vars()
                cb = cb.transform_vars()
                dc = dc.transform_vars()
                df = df.transform_vars()
                se = se.transform_vars()
                ct = ct.transform_vars()
                em = em.transform_vars()
                re = re.transform_vars()

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
                d.save()
            else:
                d = None

        return d

    def makeall(self):
        db = self.collection.database
        heroes = db["IZHero"].find({
            'dq_progress.screentimebadge': {'$exists': True},
            'dq_progress.privacybadge': {'$exists': True},
            'dq_progress.cyberbullyingbadge': {'$exists': True},
            'dq_progress.digitalcitizensbadge': {'$exists': True},
            'dq_progress.digitalfootprintbadge': {'$exists': True},
            'dq_progress.securitybadge': {'$exists': True},
            'dq_progress.criticalthinkingbadge': {'$exists': True},
            'dq_progress.empathybadge': {'$exists': True},
            'created': {'$gte': parser.parse('2016-08-23T00:00:00+0800')}})

        l = []
        for u in heroes:
            d = self.make(u)
            if d:
                l.append(d)
        return l


class DQRawScore(crudmgo.RootDocument):
    __collection__ = "dqrs"

    structure = {
        "userid": ObjectId,
        "username": basestring
    }
    default_values = {"userid": lambda: current_user.id, "username": lambda: current_user.get_username()}

    def setscore(self, user, d):
        if not user:
            return None

        i = self.find({"userid": user.id}).count()

        if i == 0:
            m = self()
            m["userid"] = user.id
            m["username"] = user.get_username()
            m.save()

        return self.collection.update({"userid": user.id}, {"$set": d}, multi=True)


pretest_rsource = """
Q1 <- 12 + as.numeric(Q1_12==1) + as.numeric(Q1_12!=1) * (rowSums(cbind(Q1_1, Q1_2, Q1_3, Q1_4, Q1_5, Q1_6, Q1_7, Q1_8, Q1_9, Q1_10, Q1_11, Q1_13))*(-1))

Q3 <- 3 + rowSums(cbind(Q3_1 * 1, Q3_2 * -1, Q3_3 * 1, Q3_4 * -1, Q3_5 * -1))

Q5_ct <- Q5_1 * 1 + Q5_2 * 2 + Q5_3 * 1

Q5_cb <- Q5_4

Q7 <- rowSums(cbind(Q7_1 * 0.5, Q7_2 * -1, Q7_3 * 2, Q7_4 * 2.5, Q7_5, Q7_6, Q7_7 * -2, Q7_8 * 2)) + 5

Q11 <- 4 - rowSums(cbind(Q11_1, Q11_2, Q11_3, Q11_4))

weight <- c( 0.4, 0.3, 0.3)
preDQ_pri <- weight[1] * Q1 / 13 + weight[2]* Q4_3 / 4 + weight[3] * (Q8 - 1) / 2

weight <- c(0.2, 0.2, 0.3, 0.3)
preDQ_df <- weight[1] * Q2_1 + weight[2] * Q2_2 + weight[3] * Q4_1 / 4 + weight[4] * Q4_5 / 4

weight_ct <- c(0.3, 0.4, 0.3)
preDQ_ct <- weight_ct[1] * Q2_3 + weight_ct[2] * Q5_ct / 4 + weight_ct[3] * Q10 / 4

weight <- c(0.5, 0.5)
preDQ_sec<- weight[1] * Q3 / 5 + weight[2] * Q6

weight <- c(0.5, 0.5)
preDQ_dc <- weight[1] * Q4_2 / 4 + weight[2] * Q4_4 / 4

weight <- c(0.5, 0.5)
preDQ_emp <- weight[1] * (Q9_1 - 1) / 3 + weight[2] * (Q9_3 - 1) / 3

weight <- c(0.6, 0.4)
preDQ_cb <- weight[1] * Q5_cb + weight[2] * Q7 / 14

weight <- c(0.1, 0.9)
preDQ_bst <- weight[1] * (Q9_2-1) / 3 + weight[2] * Q11 / 4
"""
