__author__ = 'n2m'

from flask import abort, jsonify
from flask.ext.restful import Api, reqparse
from rest import crudmgo
from mod_auth import acl, current_user
from bson import ObjectId


admin_gallery = crudmgo.CrudMgoBlueprint("admin_gallery", __name__, model="Gallery")


@admin_gallery.resource
class GalleryDelete(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("administrator")]

    def post(self, itemid):
        item = self._getitem(itemid)

        if item and "removed" in item["meta"] and item["meta"]["removed"]:
            item["meta"]["removed"] = None
            item.save()
        return jsonify(success=True)

    def put(self, itemid):
        abort(404)

    def get(self, itemid):
        abort(404)

    def delete(self, itemid):
        item = self._getitem(itemid)

        if item and ("removed" not in item["meta"] or not item["meta"]["removed"]):
            item["meta"]["removed"] = True
            item.save()
        return jsonify(success=True)


@admin_gallery.resource
class Gallery(crudmgo.ListAPI):
    method_decorators = [acl.requires_role("administrator")]

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


apigallery = Api(admin_gallery)
apigallery.add_resource(Gallery, "", endpoint="gallery")
apigallery.add_resource(Gallery, "/", endpoint="gallery_slash")
apigallery.add_resource(GalleryDelete, "/delete/<itemid>", endpoint="delete")
