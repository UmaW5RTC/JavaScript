__author__ = 'n2m'

from rest import crudmgo
from bson import ObjectId
import datetime


class Gallery(crudmgo.RootDocument):
    __collection__ = "gallery"
    __crud_searchfield__ = ("file.created.username",)
    __admin_name__ = "iZ HERO TEAM"

    structure = {
        "_id": ObjectId,
        "file": {
            "filename": basestring,
            "folder": basestring,
            "title": basestring,
            "bgcolor": basestring,
            "bgimage": basestring,
            "textcolor": basestring,
            "created": {
                "by": ObjectId,
                "username": basestring,
                "on": datetime.datetime
            }
        },
        "meta": {},
        "nominated": [{
            "by": ObjectId,
            "username": basestring,
            "on": datetime.datetime,
            "text": basestring
        }]
    }
    indexes = [
        {"fields": "nominated.by",
         "check": False},
        {"fields": "file.created.by"},
        {"fields": "meta.flag",
         "check": False}
    ]
    required = ["name", "filename"]

    def add_nomination(self, user, text):
        if not self.get("_id"):
            return False

        if not isinstance(self.get("nominated"), list):
            self["nominated"] = []

        is_admin = user.has_role("administrator")

        for n in self["nominated"]:
            if (is_admin and n["username"] == self.__admin_name__) or (not is_admin and user["_id"] == n["by"]):
                if n["text"] != text:
                    n["text"] = text
                    self.save()
                return True

        self["nominated"].append({
            "by": user["_id"],
            "username": self.__admin_name__ if is_admin else user.get_username(),
            "on": crudmgo.utctime(),
            "text": text
        })
        self.save()

        return True

    def nominate(self, itemid, user, text, sticker=True):
        if not isinstance(itemid, ObjectId):
            if not ObjectId.is_valid(itemid):
                return False

            itemid = ObjectId(itemid)

        db = self.collection.database
        item = db["File"].find_one({"_id": itemid, "meta.type": "sticker"}) if sticker else\
            db["IZStory"].find_one({"_id": itemid})

        if not item:
            return False
        gallery = self.find_one({"_id": item["_id"]})

        if not gallery:
            gallery = self()
            gallery["_id"] = item["_id"]

            if sticker:
                gallery["file"] = {
                    "filename": item["filename"],
                    "folder": item["folder"],
                    "created": item["created"]
                }
            else:
                gallery["file"] = {
                    "filename": item["cover"],
                    "folder": "",
                    "title": item["title"],
                    "bgcolor": item["bgcolor"],
                    "bgimage": item["bgimage"],
                    "textcolor": item["textcolor"],
                    "created": item["created"]
                }
            gallery["sticker"] = True
            gallery["meta"] = {
                "likes_count": db["GalleryLike"].find({"galleryid": item["_id"]}).count(),
                "type": "sticker" if sticker else "story"
            }

        gallery.add_nomination(user, text)

        if not item.get("public") or not item.get("meta") or not item["meta"].get("nominated"):
            if not item.get("meta"):
                item["meta"] = {}
            item["meta"]["nominated"] = True
            item["public"] = True
            item.save()

        return gallery

    def like(self, user):
        if self.get("_id"):
            res = "like"
            gallerylike = self.collection.database["GalleryLike"]
            like = gallerylike.find_one({"galleryid": self["_id"],
                                         "user.by": user["_id"]})
            if like:
                like.delete()
                res = "unlike"
            else:
                like = gallerylike()
                like["user"] = {
                    "by": user["_id"],
                    "username": user["username"],
                    "on": crudmgo.utctime()
                }
                like["galleryid"] = self["_id"]
                like.save()
            self.collection.update({"_id": self["_id"]},
                                   {"$inc": {"meta.likes_count": 1 if res == "like" else -1}})

            self.reload()
            return res
        return None

    def save(self, *args, **kargs):
        if not self.get("meta"):
            self["meta"] = {}
        if "likes_count" not in self["meta"]:
            self["meta"]["likes_count"] = 0

        return super(Gallery, self).save(*args, **kargs)


class GalleryLike(crudmgo.RootDocument):
    __collection__ = "gallerylikes"

    structure = {
        "user": {
            "by": ObjectId,
            "username": basestring,
            "on": datetime.datetime
        },
        "galleryid": ObjectId
    }
    indexes = [
        {"fields": "user.by"},
        {"fields": ["galleryid", "user.by"],
         "unique": True}
    ]