__author__ = 'n2m'

from flask import jsonify, abort
from rest import crudmgo
from mod_auth import current_user, acl
from flask.ext.restful import Api, Resource, reqparse


izhero_ann = crudmgo.CrudMgoBlueprint("admin_ann", __name__, model="Announcement")


@izhero_ann.resource
class AnnList(crudmgo.ListAPI):
    method_decorators = [acl.requires_login]
    readonly = True
    inbox = None
    nomark = False

    def _get(self):
        cursor, pages, count = self._getcursorwithcount()

        if self.nomark:
            l = [crudmgo.model_to_json(m, is_list=True) for m in cursor]
        else:
            l = []
            if not self.inbox:
                self.inbox = self.db["Inbox"].getuserinbox()

            for m in cursor:
                self.inbox.markread(m, True, False)
                l.append(crudmgo.model_to_json(m, is_list=True))

            self.inbox.save()

        d = dict(items=l, pages=pages)
        if self.sendcount:
            d["count"] = count

        return d

    def get(self):
        pr = reqparse.RequestParser()
        pr.add_argument("lang", type=str, store_missing=False)
        pr.add_argument("unread", type=int, store_missing=False)
        pr.add_argument("nomark", type=int, store_missing=False)
        args = pr.parse_args()
        self.nomark = args.get("nomark", 0) == 1

        if not current_user.get("squad"):
            self.filter_by = {"public": True, "status": True}
        else:
            self.filter_by = {"$or": [{"squad_code": current_user["squad"]["code"]},
                                      {"public": True}],
                              "status": True}

        if args.get("unread", 0) == 1:
            self.inbox = self.db["Inbox"].getuserinbox()
            self.filter_by["_id"] = {"$nin": self.inbox["read"]}

        self.filter_by["lang"] = args["lang"] if args.get("lang") and args["lang"] != "en" else None

        return super(AnnList, self).get()


@izhero_ann.resource
class AnnCount(Resource):
    db = None
    model = None

    def get(self, mark=False):
        pr = reqparse.RequestParser()
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()

        inbox = self.db["Inbox"].getuserinbox(makeset=False)

        if not current_user.get("squad"):
            d = {"public": True, "status": True, "_id": {"$nin": inbox["read"]}}
        else:
            d = {"$or": [{"squad_code": current_user["squad"]["code"]},
                         {"public": True}],
                 "status": True,
                 "_id": {"$nin": inbox["read"]}}

        d["lang"] = args["lang"] if args.get("lang") and args["lang"] != "en" else None

        if mark:
            cursor = self.model.find(d)
            c = 0

            for m in cursor:
                inbox.markread(m, True, False)
                c += 1

            inbox.save()
        else:
            c = self.model.find(d).count()

        return jsonify(count=c)

    def post(self):
        return self.get(True)


api_news = Api(izhero_ann)
api_news.add_resource(AnnList, "", endpoint="news")
api_news.add_resource(AnnList, "/", endpoint="news_slash")
api_news.add_resource(AnnCount, "/unread_count", endpoint="unread_count")
