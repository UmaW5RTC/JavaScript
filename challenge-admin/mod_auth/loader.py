# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask.views import View
from flask import current_app, json
from rest.crud import model_to_json
from rest.crudmgo import model_to_json as model_mgo_to_json


class Loader(View):
    def dispatch_request(self):
        u = current_app.auth.user

        if u.is_anonymous:
            d = {}
        elif current_app.auth.loader_full:
            d = model_mgo_to_json(u) if current_app.auth.is_mgo else model_to_json(u)
            d["__role__"] = u.get_role()
            d["__username__"] = u.get_username()
            d["__name__"] = u.get_name()
            d["__remember__"] = (current_app.auth.session.get("data") or {}).get("login_persist", False)
            if hasattr(u, "auth_loader_values"):
                d.update(u.auth_loader_values())
        else:
            d = {"id": current_app.auth.userid,
                 "username": u.get_username(),
                 "role": u.get_role(),
                 "name": u.get_name()}

        return current_app.response_class("window.user=" + json.dumps(d) + ";", mimetype='text/javascript')