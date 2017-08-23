__author__ = 'n2m'

from flask import jsonify, abort
from rest import crudmgo
from flask.ext.restful import Api, reqparse, Resource
from mod_auth import current_user, acl
from bson import ObjectId


gallery_sticker = crudmgo.CrudMgoBlueprint("gallery_sticker", __name__, model="Gallery")


def can_nominate(db, item, user):
    if item["created"]["by"] != user["_id"]:
        owner = db["IZHero"].find_one({"_id": item["created"]["by"]})

        if not owner.is_child_of(user) and not (owner.squadcode and user.has_role("teacher")
                                                and user.has_squad(owner.squadcode))\
                and owner.squadcode != user.squadcode:
            return False
    return True


@gallery_sticker.resource
class GalleryList(crudmgo.ListAPI):
    no_ulimit = True
    order = "-nominated.on"
    sendcount = True
    filter_by = {"meta.removed": None}

    def get(self):
        pr = reqparse.RequestParser()
        pr.add_argument("type", type=str, store_missing=False)
        pr.add_argument("reported", type=str, store_missing=False)
        pr.add_argument("removed", type=str, store_missing=False)
        reqargs = pr.parse_args()
        gallery_t = reqargs.get("type")
        reported = reqargs.get("reported")
        removed = reqargs.get("removed")
        self.filter_by = self.__class__.filter_by.copy()

        if gallery_t in ("story", "sticker"):
            self.filter_by["meta.type"] = gallery_t
        if removed:
            self.filter_by["meta.removed"] = True
        if reported:
            self.filter_by["meta.flag"] = True

        gallery = self._get()

        if gallery["items"]:
            stickersid = []
            storiesid = []
            itemsid = []

            for i in gallery["items"]:
                oid = ObjectId(i["_id"])
                if i["meta"]["type"] == "sticker":
                    stickersid.append(oid)
                else:
                    storiesid.append(oid)
                itemsid.append(oid)

            likes = set()
            if not current_user.is_anonymous:
                likes = set(str(l["galleryid"]) for l in self.db["GalleryLike"].find({"galleryid": {"$in": itemsid},
                                                                                      "user.by": current_user["_id"]}))

            squad_likes = {str(s["_id"]): s["meta"].get("likes", ()) for s in self.db["File"].find({"meta.type": "sticker",
                                                                                                    "meta.likes": {"$ne": None},
                                                                                                    "_id": {"$in": stickersid}})}
            stories_likes = {str(s["_id"]): s["meta"].get("likes", ()) for s in self.db["IZStory"].find({"meta.likes": {"$ne": None},
                                                                                                         "_id": {"$in": storiesid}})}

            for i in gallery["items"]:
                if not i["meta"]:
                    i["meta"] = {}
                i["meta"]["i_liked"] = i["_id"] in likes

                if i["meta"]["type"] == "sticker" and i["_id"] in squad_likes:
                    i["meta"]["likes_count"] = i["meta"]["likes_count"] + len(squad_likes[i["_id"]]) \
                        if "likes_count" in i["meta"] else len(squad_likes[i["_id"]])
                elif i["meta"]["type"] == "story" and i["_id"] in stories_likes:
                    i["meta"]["likes_count"] = i["meta"]["likes_count"] + len(stories_likes[i["_id"]]) \
                        if "likes_count" in i["meta"] else len(stories_likes[i["_id"]])

        return jsonify(gallery)

    @acl.requires_login
    def post(self):
        pr = reqparse.RequestParser()
        pr.add_argument("sticker", type=str, store_missing=False)
        pr.add_argument("story", type=str, store_missing=False)
        pr.add_argument("text", type=unicode, store_missing=False)
        args = pr.parse_args()
        itemid = None
        is_sticker = True

        if args.get("sticker"):
            itemid = args["sticker"]
        elif args.get("story"):
            itemid = args["story"]
            is_sticker = False

        if itemid:
            gallery = self.model.nominate(itemid, current_user._get_current_object(), args.get("text", ""), is_sticker)
            return jsonify(success=bool(gallery), nomination=crudmgo.model_to_json(gallery) if gallery else {})
        return jsonify(success=False)


@gallery_sticker.resource
class GalleryItem(crudmgo.ItemAPI):
    filter_by = {"meta.removed": None}
    
    def get(self, itemid):
        item = self._getitem(itemid)
        if item is None:
            return jsonify({})
        else:
            data = crudmgo.model_to_json(item, is_single=True)
            if not current_user.is_anonymous:
                data["meta"]["i_liked"] = self.db["GalleryLike"].find({"galleryid": item["_id"],
                                                                       "user.by": current_user["_id"]}).count() > 0
            else:
                data["meta"]["i_liked"] = False

            if data["meta"]["type"] == "sticker":
                sticker = self.db["File"].find_one({"_id": item["_id"]})
                if sticker and sticker["meta"].get("likes"):
                    data["meta"]["likes_count"] += len(sticker["meta"]["likes"])
            elif data["meta"]["type"] == "story":
                story = self.db["IZStory"].find_one({"_id": item["_id"]})
                if story and story.get("meta") and story["meta"].get("likes"):
                    data["meta"]["likes_count"] += len(story["meta"]["likes"])
                data["pages"] = crudmgo.to_flat_value(story["pages"]) if story and story.get("pages") else []
        return jsonify(data)

    # flag sticker
    @acl.requires_login
    def post(self, itemid):
        item = self._getitem(itemid)
        if item and not item["meta"].get("flag"):
            item["meta"]["flag"] = True
            item.save()
        return jsonify(success=True)

    # like/unlike sticker
    @acl.requires_login
    def put(self, itemid):
        item = self._getitem(itemid)
        if item:
            item.like(current_user._get_current_object())
            return jsonify(success=True)
        return jsonify(success=False)


api_gallery = Api(gallery_sticker)
api_gallery.add_resource(GalleryList, "", endpoint="gallery")
api_gallery.add_resource(GalleryList, "/", endpoint="gallery_slash")
api_gallery.add_resource(GalleryItem, "/item/<itemid>", endpoint="sticker")