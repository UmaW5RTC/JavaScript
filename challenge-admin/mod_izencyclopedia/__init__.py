# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify
from flask.ext import restful
from rest import crudmgo
from mod_auth import acl
from bson import ObjectId
import pymongo

admin_encyclopedia = crudmgo.CrudMgoBlueprint("admin_encyclopedia", __name__, model="EncycloCategory")
admin_encycloarticle = crudmgo.CrudMgoBlueprint("admin_encycloarticle", __name__, model="EncycloArticle")


@admin_encyclopedia.resource
class EncyclopediaList(crudmgo.ListAPI):
    order = "order"
    method_decorators = [acl.requires_role("administrator")]

    def get(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("parent", type=str, store_missing=False)
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()

        self.filter_by = {"lang": "en"}
        if args.get("lang") and args["lang"].lower() != "en":
            self.filter_by["lang"] = args["lang"].lower()

        if ObjectId.is_valid(args.get("parent")):
            self.filter_by["parent"] = ObjectId(args["parent"])

        return super(EncyclopediaList, self).get()

    def put(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("id", type=str, store_missing=False)
        pr.add_argument("order", type=int, store_missing=False)
        args = pr.parse_args()

        if args.get("order") and args["order"] > 0 and args.get("id") and ObjectId.is_valid(args["id"]):
            m = self.model.find_one({"_id": ObjectId(args["id"])})
            if m.get("order", 0) == args["order"]:
                return jsonify(success=True)
            if m.get("order"):
                self.model.collection.update({"order": {"$gt": m["order"]},
                                              "parent": m.get("parent"),
                                              "lang": m.get("lang")},
                                             {"$inc": {"order": -1}},
                                             multi=True)
            self.model.collection.update({"order": {"$gte": args["order"]},
                                          "parent": m.get("parent"),
                                          "lang": m.get("lang")},
                                         {"$inc": {"order": 1}},
                                         multi=True)
            self.model.collection.update({"_id": ObjectId(args["id"])},
                                         {"$set": {"order": args["order"]}})
            return jsonify(success=True)
        return jsonify(success=False)

    def post(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("order", type=int, store_missing=False)
        pr.add_argument("parent", type=str, store_missing=False)
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()

        self.filter_by = {"lang": "en"}
        if args.get("lang") and args["lang"].lower() != "en":
            self.filter_by["lang"] = args["lang"].lower()

        if args.get("order", 0) <= 0:
            d = {"parent": None, "lang": self.filter_by["lang"]}
            if args.get("parent") and ObjectId.is_valid(args["parent"]):
                d["parent"] = ObjectId(args["parent"])
            last = self.model.collection.find_one(d, sort=[("order", pymongo.DESCENDING)])
            self.filter_by["order"] = (last.get("order", 0) + 1) if last else 1

        return super(EncyclopediaList, self).post()


@admin_encyclopedia.resource
class EncyclopediaItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("administrator")]


@admin_encycloarticle.resource
class ArticleList(crudmgo.ListAPI):
    limit = 0
    order = "order"
    method_decorators = [acl.requires_role("administrator")]

    def get(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("category", type=str, store_missing=False)
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()

        if ObjectId.is_valid(args.get("category")):
            self.filter_by = {"category": ObjectId(args["category"])}
        else:
            self.filter_by = {"lang": "en"}
            if args.get("lang") and args["lang"].lower() != "en":
                self.filter_by["lang"] = args["lang"].lower()

        return super(ArticleList, self).get()

    def put(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("id", type=str, store_missing=False)
        pr.add_argument("order", type=int, store_missing=False)
        args = pr.parse_args()

        if args.get("order") and args["order"] > 0 and args.get("id") and ObjectId.is_valid(args["id"]):
            m = self.model.find_one({"_id": ObjectId(args["id"])})
            if m.get("order", 0) == args["order"]:
                return jsonify(success=True)
            if m.get("order"):
                self.model.collection.update({"order": {"$gt": m["order"]},
                                              "category": m.get("category"),
                                              "lang": m.get("lang")},
                                             {"$inc": {"order": -1}},
                                             multi=True)
            self.model.collection.update({"order": {"$gte": args["order"]},
                                          "category": m.get("category"),
                                          "lang": m.get("lang")},
                                         {"$inc": {"order": 1}},
                                         multi=True)
            self.model.collection.update({"_id": ObjectId(args["id"])},
                                         {"$set": {"order": args["order"]}})
            return jsonify(success=True)
        return jsonify(success=False)

    def post(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("order", type=int, store_missing=False)
        pr.add_argument("category", type=str, store_missing=False)
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()

        self.filter_by = {"lang": "en"}
        if args.get("category") and ObjectId.is_valid(args["category"]):
            cat = self.db["EncycloCategory"].find_one({"_id": ObjectId(args["category"])})
            if cat:
                self.filter_by["lang"] = cat["lang"]
        elif args.get("lang") and args["lang"].lower() != "en":
            self.filter_by["lang"] = args["lang"].lower()

        if args.get("order", 0) <= 0:
            d = {"category": None}
            if args.get("category") and ObjectId.is_valid(args["category"]):
                d["category"] = ObjectId(args["category"])
            last = self.model.collection.find_one(d, sort=[("order", pymongo.DESCENDING)])
            self.filter_by["order"] = (last.get("order", 0) + 1) if last else 1

        return super(ArticleList, self).post()


@admin_encycloarticle.resource
class ArticleItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("administrator")]


api = restful.Api(admin_encyclopedia)
api.add_resource(EncyclopediaList, "", endpoint="encyclopedia")
api.add_resource(EncyclopediaList, "/", endpoint="encyclopedia_slash")
api.add_resource(EncyclopediaItem, "/item/<itemid>", endpoint="encyclopedia_item")

api = restful.Api(admin_encycloarticle)
api.add_resource(ArticleList, "", endpoint="e_articles")
api.add_resource(ArticleList, "/", endpoint="e_articles_slash")
api.add_resource(ArticleItem, "/item/<itemid>", endpoint="e_article")
