# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify, abort
from flask.ext.restful import Resource, Api, reqparse
from mod_auth import current_user, acl
from rest import crudmgo
from bson import ObjectId
import pymongo

card_shelf = crudmgo.CrudMgoBlueprint("card_shelf", __name__, model="Card")


@card_shelf.resource
class CardShelf(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self):
        cards = self.model.find({"status": True}).sort("no", pymongo.ASCENDING)
        myshelf = self.db["CollectionShelf"].getshelf(current_user["_id"])

        if not isinstance(myshelf.get("cards"), list):
            myshelf["cards"] = []

        mycards = myshelf.get_cardmap()
        results = []

        for c in cards:
            d = crudmgo.model_to_json(c)
            d.pop("created", None)
            d.pop("modified", None)

            d["count"] = mycards.get(c["_id"], {"count": 0})["count"]

            results.append(d)
        return jsonify(items=results)

    def post(self, itemid):
        itemid = ObjectId(itemid)
        c = self.model.find_one({"_id": itemid})

        if not c:
            abort(404)

        myshelf = self.db["CollectionShelf"].getshelf(current_user["_id"])

        if not myshelf.has_card(itemid):
            price = c.get("price")
            mycoins = current_user.get("dq_coins") or 0

            if not (price and mycoins >= price and current_user.add_dq_coins_points(-price, 0)):
                return jsonify(success=False)

            myshelf.add_card(itemid)
            logger = self.db["CoinLog"].getlog(current_user["_id"])
            logger.log_purchase(price, c.get("code"), "card")

        c.pop("created", None)
        c.pop("modified", None)
        return jsonify(success=True, card=crudmgo.model_to_json(c))


@card_shelf.resource
class CardUnopened(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self):
        return jsonify({"unopened_cards": current_user.get("unopened_cards") or 0})

    def post(self):
        if current_user.get("unopened_cards", 0) <= 0:
            return jsonify(success=False, card=None, unopened_cards=0)

        """
        cardr = []
        rarity = None
        i = 0

        for c in cards:
            if rarity != c["rarity"]:
                cardr.append([])
                rarity = c["rarity"]
                i = len(cardr) - 1
            cardr[i].append(c)

        r = random.randint(1, (1 << len(cardr) - 1))
        card = None

        for i in xrange(len(cardr)-1, -1, -1):
            if r & (1 << i) != 0:
                card = random.choice(cardr[i])
                break
        """

        usr = current_user._get_current_object()
        res = usr.collection.update({"_id": usr["_id"], "unopened_cards": {"$gte": 1}}, {"$inc": {"unopened_cards": -1}})
        if res and res.get("nModified"):
            cards = self.model.cardsbyrarity()
            myshelf = self.db["CollectionShelf"].getshelf(usr["_id"])
            level = usr.get("dq_level") or 1

            for i in xrange(40):
                card = self.model.rollcard(cards)
                if level > 6 or not myshelf.has_card(card["_id"]):
                    break

            myshelf.add_card(card["_id"])
            usr.reload()
            return jsonify(success=True, card=crudmgo.model_to_json(card), unopened_cards=usr["unopened_cards"])

        return jsonify(success=False, card=None, unopened_cards=0)


api_card = Api(card_shelf)
api_card.add_resource(CardShelf, "", endpoint="cards")
api_card.add_resource(CardShelf, "/", endpoint="slash_cards")
api_card.add_resource(CardShelf, "/item/<itemid>", endpoint="card")
api_card.add_resource(CardUnopened, "/open", endpoint="open")
