# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify, current_app, request, abort, send_from_directory, url_for, render_template, redirect
from flask.views import View
from flask.ext.restful import Resource, Api, reqparse
from threading import Timer
from rest import crudmgo
from mod_auth import acl, current_user, current_session
from mod_auth.model import generate_code
from model.stage import StageOne, StageTwo, StageFour, StageFive, StageSix, StageThree, StageSeven
from bson import ObjectId
from mod_sendmail import sendmail
import os
import re
import pymongo

invalid_dir_chars = re.compile('[' + re.escape(r'\/:*?"<>|.') + ']')
lang_list = ("en", "ko")


class Drawing(object):
    ufolder = "uploads"
    ufolder_drawing = "uploads/drawing"
    vw_prefix = ""
    vw_name = "stickers"
    _stickers = None
    __recached = False
    __drawing_foldername__ = "drawing"

    @property
    def stickers(self):
        return self._stickers

    def __init__(self, app=None, vw_prefix=None, vw_name=None):
        if app is not None:
            self.init_app(app, vw_prefix, vw_name)
        else:
            self.vw_prefix = vw_prefix or self.vw_prefix
            self.vw_name = vw_name or self.vw_name

    def init_app(self, app, vw_prefix=None, vw_name=None):
        self.ufolder = app.upload_app.ufolder
        self.ufolder_drawing = os.path.join(app.upload_app.ufolder, self.__drawing_foldername__)

        if not os.path.isdir(self.ufolder_drawing):
            os.mkdir(self.ufolder_drawing)

        self.vw_prefix = vw_prefix or self.vw_prefix
        self.vw_name = vw_name or self.vw_name
        app.drawing_app = self
        app.upload_app.add_upload("drawing", upload_drawing)
        app.add_url_rule(self.vw_prefix + "/" + self.vw_name, view_func=Stickers.as_view(self.vw_name))
        self.__recache()

    def cache_stickers_list(self):
        p = os.path.join(self.ufolder, "stickers")
        stickers = {}

        if os.path.isdir(p):
            for d in os.listdir(p):
                newp = os.path.join(p, d)
                if not os.path.isdir(newp):
                    continue

                stickers[d] = sorted([({"name": s,
                                        "stickers": sorted([ss for ss in os.listdir(os.path.join(newp, s))
                                                            if os.path.isfile(os.path.join(newp, s, ss))])}
                                       if os.path.isdir(os.path.join(newp, s)) else s) for s in os.listdir(newp)])

        self._stickers = stickers

    def __recache(self):
        if self.__recached:
            return

        self.__recached = True

        def _cacheit():
            self.cache_stickers_list()
            Timer(3600, _cacheit)
        _cacheit()


class Stickers(View):
    def dispatch_request(self):
        return jsonify(current_app.drawing_app.stickers or {})


