# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask.ext import restful
from flask import jsonify, current_app
from rest import crudmgo
from model.membership import humanify_code
import hashlib

api_member = crudmgo.CrudMgoBlueprint("api_member", __name__, model="Membership")


@api_member.resource
class KeyGen(restful.Resource):
    db = None
    model = None

    def post(self):
        secret = current_app.config.get("STORE_KEYGEN_SECRET", "WltokBKo4CEYnInur")
        parser = restful.reqparse.RequestParser()
        parser.add_argument("token", type=str, store_missing=False)
        parser.add_argument("order_id", type=str, store_missing=False)
        parser.add_argument("customer_email", type=unicode, store_missing=False)
        parser.add_argument("products", type=dict, store_missing=False, action="append")
        args = parser.parse_args()

        if not args.get("order_id"):
            return jsonify({"success": False, "error": "Missing order_id"})

        md5 = hashlib.md5()
        md5.update("%s-%s" % (secret, args["order_id"]))

        if md5.hexdigest() != args.get("token"):
            return jsonify({"success": False, "error": "Invalid token"})

        email = args.get("customer_email")
        products = args.get("products", [])
        res = {
            "success": True,
            "order_id": args["order_id"],
            "products": []
        }

        if not isinstance(products, (tuple, list)):
            products = [products]

        gi = 0
        for d in products:
            if not isinstance(d, dict):
                continue

            pid = d.get("product_id")

            try:
                qty = int(d.get("qty", 1))
            except (TypeError, ValueError):
                qty = 1

            if pid == "account-individual":
                keys = []
                res["products"].append({
                    "product_id": pid,
                    "qty": qty,
                    "keys": keys
                })
                for i in xrange(qty):
                    m = self.db["Membership"].new_member(orderid=args["order_id"],
                                                         i=i, email=email)
                    if m == 0:
                        m = self.db["Membership"].find_by_orderid_i(args["order_id"], i)
                    if m:
                        keys.append(humanify_code(m["code"]))
                    else:
                        return jsonify({"success": False, "error": "Database error"})

            elif pid == "account-group":
                m = self.db["SchoolMembership"].new_member(count=qty, orderid=args["order_id"],
                                                           i=gi, email=email)
                if m == 0:
                    m = self.db["SchoolMembership"].find_by_orderid_i(args["order_id"], gi)

                if m:
                    res["products"].append({
                        "product_id": pid,
                        "qty": qty,
                        "keys": [humanify_code(m["code"])]
                    })
                else:
                    return jsonify({"success": False, "error": "Database error"})
                gi += 1

            elif pid == "report-dqparent":
                keys = []
                res["products"].append({
                    "product_id": pid,
                    "qty": qty,
                    "keys": keys
                })
                for i in xrange(qty):
                    m = self.db["DQReportAccess"].new_dqreport(orderid=args["order_id"],
                                                               i=i, email=email)
                    if m == 0:
                        m = self.db["DQReportAccess"].find_by_orderid_i(args["order_id"], i)
                    if m:
                        keys.append(humanify_code(m["code"]))
                    else:
                        return jsonify({"success": False, "error": "Database error"})

        return jsonify(res)


apimember = restful.Api(api_member)
apimember.add_resource(KeyGen, '/keygen', endpoint='keygen')
apimember.add_resource(KeyGen, '/keygen/', endpoint='keygen_slash')
