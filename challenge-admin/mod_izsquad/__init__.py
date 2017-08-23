__author__ = 'n2m'

from flask import jsonify, abort
from flask.ext.restful import Api, reqparse
from rest import crudmgo, exportmgo
from mod_auth import acl


admin_izsquad = crudmgo.CrudMgoBlueprint("admin_izsquad", __name__, model="Teacher")


@admin_izsquad.resource
class IZSquadList(crudmgo.ListArrayAPI):
    method_decorators = [acl.requires_role("administrator")]
    sendcount = True
    unwind = "squads"

    def post(self):
        abort(404)

    def delete(self):
        pr = reqparse.RequestParser()
        pr.add_argument("code", type=str, action='append', store_missing=False)
        pr.add_argument("with_izhero", type=bool, store_missing=False)
        args = pr.parse_args()
        codes = args.get("code", [])

        if codes:
            self.model.collection.update({"squads": {"$ne": None}}, {"$pull": {"squads": {"code": {"$in": codes}}}},
                                         multi=True)

            if args.get("with_izhero"):
                filter_by = {"squad.code": {"$in": codes}, "lastlogin": None}

                for u in self.db["IZHero"].collection.find(filter_by):
                    self.model.collection.database.izheroesbin.insert(u)

                # self.db["IZHero"].collection.aggregate([{"$match": filter_by},
                #                                         {"$out": "izheroesbin"}])
                self.db["IZHero"].collection.remove(filter_by)

            self.db["IZHero"].collection.update({"squad.code": {"$in": codes}}, {"$set": {"squad.code": None,
                                                                                          "squad.name": None}},
                                                multi=True)

        return jsonify(success=True)


@admin_izsquad.resource
class IZSquadExport(exportmgo.MgoExcelArrayAPI):
    method_decorators = [acl.requires_role("administrator")]
    sheet_name = "iZ SQUADS"
    unwind = "squads"
    fields = [("squads.name", "Squad Name", 25),
              ("squads.code", "Squad Code", 15),
              ("squads.grade", "Grade", 10),
              ("squads.school", "School", 30),
              ("country", "Country", 20),
              ("username", "Username", 25),
              ("givenname", "Given Name", 20),
              ("familyname", "Family Name", 20),
              ("email", "Email", 40),
              ("contact", "Contact", 20)]


api = Api(admin_izsquad)
api.add_resource(IZSquadList, "", endpoint="izsquads")
api.add_resource(IZSquadList, "/", endpoint="izsquads_slash")
api.add_resource(IZSquadExport, '/export', endpoint='export')
