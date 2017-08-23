# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify, abort
from flask.ext.restful import Resource, Api, reqparse
from mod_auth import current_user, acl
from rest import crudmgo
from bson import ObjectId
import pymongo


comic_shelf = crudmgo.CrudMgoBlueprint("comic_shelf", __name__, model="Comic")


@comic_shelf.resource
class Shelf(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self, itemid=None):
        comics = self.model.find({"status": True}).sort("title", pymongo.ASCENDING)
        myshelf = self.db["CollectionShelf"].getshelf(current_user["_id"])

        if not isinstance(myshelf.get("comics"), list):
            myshelf["comics"] = []

        mycomics = myshelf.get_comiclist()
        results = []

        for c in comics:
            d = crudmgo.model_to_json(c)
            d.pop("created", None)
            d.pop("modified", None)

            d["can_read"] = (not d.get("price")) or c["_id"] in mycomics

            if not d["can_read"]:
                d.pop("pages", None)

            results.append(d)
        return jsonify(items=results)

    def post(self, itemid):
        itemid = ObjectId(itemid)
        c = self.model.find_one({"_id": itemid})

        if not c:
            abort(404)

        myshelf = self.db["CollectionShelf"].getshelf(current_user["_id"])

        if not myshelf.has_comic(itemid):
            price = c.get("price")
            mycoins = current_user.get("coins") or 0

            if not (price and mycoins >= price and current_user.add_coins(-price)):
                return jsonify(success=False)

            myshelf.add_comic(itemid)
            logger = self.db["CoinLog"].getlog(current_user["_id"])
            logger.log_purchase(price, c.get("title"), "comic")

        c.pop("created", None)
        c.pop("modified", None)
        return jsonify(success=True, comic=crudmgo.model_to_json(c))


api_comic = Api(comic_shelf)
api_comic.add_resource(Shelf, "", endpoint="comics")
api_comic.add_resource(Shelf, "/", endpoint="slash_comics")
api_comic.add_resource(Shelf, "/purchase/<itemid>", endpoint="purchase")