# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask.ext.restful import Resource, reqparse, Api
from flask import jsonify, render_template, request, send_file, abort, url_for
from mod_auth import acl, current_user, current_app
from mod_auth.model import generate_code
from rest import crudmgo
from bson import ObjectId
from xhtml2pdf import pisa
from mod_sendmail import sendmail
import pymongo
import os


izhero_story = crudmgo.CrudMgoBlueprint("izhero_story", __name__, model="IZStory", template_folder="templates")


@izhero_story.resource
class IZStory(Resource):
    db = None
    model = None
    method_decorators = [acl.requires_login]
    pillars_title = ("Adventure 1 - Discovery Desert", "Adventure 2 - Info Jungle", "Adventure 3 - Infolluted Volcano", "Adventure 4 - Digital World", "Adventure 5 - Ice Kingdom", "Adventure 6 - Mabel’s Neighbourhood", "Adventure 7 - Guardian’s Gate")
    pillars_cover = ("izstory-eyes.jpg", "izstory-radar.jpg", "izstory-control.jpg", "izstory-protect.jpg", "izstory-shout.jpg", "izstory-ears.jpg", "izstory-teleport.jpg")
    pillars_bg = ("#57b8e7", "#4bb24a", "#4bb24a", "#e83129", "#e63d94", "#f6ac48", "#f1ef41")

    def get(self, itemid=None):
        def convert_to_page(sticker, bg):
            return {"caption": "",
                    "image": "/api/download/" + (sticker["folder"] + "/" if sticker.get("folder") else "") +
                             sticker["filename"],
                    "bgcolor": bg,
                    "textcolor": "#000"}

        pillar_stories = []
        for i in xrange(7):
            prog = current_user["progress"][i+1]

            if "_completed" in prog:
                pillar_stories.append({"title": self.pillars_title[i],
                                       "cover": "/static/img/my_panel/" + self.pillars_cover[i],
                                       "bgcolor": self.pillars_bg[i],
                                       "textcolor": "#000",
                                       "nickname": current_user["username"],
                                       "pillar_story": True,
                                       "pages": [convert_to_page(stick, self.pillars_bg[i]) for stick in self.db["File"].
                                                 find({"created.by": current_user["_id"],
                                                       "meta.type": "sticker",
                                                       "meta.stage": i + 1}).sort("_id", -1).limit(14)],
                                       "created": {"by": str(current_user["_id"]),
                                                   "username": current_user["username"],
                                                   "on": crudmgo.get_flat_value(prog["_completed"])}})

        stories = self.model.find({"status": True, "created.by": current_user["_id"]}).sort("_id", pymongo.ASCENDING)
        my_stories = [crudmgo.to_flat_value(story) for story in stories]
        return jsonify(pillar_stories=pillar_stories, my_stories=my_stories)

    def post(self, itemid=None):
        pr = reqparse.RequestParser()
        pr.add_argument("title", type=unicode, store_missing=False)
        pr.add_argument("cover", type=str, store_missing=False)
        pr.add_argument("nickname", type=unicode, store_missing=False)
        pr.add_argument("bgcolor", type=str, store_missing=False)
        pr.add_argument("bgimage", type=str, store_missing=False)
        pr.add_argument("textcolor", type=str, store_missing=False)
        args = pr.parse_args()

        title = args.get("title")
        cover = args.get("cover")
        nickname = args.get("nickname", current_user["username"])
        bgcolor = args.get("bgcolor", "white")
        bgimage = args.get("bgimage")
        textcolor = args.get("textcolor", "black")

        if title and cover and nickname:
            story = self.model()
            story["title"] = title
            story["cover"] = cover
            story["nickname"] = nickname
            story["bgcolor"] = bgcolor
            story["bgimage"] = bgimage
            story["textcolor"] = textcolor
            story.save()
            return jsonify(success=True, izstory=crudmgo.model_to_json(story))
        return jsonify(success=False)

    def put(self, itemid):
        pr = reqparse.RequestParser()
        pr.add_argument("title", type=unicode, store_missing=False)
        pr.add_argument("cover", type=str, store_missing=False)
        pr.add_argument("nickname", type=unicode, store_missing=False)
        pr.add_argument("bgcolor", type=str, store_missing=False)
        pr.add_argument("bgimage", type=str, store_missing=False)
        pr.add_argument("textcolor", type=str, store_missing=False)
        args = pr.parse_args()

        title = args.get("title")
        cover = args.get("cover")
        nickname = args.get("nickname")
        bgcolor = args.get("bgcolor", "white")
        bgimage = args.get("bgimage")
        textcolor = args.get("textcolor", "black")

        story = self.model.find_one({"_id": ObjectId(itemid), "created.by": current_user["_id"]})
        if story:
            story["title"] = title or story["title"]
            story["cover"] = cover or story["cover"]
            story["nickname"] = nickname or story["nickname"]
            story["bgcolor"] = bgcolor or story["bgcolor"]
            story["bgimage"] = bgimage or story["bgimage"]
            story["textcolor"] = textcolor or story["textcolor"]
            story.save()
            return jsonify(success=True, izstory=crudmgo.model_to_json(story))
        return jsonify(success=False)

    def delete(self, itemid):
        story = self.model.find_one({"_id": ObjectId(itemid), "created.by": current_user["_id"]})
        if story:
            if self.db["Gallery"].find({"_id": story["_id"]}).count() > 0:
                self.db["Gallery"].collection.remove({"_id": story["_id"]})
            story.delete()
            return jsonify(success=True, id=itemid)
        return jsonify(success=False)


