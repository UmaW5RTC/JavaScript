# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify
from flask.ext.restful import Resource, Api, reqparse
from mod_auth import current_user, acl
from rest import crudmgo
import random


donate_coin = crudmgo.CrudMgoBlueprint("donate_coin", __name__, model="IZHero")


@donate_coin.resource
class Donation(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self):
        return jsonify(donated=current_user.get("donated", 0), total=self.get_total())

    def post(self):
        pr = reqparse.RequestParser()
        pr.add_argument("amount", type=int, store_missing=False)
        pr.add_argument("org", type=str, store_missing=False)
        args = pr.parse_args()
        amount = args.get("amount")

        success, mystery = current_user.donate_coins(amount)

        if success:
            coinlog = self.db["CoinLog"].find_one({"_id": current_user["_id"]})
            if not coinlog:
                coinlog = self.db["CoinLog"]()
                coinlog["_id"] = current_user["_id"]
                coinlog["donations"] = []
            coinlog["donations"].append({
                "name": args.get("org"),
                "coins": amount,
                "on": crudmgo.utctime()
            })
            coinlog.save()

        return jsonify(success=success,
                       amount=amount, donated=current_user.get("donated"),
                       total=self.get_total(), donation_needed_for_gift=mystery,
                       mystery_gift=current_user["mystery_gift"])

    def get_total(self):
        result = self.model.collection.aggregate([{
            "$group": {
                "_id": None,
                "total": {
                    "$sum": "$donated"
                }
            }
        }])

        return result["result"][0]["total"] if result.get("ok") else 0


@donate_coin.resource
class MysteryGift(Resource):
    db = None
    model = None
    # TODO: pull this out into admin editable config
    rewards = [(500, 0, 0), (1000, 0, 0), (0, 5, 0), (2000, 0, 0.01), (0, 10, 0.001)]

    def get(self):
        return jsonify(mystery_gift=current_user["mystery_gift"])

    def post(self):
        equal_weights = []
        gifts = []
        total_weight = 0.0
        leftover_weight = 1.0

        for r in self.rewards:
            if r[2] > 0:
                total_weight += r[2]
                gifts.append((r, total_weight))
            else:
                equal_weights.append(r)

        leftover_weight -= total_weight

        if equal_weights and leftover_weight > 0:
            leftover_weight_d = leftover_weight / len(equal_weights)
            for ew in equal_weights:
                total_weight += leftover_weight_d
                gifts.append((ew, total_weight))

        if current_user["mystery_gift"] and current_user["mystery_gift"] > 0:
            current_user["mystery_gift"] -= 1
            current_user.save()
            rd = random.random()
            reward = None
            for g in gifts:
                if rd < g[1]:
                    reward = g[0]
                    break
            if not reward:
                reward = gifts[-1][0]
            current_user.add_coins_points(reward[1], reward[0])

            if reward[1]:
                logger = self.db["CoinLog"].getlog(current_user["_id"])

                if logger is not None:
                    logger.log_mission(reward[1], 0, "mysterygift")

            return jsonify(success=True, rewards={"points": reward[0], "coins": reward[1]},
                           mystery_gift=current_user["mystery_gift"])

        return jsonify(success=False, mystery_gift=0)

api_donate = Api(donate_coin)
api_donate.add_resource(Donation, "", endpoint="donate")
api_donate.add_resource(Donation, "/", endpoint="slash_donate")
api_donate.add_resource(MysteryGift, "/mystery", endpoint="mystery")