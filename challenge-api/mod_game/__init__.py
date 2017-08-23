# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify, abort, render_template
from flask.ext.restful import Resource, Api, reqparse
from mod_auth import current_user, acl, current_session
from rest import crudmgo
from bson import ObjectId
import pymongo


game_shelf = crudmgo.CrudMgoBlueprint("game_shelf", __name__, model="Game", template_folder="templates")


@game_shelf.resource
class Shelf(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self, itemid=None):
        games = self.model.find({"status": True}).sort("title", pymongo.ASCENDING)
        results = []
        for g in games:
            g = crudmgo.model_to_json(g)
            g.pop("created", None)
            g.pop("modified", None)
            results.append(g)
        return jsonify(items=results)

    def post(self, itemid):
        #itemid = ObjectId(itemid)
        #g = self.model.find_one({"_id": itemid})
        # TODO: do not hardcode
        g = {"game_code": "boolee-dungeon",
             "price": 2}

        if not g:
            abort(404)

        if not current_session.get("data"):
            current_session["data"] = {}
        if not current_session["data"].get("game"):
            current_session["data"]["game"] = []
        if g["game_code"] in current_session["data"]["game"]:
            return jsonify(success=True, game_code=g["game_code"])

        price = g.get("price")
        mycoins = current_user.get("coins") or 0
        if not (isinstance(price, (int, float)) and mycoins >= price and current_user.add_coins(-price)):
            return jsonify(success=False)

        current_session["data"]["game"].append(g["game_code"])
        return jsonify(success=True, game_code=g["game_code"])


@game_shelf.resource
class GamePlay(Resource):
    method_decorators = [acl.requires_login]

    def get(self, gamecode):
        """
        sessg = current_session.get("data") and current_session["data"].get("game")
        if sessg and gamecode in sessg:
            return render_template("game.html",
                                   gamecode=gamecode)
        abort(403)
        """
        sessg = current_session.get("data") and current_session["data"].get("game")
        return sessg and gamecode in sessg

    def post(self, gamecode):
        sessg = current_session.get("data") and current_session["data"].get("game")
        if sessg and gamecode in sessg:
            pr = reqparse.RequestParser()
            pr.add_argument("points", type=int, store_missing=False)
            points = pr.parse_args().get("points", 0)

            if points and 0 < points <= 1000:
                current_user.add_points(points)

            sessg.remove(gamecode)
            return jsonify(success=True)
        return jsonify(success=False)


api_game = Api(game_shelf)
api_game.add_resource(Shelf, "", endpoint="games")
api_game.add_resource(Shelf, "/", endpoint="slash_games")
api_game.add_resource(Shelf, "/purchase/<itemid>", endpoint="purchase")
api_game.add_resource(GamePlay, "/game/<gamecode>", endpoint="gameplay")
