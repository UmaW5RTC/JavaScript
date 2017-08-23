# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask.ext import restful
from rest import crud
from mod_auth import acl

admin_power = crud.CrudBlueprint("admin_power", __name__, model="whatsyourpower")


@admin_power.resource
class PowerList(crud.ListAPI):
    method_decorators = [acl.requires_role("administrator")]


@admin_power.resource
class PowerItem(crud.ItemAPI):
    method_decorators = [acl.requires_role("administrator")]


@admin_power.resource
class PowerStatus(crud.ToggleAPI):
    method_decorators = [acl.requires_role("administrator")]
    toggle = "status"
    is_val = ("inactive", "active")


@admin_power.resource
class PowerShare(crud.ToggleAPI):
    method_decorators = [acl.requires_role("administrator")]
    toggle = "share"
    is_val = ("inactive", "active")


api = restful.Api(admin_power)
api.add_resource(PowerList, "/", endpoint="powers")
api.add_resource(PowerItem, "/item/<int:itemid>", endpoint="power")
api.add_resource(PowerStatus, "/status/<int:itemid>", endpoint="status")
api.add_resource(PowerShare, "/share/<int:itemid>", endpoint="share")