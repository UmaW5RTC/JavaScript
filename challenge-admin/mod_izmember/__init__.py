# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask.ext import restful
from flask import jsonify
from mod_auth import current_user, acl
from rest import crudmgo
from rest import exportmgo

admin_izmember = crudmgo.CrudMgoBlueprint("admin_izmember", __name__, model="Membership")
admin_iztemember = crudmgo.CrudMgoBlueprint("admin_iztemember", __name__, model="SchoolMembership")


@admin_izmember.resource
class MemberList(crudmgo.ListAPI):
    method_decorators = [acl.requires_role("administrator")]
    sendcount = True

    def post(self):
        parser = restful.reqparse.RequestParser()
        # parser.add_argument("duration", type=int, store_missing=False)
        parser.add_argument("dqreport", type=int, store_missing=False)
        parser.add_argument("sponsor", type=unicode, store_missing=False)
        args = parser.parse_args()

        mem = self.model.new_member(0, args.get("dqreport", False), args.get("sponsor", ""), current_user)
        return jsonify(crudmgo.model_to_json(mem, is_single=True))

    def delete(self):
        return jsonify(success=True)


@admin_izmember.resource
class MemberItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("administrator")]


@admin_iztemember.resource
class TeacherMemberList(crudmgo.ListAPI):
    method_decorators = [acl.requires_role("administrator")]
    sendcount = True

    def post(self):
        parser = restful.reqparse.RequestParser()
        # parser.add_argument("duration", type=int, store_missing=False)
        parser.add_argument("count", type=int, store_missing=False)
        parser.add_argument("sponsor", type=unicode, store_missing=False)
        args = parser.parse_args()
        count = args.get("count", 0)
        sponsor = args.get("sponsor", "")

        mem = self.model.new_member(count, sponsor, current_user)
        return jsonify(crudmgo.model_to_json(mem, is_single=True))

    def delete(self):
        return jsonify(success=True)


@admin_iztemember.resource
class TeacherMemberItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("administrator")]


@admin_izmember.resource
class MemberExport(exportmgo.MgoExcelAPI):
    method_decorators = [acl.requires_role("administrator")]
    sheet_name = "izheroes"
    fields = [("username", "Username", 25),
              ("code", "Code", 20),
              ("started", "Date Start", 20),
              ("duration", "Duration", 20),
              ("expiry", "Expiry", 20),
              ("receipt", "Receipt", 25),
              ("byadminname", "Created By", 40)]


apiizmember = restful.Api(admin_izmember)
apiizmember.add_resource(MemberList, '/', endpoint='izmembers')
apiizmember.add_resource(MemberItem, '/item/<itemid>', endpoint='izmember')
apiizmember.add_resource(MemberExport, '/export', endpoint='export')

apiiztemember = restful.Api(admin_iztemember)
apiiztemember.add_resource(TeacherMemberList, '/', endpoint='iztemembers')
apiiztemember.add_resource(TeacherMemberItem, '/item/<itemid>', endpoint='iztemember')
