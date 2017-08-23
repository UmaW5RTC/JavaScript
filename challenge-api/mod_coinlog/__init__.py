# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify, abort
from flask.ext.restful import Resource, Api, reqparse
from mod_auth import current_user, acl
from rest import crudmgo


coinlog = crudmgo.CrudMgoBlueprint("coinlog", __name__, model="CoinLog")


@coinlog.resource
class CoinGainLog(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self):
        log = self.model.getlog(current_user["_id"])
        return jsonify(items=crudmgo.to_flat_value(log.get("missions") or []), coins=current_user.get("coins"))


@coinlog.resource
class CoinDonateLog(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self):
        log = self.model.getlog(current_user["_id"])
        return jsonify(items=crudmgo.to_flat_value(log.get("donations") or []), donated=current_user.get("donated"))


@coinlog.resource
class CoinPurchaseLog(Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self):
        log = self.model.getlog(current_user["_id"])
        return jsonify(items=crudmgo.to_flat_value(log.get("purchases") or []))


api_comiclog = Api(coinlog)
api_comiclog.add_resource(CoinGainLog, "/gain", endpoint="gain")
api_comiclog.add_resource(CoinDonateLog, "/donate", endpoint="donate")
api_comiclog.add_resource(CoinDonateLog, "/purchase", endpoint="purchase")