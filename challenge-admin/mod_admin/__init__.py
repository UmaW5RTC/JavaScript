# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask.ext import restful
from rest import crudmgo
from mod_auth import acl

admin_admin = crudmgo.CrudMgoBlueprint('admin_admin', __name__, model="Administrator")


@admin_admin.resource
class AdminList(crudmgo.ListAPI):
    method_decorators = [acl.requires_role("administrator")]


@admin_admin.resource
class AdminItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("administrator")]


@admin_admin.resource
class AdminStatus(crudmgo.ToggleAPI):
    method_decorators = [acl.requires_role("administrator")]
    toggle = "status"


api = restful.Api(admin_admin)
api.add_resource(AdminList, '/', endpoint='admins')
api.add_resource(AdminItem, '/item/<itemid>', endpoint='admin')
api.add_resource(AdminStatus, '/status/<itemid>', endpoint='status')