# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify, abort
from mod_auth import current_user
from flask.ext import restful
from rest import crudmgo
from mod_auth import acl
from dateutil import tz
from bson import ObjectId
import datetime

admin_annce = crudmgo.CrudMgoBlueprint("admin_annce", __name__, model="Announcement")
admin_message = crudmgo.CrudMgoBlueprint("admin_message", __name__, model="Message")


@admin_annce.resource
class AnnouncementList(crudmgo.ListAPI):
    sendcount = True
    order = "-_id"
    method_decorators = [acl.requires_role(["teacher", "administrator"])]

    def _get(self):
        if current_user.has_role("teacher"):
            self.filter_by = {"$and": [{"status": True},
                                       {"$or": [{"until": {"$lte": datetime.datetime.now(tz=tz.tzlocal())}},
                                                {"until": None}]},
                                       {"$or": [{"public": True}, {"teacher": True}]}]}
        else:
            self.filter_by = {"$or": [{"public": True}, {"teacher": True}],
                              "status": True}

        d = super(AnnouncementList, self)._get()

        if d.get("items") and not current_user.has_role("administrator"):
            inbox = self.db["Inbox"].find_one({"_id": current_user["_id"]})
            hasinbox = bool(inbox and inbox.get("read"))

            for i in d["items"]:
                i["read"] = hasinbox and ObjectId(i["_id"]) in inbox["read"]

        return d

    def post(self):
        if not current_user.has_role("administrator"):
            abort(403)

        pr = restful.reqparse.RequestParser()
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()

        self.filter_by = {"lang": args["lang"] if args.get("lang") and args["lang"] != "en" else None}

        return super(AnnouncementList, self).post()

    def delete(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("id", type=unicode, action='append', store_missing=False)
        ids = pr.parse_args().get("id")

        if ids:
            ids = map(lambda x: ObjectId(x) if ObjectId.is_valid(x) else None, ids)
            self.model.collection.update({"_id": {"$in": ids}}, {"$set": {"status": False}}, multi=True)
            return jsonify(success=True)
        return jsonify(siccess=False)


@admin_annce.resource
class AnnouncementItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role(["teacher", "administrator"])]

    def get(self, itemid):
        data = self._getitem(itemid)
        if data is None:
            return jsonify({})

        message = self.db["Message"].find_one({"ann": data["_id"],
                                               "created.by": current_user["_id"]})

        data = crudmgo.model_to_json(data, is_single=True)
        data["message"] = crudmgo.model_to_json(message, is_single=True) if message else None
        return jsonify(data)

    def _getitem(self, itemid):
        if current_user.has_role("teacher"):
            self.filter_by = {"$and": [{"status": True},
                                       {"$or": [{"until": {"$lte": datetime.datetime.now(tz=tz.tzlocal())}},
                                                {"until": None}]},
                                       {"$or": [{"public": True}, {"teacher": True}]}]}
        else:
            self.filter_by = {"$or": [{"public": True}, {"teacher": True}],
                              "status": True}

        item = super(AnnouncementItem, self)._getitem(itemid)

        if item:
            item.markread()
        return item

    def put(self, itemid):
        if not current_user.has_role("administrator"):
            abort(403)
        return super(AnnouncementItem, self).put(itemid)

    def delete(self, itemid):
        if not current_user.has_role("administrator"):
            abort(403)
        return super(AnnouncementItem, self).delete(itemid)


@admin_message.resource
class MessageList(crudmgo.ListAPI):
    sendcount = True
    order = "-updated"
    method_decorators = [acl.requires_role(["teacher", "administrator"])]

    def __init__(self):
        self.filter_by = {"$or": [{"created.by": current_user["_id"]},
                                  {"to": current_user["_id"] if current_user.has_role("teacher") else None}],
                          "ann": None}


@admin_message.resource
class MessageItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role(["teacher", "administrator"])]

    def __init__(self):
        self.filter_by = {"$or": [{"created.by": current_user["_id"]},
                                  {"to": current_user["_id"] if current_user.has_role("teacher") else None}],
                          "ann": None}

    def _getitem(self, itemid):
        item = super(MessageItem, self)._getitem(itemid)
        if item:
            item.markread()
        return item

    def post(self, itemid):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("body", type=unicode, store_missing=False)
        body = pr.parse_args().get("body", "").strip()

        if not body:
            return jsonify(success=False)

        item = super(MessageItem, self)._getitem(itemid)

        if not item:
            abort(404)

        item.addreply(body)
        return jsonify(success=True, item=crudmgo.model_to_json(item))


api = restful.Api(admin_annce)
api.add_resource(AnnouncementList, "", endpoint="anns")
api.add_resource(AnnouncementList, "/", endpoint="anns_slash")
api.add_resource(AnnouncementItem, "/item/<itemid>", endpoint="ann")

api = restful.Api(admin_message)
api.add_resource(MessageList, "", endpoint="messages")
api.add_resource(MessageList, "/", endpoint="messages_slash")
api.add_resource(MessageItem, "/item/<itemid>", endpoint="message")
