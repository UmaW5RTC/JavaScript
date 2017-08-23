# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify, request, abort
from flask.ext.restful import Resource, Api, reqparse
from mod_auth import current_user, acl
from rest import crudmgo
from dateutil import parser

dq_messenger = crudmgo.CrudMgoBlueprint("mesenger", __name__, model="Messenger")
dq_messengerlog = crudmgo.CrudMgoBlueprint("mesengerlog", __name__, model="ChatLog")


@dq_messenger.resource
class Messenger(crudmgo.ItemAPI):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def _getitem(self, itemid=None):
        return self.model.start()

    def get(self, itemid=None):
        return super(Messenger, self).get(itemid)

    def post(self, itemid):
        m = self._getitem()
        if not m or itemid not in self.model.__friends__:
            abort(404)

        fr = m.add_friend(itemid)
        return jsonify(fr or {})

    def put(self, itemid=None):
        return jsonify(success=False)

    def delete(self, itemid=None):
        m = self._getitem()
        if not m or not request.args.get("mission"):
            abort(404)
        mission = request.args["mission"]
        changed = False
        for k, fr in m["friends"].iteritems():
            if fr["mission"] == mission:
                fr["mission"] = ""
                fr["progress"] = ""
                changed = True
        if changed:
            m.save()
        m.collection.update({"_id": m["_id"]}, {"$set": {"missions." + mission: True}})
        return jsonify(success=True)


@dq_messenger.resource
class MessengerUnread(crudmgo.ItemAPI):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self, itemid=None):
        unread = 0
        if itemid:
            m = self.model.start(init=False)
            if m:
                unread = m.unread(itemid)
        return jsonify(unread=unread)


@dq_messengerlog.resource
class MessengerLog(crudmgo.ListAPI):
    method_decorators = [acl.requires_login]
    db = None
    model = None
    order = "-time"
    msg = None

    def get(self):
        pr = reqparse.RequestParser()
        pr.add_argument("friend", type=str, store_missing=False)
        args = pr.parse_args()
        self.filter_by = {"userid": current_user.id, "friend": args.get("friend")}
        result = super(MessengerLog, self)._get()
        if result.get("items"):
            for i in result["items"]:
                if i.get("unread"):
                    m = self.db["Messenger"].start()
                    m.mark_readall(args.get("friend"))
                    break
        return jsonify(result)

    def post(self):
        pr = reqparse.RequestParser()
        pr.add_argument("mission", type=unicode, store_missing=False)
        pr.add_argument("progress", type=unicode, store_missing=False)
        pr.add_argument("time", type=str, store_missing=False)
        args = pr.parse_args()

        self.filter_by = {"userid": current_user.id}
        if args.get("time"):
            try:
                t = parser.parse(args["time"])
                self.filter_by["time"] = t
            except ValueError:
                pass
        result = super(MessengerLog, self)._post()
        if result["success"] and self.msg["text"]:

            result["unread_count"] = 0
            m = self.db["Messenger"].start()
            if m.update_friend(self.msg["friend"], self.msg["text"], self.msg["time"], self.msg["unread"],
                               args.get("mission"), args.get("progress")):
                result["unread_count"] = m["friends"][self.msg["friend"]].get("unread", 0)
        return jsonify(result)

    def _setfilter(self, item):
        self.msg = super(MessengerLog, self)._setfilter(item)
        return self.msg


api_messenger = Api(dq_messenger)
api_messenger.add_resource(Messenger, "", endpoint="messenger")
api_messenger.add_resource(Messenger, "/", endpoint="slash_messenger")
api_messenger.add_resource(Messenger, "/<itemid>", endpoint="friend")
api_messenger.add_resource(MessengerUnread, "/unread/<itemid>", endpoint="unread")
api_messengerlog = Api(dq_messengerlog)
api_messengerlog.add_resource(MessengerLog, "", endpoint="message")
api_messengerlog.add_resource(MessengerLog, "/", endpoint="slash_message")