def upload_drawing():
    data = request.json or (request.form and request.form.to_dict())
    if not data:
        return {"success": False}
    coins = 0
    points = 0
    meta = {"type": "sticker",
            "caption": data.get("caption"),
            "stage": data.get("stage", 0),
            "mission": data.get("mission", ""),
            "sub_mission": data.get("sub_mission")}

    if not meta["mission"]:
        meta["stage"] = 0

    is_group = data.get("share")
    is_group = is_group.lower() in ["1", "true", "t", "on", "yes"]\
        if isinstance(is_group, basestring) else bool(is_group)

    user = current_user._get_current_object()
    username = user.get_username()
    part_username = username[0:2] if len(username) >= 2 else username
    part_username = invalid_dir_chars.sub("z", part_username)
    user_folder = os.path.join(current_app.drawing_app.__drawing_foldername__,
                               part_username)
    fullpath = os.path.join(current_app.drawing_app.ufolder, user_folder)
    if not os.path.isdir(fullpath):
        os.mkdir(fullpath)
    saved = current_app.upload_app.save_file(data, folder=user_folder, meta=meta, group=is_group, is_datauri=True)

    try:
        stage_num = int(meta["stage"])
    except (TypeError, ValueError):
        stage_num = 0

    if saved and 0 <= stage_num <= 7:
        # TODO: refactor the whole progress functionality
        if stage_num == 1:
            points, coins = StageOne.post(meta["mission"], meta["sub_mission"])
        elif stage_num == 2:
            points, coins = StageTwo.post(meta["mission"], meta["sub_mission"])
        elif stage_num == 3:
            points, coins = StageThree.post(meta["mission"], meta["sub_mission"])
        elif stage_num == 4:
            points, coins = StageFour.post(meta["mission"], meta["sub_mission"])
        elif stage_num == 5:
            points, coins = StageFive.post(meta["mission"], meta["sub_mission"])
        elif stage_num == 6:
            points, coins = StageSix.post(meta["mission"], meta["sub_mission"])
        elif stage_num == 7:
            points, coins = StageSeven.post(meta["mission"], meta["sub_mission"])

        if "points_stage" not in user or not user["points_stage"]:
            user["points_stage"] = {"e0": 0, "e1": 0, "e2": 0, "e3": 0, "e4": 0, "e5": 0, "e6": 0, "e7": 0}
        if "coins_stage" not in user or not user["coins_stage"]:
            user["coins_stage"] = {"e0": 0, "e1": 0, "e2": 0, "e3": 0, "e4": 0, "e5": 0, "e6": 0, "e7": 0}

        stage_key = "e"+str(stage_num)
        if stage_key not in user["coins_stage"] or not user["coins_stage"][stage_key]:
            user["coins_stage"][stage_key] = coins
        else:
            user["coins_stage"][stage_key] += coins

        if stage_key not in user["points_stage"] or not user["points_stage"][stage_key]:
            user["points_stage"][stage_key] = points
        else:
            user["points_stage"][stage_key] += points

        if not user.get("progress") or len(user["progress"]) < 8:
            user["progress"] = [{} for _ in xrange(8)]
        if not user["progress"][0].get("justlove"):
            user["progress"][0]["justlove"] = crudmgo.utctime()

        user["coins"] = user["coins"] + coins if user.get("coins") else coins
        user["points"] = user["points"] + points if user.get("points") else points

        user.save()

    return {"success": bool(saved), "coins": coins, "points": points, "_id": (saved and str(saved["_id"]) or None)}


drawing_sticker = crudmgo.CrudMgoBlueprint("drawing_sticker", __name__, model="File", template_folder="templates")


@drawing_sticker.resource
class StickerList(crudmgo.ListAPI):
    method_decorators = [acl.requires_login]
    filter_by = {"meta.type": "sticker"}
    limit = 0

    def get(self):
        self.filter_by["created.by"] = current_user["_id"]
        return super(StickerList, self).get()

    def post(self):
        return jsonify(upload_drawing())


@drawing_sticker.resource
class StickerItem(crudmgo.ItemAPI):
    db = None
    model = None
    method_decorators = [acl.requires_login]
    filter_by = {"meta.type": "sticker"}

    def put(self, itemid):
        f = self._getitem(itemid)
        if f:
            data = request.json or (request.form and request.form.to_dict())
            caption = data.get("caption")

            if caption is not None:
                f["meta"]["caption"] = caption
            is_group = data.get("share")

            if is_group is not None and not f["meta"].get("reject_share"):
                is_group = is_group.lower() in ["1", "true", "t", "on", "yes"]\
                    if isinstance(is_group, basestring) else bool(is_group)
                f["group"] = is_group

            f.save()

            return jsonify(success=True)
        abort(404)

    def _getitem(self, itemid):
        self.filter_by["created.by"] = current_user["_id"]
        return super(StickerItem, self)._getitem(itemid)

    def delete(self, itemid):
        item = self._getitem(itemid)

        if item:
            if self.db["Gallery"].find({"_id": item["_id"]}).count() > 0:
                self.db["Gallery"].collection.remove({"_id": item["_id"]})
            self.db["FileBin"]().trash(item)
            return jsonify(success=True, id=itemid)
        return jsonify(success=False, error="Item not found")


