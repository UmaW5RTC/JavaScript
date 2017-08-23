# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask.ext import restful
from rest import crud
from mod_auth import acl

admin_izquiz = crud.CrudBlueprint('admin_izquiz', __name__, model="izquiz")


@admin_izquiz.resource
class IZQuizList(crud.ListAPI):
    readonly = True
    method_decorators = [acl.requires_role("administrator")]


api = restful.Api(admin_izquiz)
api.add_resource(IZQuizList, '/', endpoint='izquizes')