# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify, abort
from flask.ext.restful import Resource, Api, reqparse
from model import stage
from mod_auth import current_user, acl
from rest import crudmgo
from bson import ObjectId

stage_progress = crudmgo.CrudMgoBlueprint("stage_progress", __name__, model="IZHero")


def mock_dq_progress(user):
    if not user["progress"] or len(user["progress"]) < 8:
        user["progress"] = [{} for _ in xrange(8)]
    if not user["progress"][0].get("dq"):
        user["progress"][0]["dq"] = {}

    pr = reqparse.RequestParser()
    pr.add_argument("mission", type=int, store_missing=False)
    pr.add_argument("answers", type=int, store_missing=False, action='append')
    args = pr.parse_args()
    mission = args.get("mission", 0)
    answers = args.get("answers", [])

    if mission <= 0 or mission > 5:
        return jsonify(success=False)
    points = 0
    coins = 0
    timenow = crudmgo.utctime()
    mission = str(mission)

    if mission not in user["progress"][0]["dq"]:
        points = 50
        if mission == '2' and isinstance(answers, (list, tuple)):
            ans = [2, 0, 0, 2, 2, 3, 0]
            for i in xrange(0, len(answers[:len(ans)])):
                if ans[i] == answers[i]:
                    coins += 1
        user["progress"][0]["dq"][mission] = {"first": timenow,
                                              "last": None,
                                              "hits": 0}

    user["progress"][0]["dq"][mission]["last"] = timenow
    user["progress"][0]["dq"][mission]["hits"] += 1
    user["points"] = user["points"] + points if user.get("points") else points
    user["coins"] = user["coins"] + coins if user.get("coins") else coins
    user.save()
    return jsonify(success=True, points=points, coins=coins)


@stage_progress.resource
class StageZero(Resource):
    progression = ["intro_video", "star", "raz", "comic", "justlove", "dq"]
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self, name):
        name = name.lower()
        if name not in self.progression:
            abort(404)
        return jsonify(success=True, progress=crudmgo.to_flat_value(current_user["progress"]))

    def post(self, name):
        name = name.lower()
        if name not in self.progression:
            abort(404)

        user = current_user._get_current_object()
        # -start mock dq progress
        if name == "dq":
            return mock_dq_progress(user)
        # -end mock dq progress
        if not user["progress"] or len(user["progress"]) < 8:
            user["progress"] = [{} for _ in xrange(8)]
        if not user["progress"][0].get(name):
            user["progress"][0][name] = crudmgo.utctime()
        user.save()
        return jsonify(success=True, progress=crudmgo.to_flat_value(user["progress"]))


class StageTwo(Resource):
    progression = {"three": 1000, "sense": 100}
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def post(self, name):
        name = name.lower()
        if name not in self.progression:
            abort(404)

        user = current_user._get_current_object()

        if name != "sense":
            timenow = crudmgo.utctime()
            if not user["progress"] or len(user["progress"]) < 8:
                user["progress"] = [{} for _ in xrange(8)]
            if not user["progress"][2].get(name):
                user["progress"][2][name] = {"first": timenow,
                                             "last": None,
                                             "hits": 0}
            user["progress"][2][name]["last"] = timenow
            user["progress"][2][name]["hits"] += 1
            user.save()
            stage.StageTwo.update_progress(user)

        pr = reqparse.RequestParser()
        pr.add_argument("points", type=int, store_missing=False)
        args = pr.parse_args()
        points = args.get("points", 0)

        if points and points <= self.progression[name]:
            if "points_stage" not in user or not user["points_stage"]:
                user["points_stage"] = {"e0": 0, "e1": 0, "e2": 0, "e3": 0, "e4": 0, "e5": 0, "e6": 0, "e7": 0}
            if "e2" not in user["points_stage"] or not user["points_stage"]["e2"]:
                user["points_stage"]["e2"] = points
            else:
                user["points_stage"]["e2"] += points
            user.save()
            user.add_points(points)

        return jsonify(success=True, progress=crudmgo.to_flat_value(user["progress"]))


