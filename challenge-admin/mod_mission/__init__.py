# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify
from flask.ext import restful
from rest import crud
from mod_auth import acl
from flask import current_app

admin_mission = crud.CrudBlueprint('admin_mission', __name__, model="mission")


@admin_mission.resource
class MissionList(crud.ListAPI):
    readonly = True
    method_decorators = [acl.requires_role("administrator")]


class UsersMissionList(crud.ListAPI):
    readonly = True
    method_decorators = [acl.requires_role("administrator")]

    def __init__(self):
        self.db = current_app.config["db"]
        self.model = current_app.config["model.users_mission"]

    def get(self, itemid=None):
        self.filter_by = {"missionid": itemid}
        return super(UsersMissionList, self).get()


class UsersMissionUploadList(crud.ListAPI):
    readonly = True
    method_decorators = [acl.requires_role("administrator")]
    _users_mission = None

    def __init__(self):
        self.db = current_app.config["db"]
        self.model = current_app.config["model.upload"]
        self._users_mission = current_app.config["model.users_mission"]

    def get(self, itemid=None):
        umission = self._users_mission.query.get(itemid)
        if umission is not None:
            self.filter_by = {"userid": umission.userid, "missionid": umission.missionid}
            return super(UsersMissionUploadList, self).get()
        return jsonify({})

api = restful.Api(admin_mission)
api.add_resource(MissionList, '/', endpoint='missions')
api.add_resource(UsersMissionList, '/item/<int:itemid>', endpoint='mission')
api.add_resource(UsersMissionUploadList, "/uploads/<int:itemid>", endpoint="uploads")