__author__ = 'n2m'

from flask.ext.restful import Api
from rest import crudmgo
from mod_auth import acl


admin_sticker = crudmgo.CrudMgoBlueprint("admin_sticker", __name__, model="File")


@admin_sticker.resource
class StickerList(crudmgo.ListAPI):
    method_decorators = [acl.requires_role("administrator")]
    filter_by = {"meta.type": "sticker"}


@admin_sticker.resource
class StickerItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("administrator")]
    filter_by = {"meta.type": "sticker"}


apisticker = Api(admin_sticker)
apisticker.add_resource(StickerList, "", endpoint="stickers")
apisticker.add_resource(StickerList, "/", endpoint="slash_stickers")