@drawing_sticker.resource
class StickerEmail(Resource):
    db = None
    model = None

    def get(self, itemid, key):
        item = self.model.find_one({"_id": ObjectId(itemid), "meta.key": key})
        if not item:
            abort(404)

        if current_app.config.get("BUCKET"):
            fileurl = "https://storage.googleapis.com/%s/%s/%s" % (current_app.config["BUCKET"],
                                                                   item["folder"],
                                                                   item["filename"])
            return redirect(fileurl)

        return send_from_directory(current_app.upload_app.ufolder,
                                   (item["folder"] + '/' + item["filename"]) if item.get("folder") else item["filename"],
                                   attachment_filename=item["name"] if item.get("name") else item["filename"],
                                   as_attachment='att' in request.args)

    @acl.requires_login
    def post(self, itemid, key=None):
        item = self.model.find_one({"_id": ObjectId(itemid), "created.by": current_user["_id"]})
        if not item:
            abort(404)

        pr = reqparse.RequestParser()
        pr.add_argument("email", type=unicode, store_missing=False)
        pr.add_argument("message", type=unicode, store_missing=False)
        pr.add_argument("is_pledge", type=bool, store_missing=False)
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()

        if args.get("email"):
            urlid = itemid

            if not isinstance(item.get("meta"), dict):
                item["meta"] = {}
            if not item["meta"].get("key"):
                item["meta"]["key"] = generate_code(16)
                item.save()

            link = url_for("drawing_sticker.email_download", itemid=itemid, key=item["meta"]["key"], _external=True)

            if args.get("is_pledge"):
                tmpl = "mediapledge.html"
                subject = "You’ve made a promise with your kid on DQWOrld.net!"
            else:
                tmpl = "/sticker.html"
                lang = args.get("lang", "en")
                lang = lang if lang in lang_list else "en"
                tmpl = (lang + tmpl) if lang in lang_list else "en" + tmpl

                title = {
                    "ko": u"[DQ 월드] %s 님이 스티커를 공유했습니다.",
                    "en": "[DQ World] %s has shared with you a STICKER"
                }
                subject = (title.get(lang) or title["en"]) % current_user["givenname"]

            if not args.get("is_pledge"):
                l = self.db["JustLoveEmailLog"]()
                l["email"] = args["email"]
                l["message"] = args.get("message")
                l["link"] = link
                l["file"] = ObjectId(itemid)
                l.save()
                urlid = l.get("_id")

            sendmail(args["email"],
                     subject,
                     render_template(tmpl,
                                     message=args.get("message", ""),
                                     link=link,
                                     url_root=os.path.dirname(request.url_root[:-1]) + '/',
                                     url=url_for('facebook.share',
                                                 mod='mediapledge' if args.get("is_pledge") else 'sticker',
                                                 itemid=urlid,
                                                 _external=True)))
            return jsonify(success=True)
        return jsonify(success=False)


@drawing_sticker.resource
class SquadStickerList(Resource):
    db = None
    model = None
    method_decorators = [acl.requires_login]
    filter_by = {"meta.type": "sticker"}

    def get(self, itemid=None):
        squad = current_user["squad"]
        if current_user.get("teacher") or current_user.get("is_parent") or (squad and squad.get("code")):
            filt = {}
            d = {}

            pr = reqparse.RequestParser()
            pr.add_argument("squadcode", type=str, store_missing=False)
            pr.add_argument("stage", type=int, store_missing=False)
            pr.add_argument("mission", type=str, store_missing=False)
            pr.add_argument("sort", type=str, store_missing=False)
            args = pr.parse_args()

            if args.get("stage") is not None:
                filt["meta.stage"] = args["stage"]
            if args.get("mission"):
                filt["meta.mission"] = args["mission"]

            if current_user.get("teacher"):
                teach = self.db["Teacher"].find_one({"username": current_user["username"]})

                if not teach or not isinstance(teach.get("squads"), list) or len(teach["squads"]) == 0:
                    return jsonify(items=[])

                d["squads"] = teach["squads"]

                if args.get("squadcode"):
                    squad = {"code": args["squadcode"]}
                else:
                    squad = {"code": teach["squads"][0]["code"]}

                d["squadcode"] = squad["code"]

            if current_user.get("is_parent"):
                sq_mems = self.db["IZHero"].find({"parent.email": current_user["parent"]["email"]})
            else:
                sq_mems = self.db["IZHero"].find({"squad.code": squad["code"]})

            filt["created.by"] = {"$in": [mem["_id"] for mem in sq_mems]}

            if not current_user.get("is_parent"):
                filt["group"] = True

            shared_stickers = self.model.find(filt).sort("_id", pymongo.ASCENDING if args.get("sort") and args["sort"].lower() == "asc" else pymongo.DESCENDING)
            d["items"] = [crudmgo.model_to_json(sticker) for sticker in shared_stickers]
            return jsonify(d)
        return jsonify(items=[])

    def post(self, itemid):
        sticker = self.model.find_one({"_id": ObjectId(itemid),
                                       "meta.type": "sticker",
                                       "created.by": current_user["_id"]})
        if sticker and not sticker["meta"].get("reject_share"):
            if not sticker["group"]:
                pr = reqparse.RequestParser()
                pr.add_argument("caption", type=unicode, store_missing=False)
                args = pr.parse_args()

                if "caption" in args:
                    sticker["meta"]["caption"] = args["caption"]

                sticker["group"] = True
                sticker.save()
            return jsonify(success=True)
        return jsonify(success=False)

    def put(self, itemid):
        sticker = self.model.find_one({"_id": ObjectId(itemid),
                                       "meta.type": "sticker",
                                       "created.by": current_user["_id"]})
        if sticker and not sticker["meta"].get("reject_share"):
            if not sticker["group"]:
                sticker["group"] = True
            else:
                sticker["group"] = False
            sticker.save()
            return jsonify(success=True)
        return jsonify(success=False)

    def delete(self, itemid):
        sticker = self.model.find_one({"_id": ObjectId(itemid),
                                       "meta.type": "sticker",
                                       "created.by": current_user["_id"]})
        if sticker:
            if sticker["group"]:
                sticker["group"] = False
                sticker.save()
            return jsonify(success=True)
        return jsonify(success=False)


