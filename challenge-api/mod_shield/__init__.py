# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify
from flask.ext.restful import Resource, Api, reqparse
from mod_auth import current_user, acl
from rest import crudmgo

shield_code = crudmgo.CrudMgoBlueprint("shield_code", __name__, model="ShieldCode")


@shield_code.resource
class ShieldCode(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self):
        # TODO: cache this
        success = False

        codes = self.claimed_codes()
        for shield in self.model.find({"$or": [{"expiry": None}, {"expiry": {"$gt": crudmgo.utctime()}}]}):
            if shield["code"] in codes or\
                    (shield["limits"] and shield["claimed"] and shield["limits"] <= len(shield["claimed"])):
                continue
            success = True
            break

        return jsonify(success=success)

    def post(self):
        pr = reqparse.RequestParser()
        pr.add_argument("code", type=str, store_missing=False)
        args = pr.parse_args()

        codes = self.claimed_codes()
        if args.get("code"):
            shield = self.model.find_one({"code": args["code"],
                                          "$or": [{"expiry": None}, {"expiry": {"$gt": crudmgo.utctime()}}]})
            if shield and not (shield["code"] in codes or
                               (shield["limits"] and shield["claimed"] and shield["limits"] <= len(shield["claimed"]))):
                shield.insert_user(current_user)
                coins = (shield["rewards"] and shield["rewards"].get("coins", 0)) or 0
                points = (shield["rewards"] and shield["rewards"].get("points", 0)) or 0
                current_user.add_coins_points(coins, points)
                if coins:
                    logger = self.db["CoinLog"].getlog(current_user["_id"])

                    if logger is not None:
                        logger.log_mission(coins, 0, "shield", args["code"])

                return jsonify(success=True, rewards=shield["rewards"])
        return jsonify(success=False)

    def claimed_codes(self):
        return [s["code"] for s in self.model.find({"claimed.by": current_user["_id"]})]


api_shield = Api(shield_code)
api_shield.add_resource(ShieldCode, "", endpoint="code")
api_shield.add_resource(ShieldCode, "/", endpoint="code_slash")