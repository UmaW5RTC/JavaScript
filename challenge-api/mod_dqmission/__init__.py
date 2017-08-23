# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify
from flask.ext.restful import Resource, Api, reqparse
from mod_auth import current_user, acl
from rest import crudmgo
from bson import ObjectId

MISSION_POINTS = 10
_GAMES_MISSION = ["priorities"]
dqmission_progress = crudmgo.CrudMgoBlueprint("dqmission_progress", __name__, model="DqUserMission")


@dqmission_progress.resource
class Mission(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self, name):
        mission = self._get(name)
        if mission is None:
            return jsonify(mission=None)
        return jsonify(mission=crudmgo.model_to_json(mission))

    def post(self, name):
        name = name.lower()
        mission = self.model.start_mission(name)
        if not mission:
            return jsonify(mission=None)
        return jsonify(mission=crudmgo.model_to_json(mission))

    def put(self, name):
        mission = self._get(name)
        if mission is None:
            return jsonify(mission=None)

        pr = reqparse.RequestParser()
        pr.add_argument("checkpoint", type=unicode, store_missing=False)
        pr.add_argument("gamescore", type=int, store_missing=False)
        pr.add_argument("cfmclose", type=int, store_missing=False)
        args = pr.parse_args()
        checkpoint = args.get("checkpoint")

        if checkpoint:
            mission.add_checkpoint(checkpoint)
        if mission["mission"] in _GAMES_MISSION and args.get("gamescore"):
            if args["gamescore"] > 150:
                args["gamescore"] = 150
            mission.set_meta("points", args["gamescore"])
        if args.get("cfmclose"):
            mission.set_meta("shownclose", True)

        return jsonify(mission=crudmgo.model_to_json(mission))

    def delete(self, name):
        mission = self._get(name)
        if mission is None:
            return jsonify(mission=None)

        status = mission.complete()
        points = 0
        coins = 0

        if status == 1 and mission["mission"] not in ("messenger",):
            coins = mission.meta("coins", 0)
            points = MISSION_POINTS + mission.meta("points", 0)
            current_user.add_dq_coins_points(coins, points, mission["mission"])

        current_user.update_dq_progress(mission["mission"])
        return jsonify(mission=crudmgo.model_to_json(mission), points=points, coins=coins)

    def _get(self, name):
        if not ObjectId.is_valid(name):
            return None

        return self.model.find_one({"_id": ObjectId(name), "userid": current_user.id})


@dqmission_progress.resource
class MissionMood(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def post(self, itemid):
        pr = reqparse.RequestParser()
        pr.add_argument("like", type=int, store_missing=False)
        args = pr.parse_args()

        if args.get("like") is None or not ObjectId.is_valid(itemid):
            return jsonify(success=False)

        m = self.model.find_one({"_id": ObjectId(itemid), "userid": current_user.id})
        if not m or m.meta("like") is not None:
            return jsonify(success=False)

        m.like() if args["like"] == 1 else m.dislike()
        return jsonify(success=True)


api_stagedq = Api(dqmission_progress)
api_stagedq.add_resource(Mission, "/<name>", endpoint="mission")
api_stagedq.add_resource(MissionMood, "/mood/<itemid>", endpoint="mood")
