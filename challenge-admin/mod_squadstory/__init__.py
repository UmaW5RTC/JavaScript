# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask.ext.restful import Api, Resource, reqparse
from flask import jsonify, request, current_app, make_response, send_from_directory
from mod_auth import acl, current_user
from rest import crudmgo
from bson import ObjectId
import os
import mimetypes


admin_squadstory = crudmgo.CrudMgoBlueprint("admin_squadstory", __name__, model="File")


@admin_squadstory.resource
class SquadStickerList(crudmgo.ListAPI):
    method_decorators = [acl.requires_role(["administrator", "teacher"])]
    readonly = True

    def get(self, squadcode=None):
        self.filter_by = {}
        if current_user.has_role("teacher"):
            if not squadcode or not current_user.get("squads"):
                return jsonify(items=[], pages=0)

            found = False
            for sq in current_user["squads"]:
                if sq["code"] == squadcode:
                    found = True
                    break

            if not found:
                return jsonify(items=[], pages=0)

            self.filter_by["group"] = True

        if squadcode:
            sq_mems = self.db["IZHero"].find({"squad.code": squadcode})
            mem_ids = [mem["_id"] for mem in sq_mems]
            self.filter_by["created.by"] = {"$in": mem_ids}
            self.filter_by["meta.type"] = "sticker"

            if request.args.get("removed"):
                self.filter_by["meta.reject_share"] = True
                self.filter_by["group"] = False

            pr = reqparse.RequestParser()
            pr.add_argument("stage", type=str, store_missing=False)
            pr.add_argument("mission", type=str, store_missing=False)
            pr.add_argument("sub_mission", type=str, store_missing=False)
            args = pr.parse_args()
            if args.get("stage"):
                try:
                    self.filter_by["meta.stage"] = int(args["stage"])
                except (ValueError, TypeError):
                    pass
            if args.get("mission"):
                self.filter_by["meta.mission"] = args["mission"]
            if args.get("sub_mission"):
                self.filter_by["meta.sub_mission"] = args["sub_mission"]

        return super(SquadStickerList, self).get()

    def post(self, squadcode=None):
        sticker = self.model.find_one({"_id": ObjectId(squadcode), "meta.reject_share": True, "meta.type": "sticker"})
        if sticker:
            if current_user.has_role("teacher"):
                owner = self.db["IZHero"].find_one({"_id": sticker["created"]["by"]})
                squadcode = owner and owner["squad"] and owner["squad"]["code"]

                if not squadcode or not current_user.get("squads"):
                    return jsonify(success=False)

                found = False
                for sq in current_user["squads"]:
                    if sq["code"] == squadcode:
                        found = True
                        break

                if not found:
                    return jsonify(success=False)

            sticker["meta"]["reject_share"] = False
            sticker["group"] = True
            sticker.save()
            return jsonify(success=True)
        return jsonify(success=False)

    def delete(self, squadcode=None):
        sticker = self.model.find_one({"_id": ObjectId(squadcode), "group": True, "meta.type": "sticker"})
        if sticker:
            if current_user.has_role("teacher"):
                owner = self.db["IZHero"].find_one({"_id": sticker["created"]["by"]})
                squadcode = owner and owner["squad"] and owner["squad"]["code"]

                if not squadcode or not current_user.get("squads"):
                    return jsonify(success=False)

                found = False
                for sq in current_user["squads"]:
                    if sq["code"] == squadcode:
                        found = True
                        break

                if not found:
                    return jsonify(success=False)

            sticker["meta"]["reject_share"] = True
            sticker["group"] = False
            sticker.save()
            return jsonify(success=True)

        return jsonify(success=False)


