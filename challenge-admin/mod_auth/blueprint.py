# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify, Blueprint, current_app, request, abort
from flask.ext.restful import Resource, reqparse
from flask.ext import restful
from bson.objectid import ObjectId
from . import current_user, current_userid, current_session
from rest.crud import model_to_json, ItemAPI
from rest.crudmgo import model_to_json as model_mgo_to_json
from werkzeug.datastructures import MultiDict


class AuthLogin(Resource):
    @staticmethod
    def post():
        res = {"success": False}
        parser = reqparse.RequestParser()
        parser.add_argument("username", type=unicode, store_missing=False)
        parser.add_argument("password", type=unicode, store_missing=False)
        parser.add_argument("remember", type=bool, default=False)
        parser.add_argument("action", type=str, store_missing=False)  # TODO
        args = parser.parse_args()
        username = args.get("username", None)
        password = args.get("password", None)
        remember = args.get("remember", False)

        if username is not None and password is not None:
            res["success"], err = current_app.auth.login(username, password, remember)

            if res["success"]:
                res["user"] = model_mgo_to_json(current_user) \
                    if current_app.auth.is_mgo else model_to_json(current_user)
                res["user"].update({"__name__": current_app.auth.user.get_name(),
                                    "__username__": current_app.auth.user.get_username(),
                                    "__role__": current_app.auth.user.get_role(),
                                    "__remember__": remember})
            else:
                res["error"] = err

        return jsonify(res)


class AuthLogout(Resource):
    @staticmethod
    def post():
        current_app.auth.logout()
        return jsonify({"success": True})


class AuthUser(ItemAPI):
    is_mgo = False
    model_to_json = None

    def __init__(self):
        self.is_mgo = current_app.auth.is_mgo
        self.db = current_app.auth.mgo if self.is_mgo else current_app.auth.db
        if self.is_mgo:
            self.model = current_user._get_current_object().__class__
        else:
            self.model = current_app.auth.userdb
        self.model_to_json = model_mgo_to_json if self.is_mgo else model_to_json

    def get(self, itemid=None):
        d = self.model_to_json(current_user)
        d["__role__"] = current_user.get_role()
        d["__username__"] = current_user.get_username()
        d["__name__"] = current_user.get_name()
        return jsonify(d)

    def put(self, itemid=None):
        if current_userid:
            remove_from_request(self.model.__username_field__)
            remove_from_request(self.model.__status_field__)
            remove_from_request(self.model.__role_field__)
            if self.is_mgo:
                m = current_user._get_current_object()
                if m and not m.is_anonymous:
                    data = request.json if request.json is not None else request.form
                    m.update(**data)
                    m.save()
                    return jsonify(success=True)
            else:
                return super(AuthUser, self).put(current_userid)
        return jsonify(success=False)

    def delete(self, itemid):
        # TODO: deactivate user account?
        pass


class AuthSession(Resource):
    is_mgo = False
    model_to_json = None
    modify = False

    def __init__(self, *args, **kargs):
        super(AuthSession, self).__init__(*args, **kargs)
        self.is_mgo = bool(current_app.auth.mgo)
        self.model_to_json = model_mgo_to_json if self.is_mgo else model_to_json
        # TODO: get modify setting from current_app.auth

    def get(self):
        return jsonify(self.model_to_json(current_session))

    def post(self):
        if not self.modify:
            abort(403)

        data = MultiDict(request.json).to_dict(False) if request.json is not None else request.form
        newdata = {}
        if data:
            for k, v in data.items():
                newdata[k] = v[0] if isinstance(v, (list, tuple)) and len(v) == 1 else v
        if self.is_mgo:
            current_session["data"].update(**data)
        else:
            current_session.update(**data)
        return jsonify(success=True, session=self.model_to_json(current_session))

    def delete(self):
        if not self.modify:
            abort(403)

        parser = reqparse.RequestParser()
        parser.add_argument("key", type=str, action="append", default=[])
        parser.add_argument("clearall", type=bool, default=False)
        args = parser.parse_args()

        if args["clearall"]:
            if self.is_mgo:
                current_session["data"].clear()
            else:
                current_session.clear()
        else:
            if self.is_mgo:
                for key in args["key"]:
                    current_session["data"].pop(key, None)
            else:
                for key in args["key"]:
                    current_session.delete(key)
        return jsonify(success=True, session=self.model_to_json(current_session))


class AuthAccount(AuthUser):
    @staticmethod
    def get():
        u = current_user
        d = {"id": u.id,
             "username": u.get_username(),
             "role": u.get_role(),
             "name": u.get_name()} if not u.is_anonymous else {}
        return jsonify(d)


auth_bp = Blueprint("auth", __name__)

api = restful.Api(auth_bp)
api.add_resource(AuthLogin, "/login", endpoint="login")
api.add_resource(AuthLogout, "/logout", endpoint="logout")
api.add_resource(AuthUser, "/user", endpoint="user")
api.add_resource(AuthSession, "/session", endpoint="session")
api.add_resource(AuthAccount, "/account", endpoint="account")


def remove_from_request(name):
    if request.json and name in request.json:
        del(request.json[name])
    if request.form and name in request.form:
        del(request.form[name])