@izhero_story.resource
class IZStoryPage(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self, itemid):
        izstory = self.get_izstory(itemid)
        if izstory:
            return jsonify(crudmgo.model_to_json(izstory))
        return jsonify({})

    # add page
    def post(self, itemid=None, pageid=None):
        izstory = self.get_izstory(itemid)
        if izstory:
            pr = reqparse.RequestParser()
            pr.add_argument("caption", type=unicode, store_missing=False)
            pr.add_argument("image", type=str, store_missing=False)
            pr.add_argument("sticker", type=str, store_missing=False)
            pr.add_argument("nickname", type=unicode, store_missing=False)
            pr.add_argument("bgcolor", type=str, store_missing=False)
            pr.add_argument("bgimage", type=str, store_missing=False)
            pr.add_argument("textcolor", type=str, store_missing=False)
            args = pr.parse_args()

            caption = args.get("caption")
            image = args.get("image")
            bgcolor = args.get("bgcolor", "white")
            bgimage = args.get("bgimage")
            textcolor = args.get("textcolor", "black")
            sticker = args.get("sticker")

            if caption and (image or sticker):
                if sticker:
                    sticker = self.db["File"].find_one(ObjectId(sticker))
                    if sticker:
                        image = "/api/download/"
                        if sticker.get("folder"):
                            image += sticker.get("folder") + "/"
                        image += sticker.get("filename")

                page = {"id": ObjectId(),
                        "caption": caption,
                        "image": image,
                        "bgcolor": bgcolor,
                        "bgimage": bgimage,
                        "textcolor": textcolor}
                if not izstory["pages"]:
                    izstory["pages"] = [page]
                else:
                    izstory["pages"].append(page)

                izstory.save()
                return jsonify(success=True, page=crudmgo.to_flat_value(page))
        return jsonify(success=False)

    # edit page
    def put(self, itemid=None, pageid=None):
        izstory = self.get_izstory(itemid)

        if izstory and izstory["pages"] and pageid:
            pageid = ObjectId(pageid)
            page = None

            for p in izstory["pages"]:
                if p["id"] == pageid:
                    page = p
                    break

            if page:
                pr = reqparse.RequestParser()
                pr.add_argument("caption", type=unicode, store_missing=False)
                pr.add_argument("image", type=str, store_missing=False)
                pr.add_argument("nickname", type=unicode, store_missing=False)
                pr.add_argument("bgcolor", type=str, store_missing=False)
                pr.add_argument("bgimage", type=str, store_missing=False)
                pr.add_argument("textcolor", type=str, store_missing=False)
                args = pr.parse_args()

                caption = args.get("caption")
                image = args.get("image")
                bgcolor = args.get("bgcolor")
                bgimage = args.get("bgimage")
                textcolor = args.get("textcolor")

                if caption and image:
                    page["caption"] = caption or page["caption"]
                    page["image"] = image or page["image"]
                    page["bgcolor"] = bgcolor or page["bgcolor"]
                    page["bgimage"] = bgimage or page["bgimage"]
                    page["textcolor"] = textcolor or page["textcolor"]

                    izstory.save()
                return jsonify(success=True, page=crudmgo.to_flat_value(page))
        return jsonify(success=False)

    # delete page
    def delete(self, itemid=None, pageid=None):
        izstory = self.get_izstory(itemid)

        if izstory and izstory["pages"] and pageid:
            pageid = ObjectId(pageid)

            for p in izstory["pages"]:
                if p["id"] == pageid:
                    izstory["pages"].remove(p)
                    izstory.save()
                    break

            return jsonify(success=True)
        return jsonify(success=False)

    def get_izstory(self, itemid):
        return self.model.find_one({"_id": ObjectId(itemid), "created.by": current_user["_id"]})