@drawing_sticker.resource
class SquadStickItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_login]

    def _getitem(self, itemid):
        squad = current_user["squad"]
        if current_user.get("is_parent") or (squad and squad.get("code")):
            sticker = self.model.find_one({"_id": ObjectId(itemid),
                                           "meta.type": "sticker"})
            if sticker and sticker.get("created") and sticker["created"].get("by"):
                filt = {"_id": sticker["created"]["by"]}
                if current_user.get("is_parent"):
                    filt["parent.email"] = current_user["parent"]["email"]
                else:
                    filt["squad.code"] = squad["code"]
                owner = self.db["IZHero"].find_one(filt)
                if owner:
                    return sticker
        return None

    # post comment
    def post(self, itemid):
        sticker = self._getitem(itemid)
        if sticker:
            data = request.json or (request.form and request.form.to_dict())

            if data and "comment" in data:
                if not sticker["meta"].get("comments"):
                    sticker["meta"]["comments"] = []
                sticker["meta"]["comments"].append({"_id": ObjectId(),
                                                    "comment": data["comment"],
                                                    "created": {
                                                        "by": current_user["_id"],
                                                        "username": current_user.get_username(),
                                                        "on": crudmgo.utctime()}})
                sticker.save()
                return jsonify(success=True)
        return jsonify(success=False)

    # like/dislike sticker
    def put(self, itemid):
        sticker = self._getitem(itemid)
        if sticker:
            if not sticker["meta"].get("likes"):
                sticker["meta"]["likes"] = []
            if current_user["_id"] in sticker["meta"]["likes"]:
                sticker["meta"]["likes"].remove(current_user["_id"])
            else:
                sticker["meta"]["likes"].append(current_user["_id"])
            sticker.save()
            return jsonify(success=True)
        return jsonify(success=False)

    # delete comment
    def delete(self, itemid):
        pass


api_sticker = Api(drawing_sticker)
api_sticker.add_resource(StickerList, '', endpoint="stickers")
api_sticker.add_resource(StickerList, '/', endpoint="stickers_slash")
api_sticker.add_resource(StickerItem, '/item/<itemid>', endpoint="sticker")
api_sticker.add_resource(SquadStickerList, "/squad", endpoint="squad_stickers")
api_sticker.add_resource(SquadStickerList, "/squad/share/<itemid>", endpoint="squad_stickers_id")
api_sticker.add_resource(SquadStickItem, "/squad/item/<itemid>", endpoint="squad_sticker")
api_sticker.add_resource(StickerEmail, "/email/<itemid>", endpoint="email")
api_sticker.add_resource(StickerEmail, "/download/<itemid>/<key>", endpoint="email_download")