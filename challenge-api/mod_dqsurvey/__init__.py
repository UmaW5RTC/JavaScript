# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify
from flask.ext.restful import Resource, Api, reqparse
from mod_auth import acl, current_user
from rest import crudmgo
from bson import ObjectId
import pymongo

survey = crudmgo.CrudMgoBlueprint("dq_survey", __name__, model="SurveyDQ")
answer = crudmgo.CrudMgoBlueprint("dq_surveyans", __name__, model="SurveyDQAnswer")


@survey.resource
class Survey(crudmgo.ItemAPI):
    method_decorators = [acl.requires_login]
    db = None
    model = None
    readonly = True

    def get(self, itemid):
        data = self.model.find_one({"name": itemid})
        if data is None:
            return jsonify({})

        surveyid = data["_id"]
        data = crudmgo.model_to_json(data, is_single=True)
        pr = reqparse.RequestParser()
        pr.add_argument("missionid", type=str, store_missing=False)
        args = pr.parse_args()

        if ObjectId.is_valid(args.get("missionid", "")):
            data["count"] = self.db["SurveyDQAnswer"].find({"surveyid": surveyid,
                                                            "created.by": current_user.id,
                                                            "missionid": {"$ne": ObjectId(args["missionid"])}}).count()

        return jsonify(data)