@izhero_story.resource
class IZStorySquad(crudmgo.ToggleAPI):
    method_decorators = [acl.requires_login]
    toggle = "group"

    def get(self, itemid=None):
        squad = current_user["squad"]
        if current_user.get("teacher") or current_user.get("is_parent") or (squad and squad.get("code")):
            filt = {}
            d = {}

            pr = reqparse.RequestParser()
            pr.add_argument("squadcode", type=str, store_missing=False)
            pr.add_argument("stage", type=int, store_missing=False)
            pr.add_argument("mission", type=str, store_missing=False)
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

            shared_stories = self.model.find(filt).sort("_id", pymongo.ASCENDING)
            d["my_stories"] = [crudmgo.model_to_json(story) for story in shared_stories]
            return jsonify(d)
        return jsonify(my_stories=[])

    # like/dislike story
    def put(self, itemid):
        story = self._getsquaditem(itemid)
        if story:
            if not isinstance(story.get("meta"), dict):
                story["meta"] = {}
            if not story["meta"].get("likes"):
                story["meta"]["likes"] = []
            if current_user["_id"] in story["meta"]["likes"]:
                story["meta"]["likes"].remove(current_user["_id"])
            else:
                story["meta"]["likes"].append(current_user["_id"])
            story.save()
            return jsonify(success=True)
        return jsonify(success=False)

    def _getsquaditem(self, itemid):
        squad = current_user["squad"]
        if squad and squad.get("code"):
            story = self.model.find_one({"_id": ObjectId(itemid)})
            if story and story.get("created") and story["created"].get("by"):
                owner = self.db["IZHero"].find_one({"_id": story["created"]["by"],
                                                    "squad.code": squad["code"]})
                if owner:
                    return story
        return None

    def _getitem(self, itemid):
        self.filter_by = {"created.by": current_user["_id"]}
        item = super(IZStorySquad, self)._getitem(itemid)
        if item and "group" not in item:
            item["group"] = False
        return item


@izhero_story.resource
class IZStoryEmail(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def post(self, itemid):
        item = self.model.find_one({"_id": ObjectId(itemid), "created.by": current_user["_id"]})
        if not item:
            abort(404)
        pr = reqparse.RequestParser()
        pr.add_argument("email", type=unicode, store_missing=False)
        pr.add_argument("message", type=unicode, store_missing=False)
        args = pr.parse_args()

        if args.get("email"):
            if not isinstance(item.get("meta"), dict):
                item["meta"] = {}
            if not item["meta"].get("key"):
                item["meta"]["key"] = generate_code(16)
                item.save()

            link = url_for("izhero_story.download", itemid=itemid, _external=True)
            sendmail(args["email"],
                     "[DQ World] %s has shared with you a STORY" % current_user["givenname"],
                     render_template("izstory.html",
                                     url_root=os.path.dirname(request.url_root[:-1]) + '/',
                                     message=args.get("message", ""),
                                     link=link))


@izhero_story.resource
class IZStoryDownload(Resource):
    db = None
    model = None

    def get(self, itemid):
        item = self.model.find_one({"_id": ObjectId(itemid)})
        if not item:
            abort(404)

        storypath = os.path.join(current_app.drawing_app.ufolder, "izstory")
        if not os.path.isdir(storypath):
            os.mkdir(storypath)

        username = item.get("created", {}).get("username", "aa")
        userpath = os.path.join(storypath, username[0:2] if len(username) >= 2 else username)
        if not os.path.isdir(userpath):
            os.mkdir(userpath)

        fpath = os.path.join(userpath, itemid + '.pdf')

        if item and not (isinstance(item.get("meta"), dict) and item["meta"].get("pdfied") and os.path.isfile(fpath)
                         and (not item.get("modified") or (isinstance(item.get("modified"), list)
                              and item["meta"].get("pdfied") and item["modified"]
                              and item["meta"]["pdfied"] >= item["modified"][len(item["modified"]) - 1]["on"]))):
            html = render_template("izstory_dl.html",
                                   url_root=os.path.dirname(request.url_root[:-1]) + '/',
                                   **item)

            with open(fpath, "w+b") as f:
                pisa.CreatePDF(html, dest=f, link_callback=self.link_callback)

            item.collection.update({"_id": item["_id"]}, {"$set": {"meta.pdfied": crudmgo.utctime()}})

        return send_file(fpath, mimetype='application/pdf', as_attachment=True)

    @staticmethod
    def link_callback(uri, rel):
        dl_uri = "/api/download/"
        templates_uri = "/template/"
        path = ""
        if uri.startswith(dl_uri):
            path = os.path.join(current_app.upload_app.ufolder, uri.replace(dl_uri, ""))
        elif uri.startswith(templates_uri):
            path = os.path.join(os.path.dirname(__file__), izhero_story.template_folder, uri.replace(templates_uri, ""))
        return path


api_izstory = Api(izhero_story)
api_izstory.add_resource(IZStory, "", endpoint="izstory")
api_izstory.add_resource(IZStory, "/", endpoint="slash_izstory")
api_izstory.add_resource(IZStory, "/cover/<itemid>", endpoint="cover")
api_izstory.add_resource(IZStoryPage, "/<itemid>", endpoint="page")
api_izstory.add_resource(IZStoryPage, "/<itemid>/page/<pageid>", endpoint="page_mod")
api_izstory.add_resource(IZStorySquad, "/share/<itemid>", endpoint="share")
api_izstory.add_resource(IZStorySquad, "/squad", endpoint="squad")
api_izstory.add_resource(IZStoryDownload, "/download/<itemid>", endpoint="download")
api_izstory.add_resource(IZStoryEmail, "/email/<itemid>", endpoint="email")
