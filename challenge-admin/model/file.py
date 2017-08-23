# -*- coding: utf-8 -*-
__author__ = 'n2m'

from mod_auth import current_user
from rest import crudmgo
from bson import ObjectId
import datetime


class File(crudmgo.RootDocument):
    __collection__ = "files"

    structure = {
        "name": basestring,
        "filename": basestring,
        "folder": basestring,
        "meta": {},
        "group": bool,
        "public": bool,
        "created": {
            "by": ObjectId,
            "username": basestring,
            "on": datetime.datetime
        }
    }
    indexes = [
        {"fields": ["filename", "folder"]},
        {"fields": ["meta.type", "created.by", "_id"],
         "check": False},
        {"fields": ["meta.type", "_id"],
         "check": False}
    ]
    required = ["name", "filename"]
    default_values = {"group": False, "public": False, "created.on": crudmgo.localtime, "folder": "",
                      "created.by": lambda: current_user["_id"] if not current_user.is_anonymous else None,
                      "created.username": lambda: current_user.get("username") if not current_user.is_anonymous else None}


class FileBin(crudmgo.RootDocument):
    __collection__ = "filesbin"

    structure = {
        "_id": ObjectId,
        "name": basestring,
        "filename": basestring,
        "folder": basestring,
        "meta": {},
        "group": bool,
        "public": bool,
        "created": {
            "by": ObjectId,
            "username": basestring,
            "on": datetime.datetime
        }
    }
    indexes = [
        {"fields": ["filename", "folder"]},
        {"fields": ["meta.type", "created.by", "_id"],
         "check": False}
    ]
    required = ["name", "filename"]

    def trash(self, f):
        if isinstance(f, File) and f.get("_id"):
            self["_id"] = f["_id"]
            self["name"] = f.get("name")
            self["filename"] = f.get("filename")
            self["folder"] = f.get("folder")
            self["meta"] = f.get("meta")
            self["group"] = f.get("group")
            self["public"] = f.get("public")
            self["created"] = f.get("created")
            self.save()
            f.delete()
            return True
        return False

    def restore(self):
        if self.get("_id"):
            f = File()
            f["_id"] = self["_id"]
            f["name"] = self.get("name")
            f["filename"] = self.get("filename")
            f["folder"] = self.get("folder")
            f["meta"] = self.get("meta")
            f["group"] = self.get("group")
            f["public"] = self.get("public")
            f["created"] = self.get("created")
            f.save()
            self.delete()
            return True
        return False


class JustLoveEmailLog(crudmgo.RootDocument):
    __collection__ = "justloveemaillog"

    structure = {
        "email": basestring,
        "message": basestring,
        "link": basestring,
        "file": ObjectId,
        "sent": {
            "by": ObjectId,
            "username": basestring,
            "on": datetime.datetime
        }
    }
    default_values = {"sent.on": crudmgo.localtime,
                      "sent.by": lambda: current_user["_id"] if not current_user.is_anonymous else None,
                      "sent.username": lambda: current_user.get("username") if not current_user.is_anonymous else None}