@admin_squadstory.resource
class SquadStoryList(crudmgo.ListAPI):
    method_decorators = [acl.requires_role(["administrator", "teacher"])]
    readonly = True

    def __init__(self, *args, **kargs):
        super(SquadStoryList, self).__init__(*args, **kargs)
        self.model = self.db["IZStory"]

    def get(self, squadcode=None):
        self.filter_by = {}
        if current_user.has_role("teacher"):
            if not squadcode or not current_user.get("squads"):
                return jsonify(items=[], pages=0)

            found = False
            for sq in current_user["squads"]:
                if sq["code"] == squadcode:
                    found = True
                    break

            if not found:
                return jsonify(items=[], pages=0)

            self.filter_by["group"] = True

        if squadcode:
            sq_mems = self.db["IZHero"].find({"squad.code": squadcode})
            mem_ids = [mem["_id"] for mem in sq_mems]
            self.filter_by["created.by"] = {"$in": mem_ids}

            if request.args.get("removed"):
                self.filter_by["meta.reject_share"] = True
                self.filter_by["group"] = False

        return super(SquadStoryList, self).get()

    def post(self, squadcode=None):
        sticker = self.model.find_one({"_id": ObjectId(squadcode), "meta.reject_share": True})
        if sticker:
            if current_user.has_role("teacher"):
                owner = self.db["IZHero"].find_one({"_id": sticker["created"]["by"]})
                squadcode = owner and owner["squad"] and owner["squad"]["code"]

                if not squadcode or not current_user.get("squads"):
                    return jsonify(success=False)

                found = False
                for sq in current_user["squads"]:
                    if sq["code"] == squadcode:
                        found = True
                        break

                if not found:
                    return jsonify(success=False)

            sticker["meta"]["reject_share"] = False
            sticker["group"] = True
            sticker.save()
            return jsonify(success=True)
        return jsonify(success=False)

    def delete(self, squadcode=None):
        sticker = self.model.find_one({"_id": ObjectId(squadcode), "group": True})
        if sticker:
            if current_user.has_role("teacher"):
                owner = self.db["IZHero"].find_one({"_id": sticker["created"]["by"]})
                squadcode = owner and owner["squad"] and owner["squad"]["code"]

                if not squadcode or not current_user.get("squads"):
                    return jsonify(success=False)

                found = False
                for sq in current_user["squads"]:
                    if sq["code"] == squadcode:
                        found = True
                        break

                if not found:
                    return jsonify(success=False)

            sticker["meta"]["reject_share"] = True
            sticker["group"] = False
            sticker.save()
            return jsonify(success=True)

        return jsonify(success=False)


@admin_squadstory.resource
class StickerList(crudmgo.ListAPI):
    method_decorators = [acl.requires_role("administrator")]

    def __init__(self):
        super(StickerList, self).__init__()
        self.filter_by = {"meta.type": "sticker"}

    def get(self):
        pr = reqparse.RequestParser()
        pr.add_argument("stage", type=str, store_missing=False)
        pr.add_argument("mission", type=str, store_missing=False)
        pr.add_argument("sub_mission", type=str, store_missing=False)
        args = pr.parse_args()

        if args.get("stage"):
            try:
                self.filter_by["meta.stage"] = int(args["stage"])
            except (ValueError, TypeError):
                pass
        if args.get("mission"):
            self.filter_by["meta.mission"] = args["mission"]
        if args.get("sub_mission"):
            self.filter_by["meta.sub_mission"] = args["sub_mission"]

        return super(StickerList, self).get()


@admin_squadstory.resource
class StickerItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("administrator")]
    filter_by = {"meta.type": "sticker"}


class DownloadSticker(Resource):
    method_decorators = [acl.requires_role("administrator")]
    __folder__ = None

    @classmethod
    def get(cls, filename, _v=False):
        def get_mimetype(fn):
            mimetype = mimetypes.guess_type(fn)[0]
            if mimetype is None:
                mimetype = 'application/octet-stream'

            return mimetype

        if current_app.config.get('USE_X_ACCEL_REDIRECT', False):
            response = make_response("")

            if '_v' in request.args:
                response.headers['Expires'] = 'Thu, 31 Dec 2037 23:55:55 GMT'
                response.headers['Cache-Control'] = 'private, max-age=315360000'
                response.headers['Pragma'] = 'cache'

            elif 'nocache' in request.args:
                response.headers['Cache-Control'] = 'no-cache, no-store, max-age=0'
                response.headers['Pragma'] = 'no-cache'

            response.headers['Content-Type'] = get_mimetype(filename)

            if 'att' in request.args:
                response.headers['Content-Disposition'] = 'attachment, filename=%s' % os.path.basename(filename)

            response.headers["X-Accel-Expires"] = 3600
            response.headers["X-Accel-Redirect"] = '%s/%s' % (current_app.config.get('X_ACCEL_REDIRECT_UPLOAD_URL', '/direct'), filename)
            return response
        else:
            if not cls.__folder__:
                cls.__folder__ = current_app.config.get("UPLOAD_FOLDER", None)
                if not cls.__folder__:
                    rdir = os.path.dirname(os.path.abspath(__file__))
                    rdir = os.path.dirname(os.path.dirname(rdir))
                    cls.__folder__ = os.path.join(rdir, "challenge-api", "uploads")
            return send_from_directory(cls.__folder__,
                                       filename,
                                       attachment_filename=filename,
                                       as_attachment='att' in request.args)


api_squadstory = Api(admin_squadstory)
api_squadstory.add_resource(StickerList, "", endpoint="stickers")
api_squadstory.add_resource(StickerList, "/", endpoint="slash_stickers")
api_squadstory.add_resource(SquadStickerList, "/squad/<squadcode>", endpoint="slash_squadsticker")
api_squadstory.add_resource(SquadStoryList, "/story/squad/<squadcode>", endpoint="slash_squadstory")
api_squadstory.add_resource(DownloadSticker, "/download/<int:_v>/<path:filename>", endpoint="download_v")
api_squadstory.add_resource(DownloadSticker, "/download/<path:filename>", endpoint="download")