__author__ = 'n2m'

from rest import crudmgo
from bson import ObjectId


class EncycloCategory(crudmgo.RootDocument):
    __collection__ = "encyclocategories"

    structure = {
        "uname": basestring,
        "name": basestring,
        "titleimg": basestring,
        "charimg": basestring,
        "baseimg": basestring,
        "order": int,
        "parent": ObjectId,
        "lang": basestring
    }
    indexes = [
        {"fields": ["parent"],
         "check": False}
    ]
    default_values = {"lang": "en"}

    def update_parent(self, value):
        if isinstance(value, ObjectId):
            self['parent'] = value
        elif ObjectId.is_valid(value):
            self['parent'] = ObjectId(value)
        elif value is None:
            self['parent'] = None


class EncycloArticle(crudmgo.RootDocument):
    __collection__ = "encycloarticles"

    structure = {
        "uname": basestring,
        "name": basestring,
        "titleimg": basestring,
        "charimg": basestring,
        "descr": basestring,
        "order": int,
        "category": ObjectId,
        "lang": basestring
    }
    indexes = [
        {"fields": ["category"],
         "check": False}
    ]
    default_values = {"lang": "en"}

    def update_category(self, value):
        if isinstance(value, ObjectId):
            self['category'] = value
        elif ObjectId.is_valid(value):
            self['category'] = ObjectId(value)
