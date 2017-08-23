# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify
from flask.ext import restful
from rest import crudmgo
from bson import ObjectId

iz_encyclopedia = crudmgo.CrudMgoBlueprint("iz_encyclopedia", __name__, model="EncycloCategory")
iz_encycloarticle = crudmgo.CrudMgoBlueprint("iz_encycloarticle", __name__, model="EncycloArticle")


@iz_encyclopedia.resource
class EncyclopediaList(crudmgo.ListAPI):
    readonly = True
    order = "order"

    """
    def get(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("parent", type=str, store_missing=False)
        args = pr.parse_args()

        self.filter_by = {"parent": None}
        if args.get("parent"):
            m = self.model.find_one({"uname": args["parent"]})
            if m:
                self.filter_by["parent"] = m["_id"]
        return super(EncyclopediaList, self).get()
    """
    def get(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()

        self.filter_by = {"lang": "en"}
        if args.get("lang") and args["lang"].lower() != "en":
            self.filter_by["lang"] = args["lang"].lower()
        return super(EncyclopediaList, self).get()


@iz_encyclopedia.resource
class EncyclopediaItem(crudmgo.ItemAPI):
    readonly = True

    def get(self, itemid):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()

        lang = "en"
        if args.get("lang") and args["lang"].lower() != "en":
            lang = args["lang"].lower()

        m = self.model.find_one({"uname": itemid, "lang": lang})
        if m:
            return jsonify(crudmgo.model_to_json(m, is_single=True))
        return jsonify({})


@iz_encycloarticle.resource
class ArticleList(crudmgo.ListAPI):
    limit = 0
    order = "order"
    readonly = True

    def get(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("category", type=str, store_missing=False)
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()

        self.filter_by = {"category": None, "lang": "en"}
        if args.get("lang") and args["lang"].lower() != "en":
            self.filter_by["lang"] = args["lang"].lower()

        if args.get("category"):
            if ObjectId.is_valid(args["category"]):
                self.filter_by["category"] = ObjectId(args["category"])
            else:
                m = self.db["EncycloCategory"].find_one({"uname": args["category"], "lang": self.filter_by["lang"]})
                if m:
                    self.filter_by["category"] = m["_id"]

        return super(ArticleList, self).get()


@iz_encycloarticle.resource
class ArticleItem(crudmgo.ItemAPI):
    readonly = True

    def get(self, itemid):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()

        lang = "en"
        if args.get("lang") and args["lang"].lower() != "en":
            lang = args["lang"].lower()

        m = self.model.find_one({"uname": itemid, "lang": lang})
        if m:
            return jsonify(crudmgo.model_to_json(m, is_single=True))
        return jsonify({})


api = restful.Api(iz_encyclopedia)
api.add_resource(EncyclopediaList, "", endpoint="encyclopedia")
api.add_resource(EncyclopediaList, "/", endpoint="encyclopedia_slash")
api.add_resource(EncyclopediaItem, "/item/<itemid>", endpoint="encyclopedia_item")

api = restful.Api(iz_encycloarticle)
api.add_resource(ArticleList, "", endpoint="e_articles")
api.add_resource(ArticleList, "/", endpoint="e_articles_slash")
api.add_resource(ArticleItem, "/item/<itemid>", endpoint="e_article")