class StageThree(Resource):
    progression = {"discipline": 1000, "time": 1000}
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def post(self, name):
        name = name.lower()
        if name not in self.progression:
            abort(404)

        user = current_user._get_current_object()

        pr = reqparse.RequestParser()
        pr.add_argument("points", type=int, store_missing=False)
        args = pr.parse_args()
        points = args.get("points", 0)

        if points and points <= self.progression[name]:
            if "points_stage" not in user or not user["points_stage"]:
                user["points_stage"] = {"e0": 0, "e1": 0, "e2": 0, "e3": 0, "e4": 0, "e5": 0, "e6": 0, "e7": 0}
            if "e2" not in user["points_stage"] or not user["points_stage"]["e3"]:
                user["points_stage"]["e3"] = points
            else:
                user["points_stage"]["e3"] += points
            user.save()
            user.add_points(points)

        return jsonify(success=True, progress=crudmgo.to_flat_value(user["progress"]))


@stage_progress.resource
class StageECounsel(Resource):
    progression = {"ctrl": (100, 1), "post": (100, 1)}
    db = None
    model = None

    def post(self, name):
        name = name.lower()
        if name not in self.progression:
            abort(404)

        pr = reqparse.RequestParser()
        pr.add_argument("_id", type=str, store_missing=False)
        pr.add_argument("id", type=str, store_missing=False)
        pr.add_argument("username", type=unicode, store_missing=False)
        args = pr.parse_args()
        userid = args.get("_id") or args.get("id")

        if userid or args.get("username"):
            user = self.model.find_one({"_id": ObjectId(userid)}
                                       if userid else {"username": args["username"].lower()})
            if user:
                user.add_coins_points(self.progress[name][1], self.progress[name][0])
                return jsonify(success=True, rewards={"points": self.progress[name][0], "coins": self.progress[name][1]})

        return jsonify(success=False)


@stage_progress.resource
class StageAll(Resource):
    db = None
    model = None

    def post(self):
        pr = reqparse.RequestParser()
        pr.add_argument("stage", type=int, store_missing=False)
        pr.add_argument("mission", type=str, store_missing=False)
        pr.add_argument("sub_mission", type=str, store_missing=False)
        args = pr.parse_args()
        s, mission, sub = args.get("stage"), args.get("mission"), args.get("sub_mission")

        allstages = {
            1: stage.StageOne,
            2: stage.StageTwo,
            3: stage.StageThree,
            4: stage.StageFour,
            5: stage.StageFive,
            6: stage.StageSix,
            7: stage.StageSeven,
        }

        if s not in allstages or not mission:
            return jsonify(success=False)

        points, coins = allstages[s].post(mission, sub)
        user = current_user._get_current_object()

        if "points_stage" not in user or not user["points_stage"]:
            user["points_stage"] = {"e0": 0, "e1": 0, "e2": 0, "e3": 0, "e4": 0, "e5": 0, "e6": 0, "e7": 0}
        if "coins_stage" not in user or not user["coins_stage"]:
            user["coins_stage"] = {"e0": 0, "e1": 0, "e2": 0, "e3": 0, "e4": 0, "e5": 0, "e6": 0, "e7": 0}

        if 0 <= s <= 7:
            stage_key = "e"+str(s)
            if stage_key not in user["coins_stage"] or not user["coins_stage"][stage_key]:
                user["coins_stage"][stage_key] = coins
            else:
                user["coins_stage"][stage_key] += coins

            if stage_key not in user["points_stage"] or not user["points_stage"][stage_key]:
                user["points_stage"][stage_key] = points
            else:
                user["points_stage"][stage_key] += points

        user["coins"] = user["coins"] + coins if user.get("coins") else coins
        user["points"] = user["points"] + points if user.get("points") else points

        user.save()
        return jsonify(success=True, points=points, coins=coins)


api_stagezero = Api(stage_progress)
api_stagezero.add_resource(StageAll, "", endpoint="all")
api_stagezero.add_resource(StageAll, "/", endpoint="all_slash")
api_stagezero.add_resource(StageZero, "/0/<name>", endpoint="zero")
api_stagezero.add_resource(StageTwo, "/2/<name>", endpoint="two")
api_stagezero.add_resource(StageThree, "/3/<name>", endpoint="three")
api_stagezero.add_resource(StageECounsel, "/ecounsel/<name>", endpoint="ecounsel")