@answer.resource
class Answer(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self, answerid=None):
        a = None
        if ObjectId.is_valid(answerid):
            answerid = ObjectId(answerid)
            a = self.model.find_one({"_id": answerid, "created.by": current_user.id})

        if a is None:
            pr = reqparse.RequestParser()
            pr.add_argument("surveyid", type=str, store_missing=False)
            pr.add_argument("missionid", type=str, store_missing=False)
            pr.add_argument("messenger", type=int, store_missing=False)
            pr.add_argument("nocreate", type=int, store_missing=False)
            args = pr.parse_args()

            surveyid = None
            missionid = None

            if args.get("messenger"):
                args["surveyname"] = args["surveyid"]
            elif not ObjectId.is_valid(args.get("surveyid")):
                return jsonify({})
            else:
                surveyid = ObjectId(args["surveyid"])

            if ObjectId.is_valid(args.get("missionid")):
                missionid = ObjectId(args["missionid"])
                d = {"missionid": missionid, "created.by": current_user.id}
                if surveyid:
                    d["surveyid"] = surveyid
                else:
                    d["surveyname"] = args["surveyname"]
                a = self.model.find_one(d)
            elif args.get("messenger"):
                return jsonify(success=False)

            if a is None and not args.get("nocreate"):
                a = self.model()
                a["surveyid"] = surveyid or ObjectId()
                a["missionid"] = missionid or ObjectId()
                a["surveyname"] = args.get("surveyname")
                a["answers"] = []
                a["meta"] = {}
                if not missionid or args.get("messenger"):
                    a["meta"]["not_mission"] = True
                a.save()

        return jsonify(crudmgo.model_to_json(a, is_single=True) if a is not None else {})

    def put(self, answerid=None):
        a = None
        if ObjectId.is_valid(answerid):
            answerid = ObjectId(answerid)
            a = self.model.find_one({"_id": answerid, "created.by": current_user.id})

        pr = reqparse.RequestParser()
        pr.add_argument("surveyid", type=str, store_missing=False, ignore=True)
        pr.add_argument("missionid", type=str, store_missing=False, ignore=True)
        pr.add_argument("qid", type=str, store_missing=False, ignore=True)
        pr.add_argument("qns", type=unicode, store_missing=False, ignore=True)
        pr.add_argument("ans", type=unicode, store_missing=False, ignore=True)
        pr.add_argument("ansval", type=int, store_missing=False, ignore=True)
        pr.add_argument("anslist", type=int, store_missing=False, action='append', ignore=True)
        pr.add_argument("timeleft", type=int, store_missing=False, ignore=True)
        pr.add_argument("messenger", type=int, store_missing=False, ignore=True)
        args = pr.parse_args()

        has_qid = ObjectId.is_valid(args.get("qid"))
        has_timeleft = args.get("timeleft", -1) >= 0
        has_messenger = args.get("messenger") == 1 and args.get("qns") is not None

        if not has_qid and not has_timeleft and not has_messenger:
            return jsonify(success=False)

        if a is None:
            missionid = None
            surveyid = None

            if has_messenger:
                args["surveyname"] = args["surveyid"]
            elif not ObjectId.is_valid(args.get("surveyid")):
                return jsonify(success=False)
            else:
                surveyid = ObjectId(args["surveyid"])

            if ObjectId.is_valid(args.get("missionid")):
                missionid = ObjectId(args["missionid"])
                d = {"missionid": missionid, "created.by": current_user.id}
                if surveyid:
                    d["surveyid"] = surveyid
                else:
                    d["surveyname"] = args["surveyname"]
                a = self.model.find_one(d)
            elif args.get("messenger"):
                return jsonify(success=False)

            if a is None:
                a = self.model()
                a["surveyid"] = surveyid or ObjectId()
                a["missionid"] = missionid or ObjectId()
                a["surveyname"] = args.get("surveyname")
                a["answers"] = []
                a["meta"] = {}
                if not missionid or args.get("messenger"):
                    a["meta"]["not_mission"] = True
                if has_timeleft:
                    a["meta"]["timeleft"] = args["timeleft"]
                    has_timeleft = False
                a.save()

        success = True

        if has_qid or has_messenger:
            surveyobj = self.db["SurveyDQ"].find_one({"_id": a["surveyid"]})
            qid = ObjectId(args["qid"]) if has_qid else None
            ans = args.get("ans", "")
            ansval = args.get("ansval")
            anslist = args.get("anslist")
            update = {"$push": {"answers": {"no": -1,
                                            "qns": args.get("qns"),
                                            "qid": qid,
                                            "ans": ans,
                                            "ansval": ansval,
                                            "anslist": anslist},
                                "modified": {"by": current_user.id,
                                             "on": crudmgo.localtime()}}}
            if surveyobj is not None:
                i = 0
                position = -1
                for q in surveyobj["questions"]:
                    if q["qid"] == qid:
                        position = i
                        break
                    i += 1
                if position != -1:
                    update["$push"]["answers"]["no"] = position
                    update["$push"]["answers"] = {
                        "$each": [update["$push"]["answers"]],
                        "$sort": {"no": 1}
                    }

            if has_timeleft:
                update["$set"] = {"meta.timeleft": args["timeleft"]}

            query = {"_id": a["_id"]}
            if has_qid:
                exists = self.model.collection.find({"_id": a["_id"], "answers.qid": qid}).count()
                if exists:
                    if "$set" not in update:
                        update["$set"] = {}
                    update["$set"]["answers.$.ans"] = ans
                    update["$set"]["answers.$.ansval"] = ansval
                    update["$set"]["answers.$.anslist"] = anslist
                    del update["$push"]["answers"]
                    query["answers.qid"] = qid
                else:
                    query["answers.qid"] = {"$ne": qid}
            else:
                exists = self.model.collection.find({"_id": a["_id"], "answers.qns": args["qns"]}).count()
                if exists:
                    if "$set" not in update:
                        update["$set"] = {}
                    update["$set"]["answers.$.ans"] = ans
                    update["$set"]["answers.$.ansval"] = ansval
                    update["$set"]["answers.$.anslist"] = anslist
                    del update["$push"]["answers"]
                    query["answers.qns"] = args["qns"]
                else:
                    query["answers.qns"] = {"$ne": args["qns"]}
            res = self.model.collection.update(query, update)

            success = bool(res and res.get("nModified"))
            if success:
                a.reload()
                has_timeleft = False

        if has_timeleft:
            self.model.collection.update({"_id": a["_id"]},
                                         {"$set": {"meta.timeleft": args["timeleft"]}})
            if not isinstance(a.get("meta"), dict):
                a["meta"] = {}
            a["meta"]["timeleft"] = args["timeleft"]

        if success and not a.get("meta", {}).get("not_mission") and has_qid:
            s = self.db["SurveyDQ"].collection.find_one({"_id": a["surveyid"], "questions.qid": qid},
                                                        {"questions.$": 1, "meta": 1})
            if s is not None and "ans" in s["questions"][0]:
                q = s["questions"][0]

                if self.checkans(q, ansval, anslist):
                    if "meta" not in s or s["meta"] is None:
                        s["meta"] = {}

                    inc = {"$inc": {}}
                    coins = s["meta"].get("awardcoins", 1)
                    if coins:
                        try:
                            inc["$inc"]["meta.coins"] = int(coins)
                        except (ValueError, TypeError):
                            pass
                    points = s["meta"].get("awardpoints")
                    if points:
                        try:
                            inc["$inc"]["meta.points"] = int(points)
                        except (ValueError, TypeError):
                            pass
                    if inc["$inc"]:
                        self.db["DqUserMission"].collection.update({"_id": a["missionid"], "userid": current_user.id},
                                                                   inc)

        return jsonify(success=success, answer=crudmgo.model_to_json(a))

    def checkans(self, q, ansval, anslist):
        if q["typ"] == self.db["SurveyDQ"].QUESTION_TYPES["checkbox"]:
            if anslist and q["ans"] and len(q["ans"]) == len(anslist):
                for a in q["ans"]:
                    if a not in anslist:
                        return False
                return True
        elif q["typ"] != self.db["SurveyDQ"].QUESTION_TYPES["text"] and q["ans"] == ansval:
            return True
        return False


