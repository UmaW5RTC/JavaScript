# -*- coding: utf-8 -*-
__author__ = 'n2m'

from rest import crudmgo
from mod_auth import current_user, acl
from flask import jsonify
from flask.ext.restful import Api, reqparse


admin_ann = crudmgo.CrudMgoBlueprint("admin_ann", __name__, model="Announcement")


@admin_ann.resource
class AnnList(crudmgo.ListAPI):
    method_decorators = [acl.requires_role(["administrator", "teacher"])]

    def get(self, squadcode=None):
        usr = current_user._get_current_object()

        if usr.has_role("teacher"):
            if squadcode:
                if not hasattr(usr, "has_squad") or not usr.has_squad(squadcode):
                    return jsonify(items=[], pages=0)

                self.filter_by = {"squad_code": squadcode}
            elif usr.get("squads"):
                self.filter_by = {"squad_code": {"$in": [s["code"] for s in usr["squads"]]}}
            else:
                return jsonify(items=[], pages=0)
        return super(AnnList, self).get()

    def post(self, squadcode=None):
        usr = current_user._get_current_object()

        if usr.has_role("teacher"):
            if not usr.get("squads") or (squadcode and (not hasattr(usr, "has_squad") or not usr.has_squad(squadcode))):
                return jsonify(success=False)

            squadcode = [s["code"] for s in usr["squads"]] if not squadcode else [squadcode]
            self.filter_by = {"squad_code": squadcode,
                              "public": False}

            pr = reqparse.RequestParser()
            pr.add_argument("lang", type=str, store_missing=False)
            args = pr.parse_args()

            self.filter_by["lang"] = args["lang"] if args.get("lang") and args["lang"] != "en" else None

        return super(AnnList, self).post()


@admin_ann.resource
class AnnItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role(["administrator", "teacher"])]

    def _getitem(self, itemid):
        item = super(AnnItem, self)._getitem(itemid)
        usr = current_user._get_current_object()

        if item and usr.has_role("teacher"):
            if not hasattr(usr, "has_squad") or not usr.has_squad(item.get("squad_code"), True):
                item = None
            else:
                self.filter_by = {"squad_code": item["squad_code"],
                                  "public": False}

        return item


apiann = Api(admin_ann)
apiann.add_resource(AnnList, "", endpoint="news")
apiann.add_resource(AnnList, "/", endpoint="news_slash")
apiann.add_resource(AnnList, "/<squadcode>", endpoint="news_code")
apiann.add_resource(AnnItem, "/item/<itemid>", endpoint="news_one")