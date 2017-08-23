__author__ = 'n2m'

from rest import crudmgo
from flask.ext.restful import Api, Resource, reqparse


izhero_sub = crudmgo.CrudMgoBlueprint("izhero_subscribe", __name__, model="MailSubscription")


@izhero_sub.resource
class SubscriptionList(crudmgo.ListAPI):
    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass


api_subscription = Api(izhero_sub)
api_subscription.add_resource(SubscriptionList, "", endpoint="subcribe")
api_subscription.add_resource(SubscriptionList, "/", endpoint="subscribe_slash")