@answer.resource
class Result(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self, itemid=None):
        a = None
        if ObjectId.is_valid(itemid):
            itemid = ObjectId(itemid)
            a = self.model.find_one({"_id": itemid, "created.by": current_user.id})

        if a is None:
            pr = reqparse.RequestParser()
            pr.add_argument("surveyid", type=str, store_missing=False)
            pr.add_argument("surveyname", type=unicode, store_missing=False)
            args = pr.parse_args()
            sid = args.get("surveyid")
            sname = args.get("surveyname")

            if not sid and not sname:
                return jsonify({})

            if sname:
                surveyobj = self.db["SurveyDQ"].find_one({"name": sname})
                if surveyobj:
                    sid = str(surveyobj["_id"])
            if sid:
                if ObjectId.is_valid(sid):
                    a = self.model.find_one({"surveyid": ObjectId(sid),
                                             "created.by": current_user.id},
                                            sort=[("_id", pymongo.ASCENDING)])
                if not a:
                    a = self.model.find_one({"surveyname": sid,
                                             "created.by": current_user.id},
                                            sort=[("_id", pymongo.ASCENDING)])

        return jsonify(crudmgo.model_to_json(a, is_single=True) if a else {})


@answer.resource
class QuizResult(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self, quizname):
        json = {}
        surveyobj = self.db["SurveyDQ"].find_one({"name": quizname})
        if surveyobj:
            answers = self.model.find_one({"surveyid": surveyobj["_id"],
                                           "created.by": current_user.id},
                                          sort=[("_id", pymongo.ASCENDING)])

            if answers:
                json = crudmgo.model_to_json(answers, is_single=True)
                score = 0
                i = 0
                incorrect = []
                incorrect_qid = []

                for q in surveyobj["questions"]:
                    if "ans" not in q or q["ans"] is None:
                        continue

                    ans = None
                    if i in answers["answers"] and answers["answers"][i]["qid"] == q["qid"]:
                        ans = answers["answers"][i]
                    else:
                        for a in answers["answers"]:
                            if a["qid"] == q["qid"]:
                                ans = a
                                break

                    if ans is None:
                        incorrect.append(i)
                        incorrect_qid.append(q["qid"])
                    elif q["typ"] == self.db["SurveyDQ"].QUESTION_TYPES["checkbox"]:
                        if q["ans"] and ans["anslist"] and len(q["ans"]) == len(ans["anslist"]):
                            for a in q["ans"]:
                                if a not in ans["anslist"]:
                                    incorrect.append(i)
                                    incorrect_qid.append(q["qid"])
                                    break
                            else:
                                score += 1
                        else:
                            incorrect.append(i)
                            incorrect_qid.append(q["qid"])
                    elif q["typ"] != self.db["SurveyDQ"].QUESTION_TYPES["text"]:
                        if ans["ansval"] == q["ans"]:
                            score += 1
                        else:
                            incorrect.append(i)
                            incorrect_qid.append(q["qid"])
                    i += 1

                qr = self.db["QuizResult"].find_one({"surveyid": surveyobj["_id"],
                                                     "created.by": current_user.id})
                if not qr:
                    qr = self.db["QuizResult"]()
                    qr["surveyid"] = surveyobj["_id"]
                    qr["incorrect"] = incorrect
                    qr["incorrect_qid"] = incorrect_qid
                    qr["score"] = score
                    qr.save()

                elif qr["incorrect_qid"] != incorrect_qid or qr["score"] != score:
                    qr["incorrect"] = incorrect
                    qr["incorrect_qid"] = incorrect_qid
                    qr["score"] = score
                    qr.save()

                json["quizresult"] = crudmgo.model_to_json(qr, is_single=True)
                lt = self.db["QuizResult"].find({"surveyid": surveyobj["_id"], "score": {"$lt": qr["score"]}}).count()
                total = self.db["QuizResult"].find({"surveyid": surveyobj["_id"]}).count()
                if total == 1:
                    json["compare"] = 1.0
                elif lt == 0:
                    json["compare"] = 0.0
                else:
                    json["compare"] = lt / (total - 1.0)
        return jsonify(json)


api_dqsurvey = Api(survey)
api_dqanswer = Api(answer)
api_dqsurvey.add_resource(Survey, "/<itemid>", endpoint="dqsurvey")
api_dqanswer.add_resource(Answer, "", endpoint="dqanswer")
api_dqanswer.add_resource(Answer, "/", endpoint="slash_dqanswer")
api_dqanswer.add_resource(Answer, "/<answerid>", endpoint="dqanswer_id")
api_dqanswer.add_resource(Result, "/result/item", endpoint="dqanswer_result")
api_dqanswer.add_resource(Result, "/result/item/<itemid>", endpoint="dqanswer_result_id")
api_dqanswer.add_resource(QuizResult, "/quizresult/<quizname>", endpoint="dqanswer_quizresult")
