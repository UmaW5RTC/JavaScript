# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask.ext import restful
from flask import jsonify, abort, current_app, render_template, request, redirect, url_for
from mod_auth import current_user, acl, model
from mod_sendmail import sendmail
from rest import crudmgo
from bson.objectid import ObjectId
from rest import exportmgo
from model import membership
import re
import os

admin_country = crudmgo.CrudMgoBlueprint("admin_country", __name__, model="Country")
admin_izhero = crudmgo.CrudMgoBlueprint("admin_izhero", __name__, model="IZHero")
admin_school = crudmgo.CrudMgoBlueprint('admin_school', __name__, model="Country")
admin_teacher = crudmgo.CrudMgoBlueprint('admin_teacher', __name__, model="Teacher", template_folder="templates")
username_ic = re.compile(r"^[sgt]?[\.\/\\]?[\d]{7}[\.\/\\]?[a-z]?$", re.I)
whitespace = re.compile(r"\s")

lang_list = ("en", "ko", "es")

@admin_country.resource
class CountryList(crudmgo.ListAPI):
    method_decorators = [acl.requires_role("administrator")]


@admin_country.resource
class CountryItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("administrator")]

    def _updateitem(self, itemid, data):
        country = self._getitem(itemid)
        if country:
            prevname = country["name"]
            item, err = super(CountryItem, self)._updateitem(itemid, data)
            if item is not None and item["name"] != prevname:
                self.db["IZHero"].collection.update({"country": prevname}, {"$set": {"country": item["name"]}})
                self.db["Teacher"].collection.update({"country": prevname}, {"$set": {"country": item["name"]}})
            return item, err
        return None, "Country not found."


@admin_school.resource
class SchoolList(crudmgo.ListAPI):
    method_decorators = [acl.requires_role("administrator")]

    def get(self, country=None):
        country, _, _ = self.getargs(country)
        c = self.model.find_one({"name": country})
        return jsonify(schools=c["schools"] if c and "schools" in c else [])

    def post(self, country=None):
        country, school_name, _ = self.getargs(country)

        if school_name and country:
            c = self.model.find_one({"name": country})
            if c:
                schools = c.get("schools")
                if not schools:
                    c["schools"] = [school_name]
                elif school_name not in schools:
                    c["schools"].append(school_name)
                c.save()

                return jsonify(success=True)
            return jsonify(success=False, error="Country not found.")

        return jsonify(success=False, error="Country and school name must be provided.")

    def put(self, country=None):
        country, school_name, prev_school = self.getargs(country)

        if prev_school and school_name and country and prev_school != school_name:
            c = self.model.find_one({"name": country, "schools": prev_school})
            if c:
                for i in xrange(len(c["schools"])):
                    if c["schools"][i] == prev_school:
                        c["schools"][i] = school_name
                        break
                c.save()
                self.db["IZHero"].collection.update({"country": country, "school": prev_school},
                                                    {"$set": {"school": school_name}})
                self.db["Teacher"].collection.update({"country": country, "squads.school": prev_school},
                                                     {"$set": {"squads.$.school": school_name}})

                return jsonify(success=True)
            return jsonify(success=False, error="Country not found.")
        return jsonify(success=False, error="Country and school name must be provided.")

    @staticmethod
    def getargs(country):
        parser = restful.reqparse.RequestParser()
        parser.add_argument("name", type=unicode, store_missing=False)
        parser.add_argument("prevname", type=unicode, store_missing=False)
        parser.add_argument("country", type=unicode, store_missing=False)
        args = parser.parse_args()
        school_name = args.get("name")
        prev_school = args.get("prevname")
        if country is None:
            country = args.get("country")
        return country, school_name, prev_school


@admin_school.resource
class SchoolUnverifList(crudmgo.ListAPI):
    method_decorators = [acl.requires_role("administrator")]

    def get(self, country=None):
        if country is None:
            parser = restful.reqparse.RequestParser()
            parser.add_argument("country", type=unicode, store_missing=False)
            args = parser.parse_args()
            country = args.get("country", "Singapore")

        c = self.model.find_one({"name": country})
        return jsonify(schools=c["schools_unverified"] if c and "schools_unverified" in c else [])

    def post(self):
        abort(404)


@admin_school.resource
class SchoolUnverifItem(restful.Resource):
    method_decorators = [acl.requires_role("administrator")]

    def get(self, country=None, school=None):
        heroes = [{"_id": str(h["_id"]), "username": h["username"]} for h in self.db["IZHero"].find({"country": country,
                                                                                                     "school": school,
                                                                                                     "squad.code": {"$in": [None, ""]}})]
        squads = []
        for teach in self.db["Teacher"].find({"country": country, "squads.school": school}):
            for s in teach["squads"]:
                if s["school"] == school:
                    squads.append({"code": s["code"], "name": s["name"]})
        teachers = [{"_id": str(t["_id"]), "username": t["username"]} for t in self.db["Teacher"].find({"country": country, "school": school})]
        return jsonify(izheroes=heroes, squads=squads, teachers=teachers)

    def put(self, country=None, school=None, rename=None):
        parser = restful.reqparse.RequestParser()
        parser.add_argument("country", type=unicode, store_missing=False)
        parser.add_argument("school", type=unicode, store_missing=False)
        parser.add_argument("rename", type=unicode, store_missing=False)
        parser.add_argument("update_all", type=str, store_missing=False)
        parser.add_argument("update_all_users", type=str, store_missing=False)
        parser.add_argument("update_all_teachers", type=str, store_missing=False)
        parser.add_argument("update_all_squads", type=str, store_missing=False)
        parser.add_argument("users_id", type=str, action="append", store_missing=False)
        parser.add_argument("teachers_id", type=str, action="append", store_missing=False)
        parser.add_argument("squads_id", type=str, action="append", store_missing=False)
        args = parser.parse_args()

        if country is None:
            country = args.get("country")
        if school is None:
            school = args.get("school")
        if rename is None:
            rename = args.get("rename")

        if not country or not school or not rename:
            return jsonify(success=False)

        c = self.model.find_one({"name": country, "schools_unverified": school}, fields=["name",
                                                                                         "schools_unverified.$",
                                                                                         "created"])
        if not c:
            abort(404)

        # self.model.collection.update({"name": country, "schools_unverified": school},
        #                              {"$set": {"schools_unverified.$": rename}})

        if args.get("update_all", "").lower() == "true":
            self.db["IZHero"].collection.update({"country": country, "school": school},
                                                {"$set": {"school": rename}},
                                                multi=True)
            self.db["Teacher"].collection.update({"country": country, "school": school},
                                                 {"$set": {"school": rename}},
                                                 multi=True)
            self.db["Teacher"].collection.update({"country": country, "squads.school": school},
                                                 {"$set": {"squads.$.school": rename}},
                                                 multi=True)
        else:
            if args.get("update_all_teachers", "").lower() == "true":
                self.db["Teacher"].collection.update({"country": country, "school": school},
                                                     {"$set": {"school": rename}},
                                                     multi=True)
            elif args.get("teachers_id"):
                teachers_ids = [ObjectId(t) for t in args["teachers_id"]]
                self.db["Teacher"].collection.update({"_id": {"$in": teachers_ids}},
                                                     {"$set": {"school": rename}},
                                                     multi=True)

            if args.get("update_all_squads", "").lower() == "true":
                squads = self.db["Teacher"].collection.find({"country": country, "squads.school": school},
                                                            fields=["squads.$"])
                codes = [squad["code"] for squad in squads]

                self.db["IZHero"].collection.update({"squad.code": {"$in": codes}},
                                                    {"$set": {"school": rename}},
                                                    multi=True)
                self.db["Teacher"].collection.update({"country": country, "squads.school": school},
                                                     {"$set": {"squads.$.school": rename}},
                                                     multi=True)
            elif args.get("squads_id"):
                self.db["IZHero"].collection.update({"squad.code": {"$in": args["squads_id"]}},
                                                    {"$set": {"school": rename}},
                                                    multi=True)
                self.db["Teacher"].collection.update({"squads.code": {"$in": args["squads_id"]}},
                                                     {"$set": {"squads.$.school": rename}},
                                                     multi=True)

            if args.get("update_all_users", "").lower() == "true":
                self.db["IZHero"].collection.update({"country": country, "school": school},
                                                    {"$set": {"school": rename}},
                                                    multi=True)
            elif args.get("users_id"):
                user_ids = [ObjectId(u) for u in args["users_id"]]
                self.db["IZHero"].collection.update({"_id": {"$in": user_ids}},
                                                    {"$set": {"school": rename}},
                                                    multi=True)

        return jsonify(success=True)


@admin_izhero.resource
class StudentList(crudmgo.ListAPI):
    method_decorators = [acl.requires_role(["administrator", "counselor"])]
    sendcount = True

    def delete(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("id", type=str, action='append', store_missing=False)
        args = pr.parse_args()
        ids = args.get("id", [])

        if ids:
            for i in xrange(len(ids)):
                if ObjectId.is_valid(ids[i]):
                    ids[i] = ObjectId(ids[i])
            filter_by = {"_id": {"$in": ids}, "teacher": {"$ne": True}, "username": {"$ne": None}}
            for u in self.model.collection.find(filter_by):
                self.model.collection.database.izheroesbin.insert(u)
            # self.model.collection.aggregate([{"$match": filter_by},
            #                                  {"$out": "izheroesbin"}])
            self.model.collection.remove(filter_by)
        return jsonify(success=True)


@admin_izhero.resource
class StudentItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role(["administrator", "counselor"])]


@admin_izhero.resource
class StudentStatus(crudmgo.ToggleAPI):
    method_decorators = [acl.requires_role("administrator")]
    toggle = "status"


@admin_izhero.resource
class StudentGuardAck(crudmgo.ToggleAPI):
    method_decorators = [acl.requires_role("administrator")]
    toggle = "guardiansack"


@admin_izhero.resource
class StudentExport(exportmgo.MgoExcelAPI):
    method_decorators = [acl.requires_role("administrator")]
    sheet_name = "izheroes"
    fields = [("username", "Username", 25),
              ("givenname", "Given Name", 20),
              ("familyname", "Family Name", 20),
              ("dob", "Date of Birth", 20),
              ("country", "Country", 20),
              ("school", "School Name", 25),
              ("parent.email", "Parent's Email", 40),
              ("parent.givenname", "Parent's Given Name", 20),
              ("parent.familyname", "Parent's Family Name", 20),
              ("points", "Points", 10),
              ("dq_points", "Score", 10),
              ("created", "Created Date", 20),
              ("lastlogin", "Last Login", 20),
              ("squad.name", "Squad Name", 20),
              ("squad.code", "Squad Code", 20),
              ("coins", "Coins", 10),
              ("dq_coins", "DQ Coins", 10),
              ("dq_level", "DQ Level", 10),
              ("donated", "Donated", 10),
              ("dq_progress.screentimebadge.first", "Screen Time Badge", 20),
              ("dq_progress.privacybadge.first", "Privacy Badge", 20),
              ("dq_progress.cyberbullyingbadge.first", "Cyberbullying Badge", 20),
              ("dq_progress.digitalcitizensbadge.first", "Digital Citizens Badge", 20),
              ("dq_progress.digitalfootprintbadge.first", "Digital Footprint Badge", 20),
              ("dq_progress.securitybadge.first", "Security Badge", 20),
              ("dq_progress.criticalthinkingbadge.first", "Critical Thinking Badge", 20),
              ("dq_progress.empathybadge.first", "Empathy Badge", 20),
              # ("points_stage.e2", "iZ RADAR iZPs", 20),
              # ("points_stage.e1", "iZ EYES iZPs", 20),
              # ("points_stage.e5", "iZ SHOUT iZPs", 20),
              # ("points_stage.e4", "iZ PROTECT iZPs", 20),
              # ("points_stage.e6", "iZ EARS iZPs", 20),
              # ("points_stage.e3", "iZ CONTROL iZPs", 20),
              # ("points_stage.e7", "iZ TELEPORT iZPs", 20),
              # ("progress.2._completed", "iZ RADAR Complete", 20),
              # ("progress.1._completed", "iZ EYES Complete", 20),
              # ("progress.5._completed", "iZ SHOUT Complete", 20),
              # ("progress.4._completed", "iZ PROTECT Complete", 20),
              # ("progress.6._completed", "iZ EARS Complete", 20),
              # ("progress.3._completed", "iZ CONTROL Complete", 20),
              # ("progress.7._completed", "iZ TELEPORT Complete", 20),
              ("guardiansack", "Guardian's Acknowledge", 22),
              ("teacher", "Teacher's Account", 22)]


@admin_izhero.resource
class StudentUpdate(restful.Resource):
    method_decorators = [acl.requires_role("administrator")]

    def post(self, itemid):
        itemid = ObjectId(itemid)
        izhero = self.model.find_one({"_id": itemid})

        if not izhero:
            abort(404)

        if izhero.get("teacher"):
            izhero = self.db["Teacher"].find_one({"username": izhero["username"]})
            email_addr = izhero["email"]
        else:
            email_addr = izhero["parent"]["email"]

        if izhero["activationcode"]:
            pr = restful.reqparse.RequestParser()
            pr.add_argument("lang", type=str, store_missing=False)
            args = pr.parse_args()

            tmpl = "/izhero_activation.html"
            lang = args.get("lang", "en")
            lang = lang if lang in lang_list else "en"
            tmpl = (lang + tmpl) if lang in lang_list else "en" + tmpl

            title = {
                "ko": u"[DQ 월드] 귀하의 자녀가 DQ 월드에 가입했습니다. 학습을 시작하려면 7일 안에 계정을 활성화해 주세요.",
                "en": u"[DQ World] Your child has signed up for DQ World™",
                "es": u"[DQ World] Su hijo(a) se acaba de inscribir en DQ World™"
            }
            sendmail(email_addr,
                     title[lang],
                     render_template(tmpl,
                                     url_root=os.path.dirname(request.url_root[:-1]) + '/',
                                     **izhero))
            return jsonify(success=True)
        return jsonify(success=False)

    def put(self, itemid):
        itemid = ObjectId(itemid)
        izhero = self.model.find_one({"_id": itemid})

        if izhero:
            parser = restful.reqparse.RequestParser()
            parser.add_argument("points", type=int, store_missing=False)
            parser.add_argument("coins", type=int, store_missing=False)
            parser.add_argument("guardiansack", type=str, store_missing=False)
            parser.add_argument("username", type=unicode, store_missing=False)
            args = parser.parse_args()
            points = args.get("points")
            coins = args.get("coins")
            guardiansack = args.get("guardiansack")
            username = self.model.normalize_username(args.get("username", "").strip())

            if username and username != izhero['username']:
                if len(username) < 3 or " " in username:
                    return jsonify(success=False, errorcode=101)

                if self.model.find_one({"username": username}):
                    return jsonify(success=False, errorcode=102)

                izhero['username'] = username

            if points is not None:
                izhero['points'] = points
            if coins is not None:
                izhero['coins'] = coins
            if guardiansack:
                izhero['guardiansack'] = bool(guardiansack.lower()[0] not in '0fn')

            izhero.save()
            return jsonify(success=True)
        return jsonify(success=False)


@admin_teacher.resource
class TeacherList(crudmgo.ListAPI):
    method_decorators = [acl.requires_role("administrator")]


@admin_teacher.resource
class TeacherItem(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("administrator")]
    __item = None

    def put(self, itemid=None):
        result = super(TeacherItem, self)._put(itemid)
        if result["success"]:
            self.db["IZHero"].collection.update({"username": self.__item["username"]},
                                                {"$set": {"password": self.__item.get("password"),
                                                          "country": self.__item.get("country"),
                                                          "school": self.__item.get("school"),
                                                          "familyname": self.__item.get("familyname"),
                                                          "givenname": self.__item.get("givenname")}})
        return jsonify(result)

    def _updateitem(self, itemid, data, item=None):
        item, err = super(TeacherItem, self)._updateitem(itemid, data, item)
        self.__item = item
        return item, err


@admin_teacher.resource
class TeacherStatus(crudmgo.ToggleAPI):
    method_decorators = [acl.requires_role("administrator")]
    toggle = "status"


@admin_teacher.resource
class TeacherExport(exportmgo.MgoExcelAPI):
    method_decorators = [acl.requires_role("administrator")]
    sheet_name = "teachers"
    fields = [("username", "Username", 25),
              ("givenname", "Given Name", 20),
              ("familyname", "Family Name", 20),
              ("email", "Email", 40),
              ("country", "Country", 20),
              ("school", "School", 30),
              ("referral", "Access Code", 15),
              ("contact", "Phone Number", 25),
              ("created", "Created Date", 20),
              ("lastlogin", "Last Login", 20)]


@admin_teacher.resource
class TeacherRegistration(crudmgo.ListAPI):
    teacher = None

    # check username and email's availability
    def get(self):
        parser = restful.reqparse.RequestParser()
        parser.add_argument("email", type=unicode, store_missing=False)
        parser.add_argument("username", type=unicode, store_missing=False)
        args = parser.parse_args()
        email = args.get("email")
        username = args.get("username")
        filt = {}

        if email:
            filt["email"] = email

        if username:
            username = self.model.normalize_username(username)
            if filt:
                filt = {"$or": [filt, {"username": username}]}
            else:
                filt["username"] = username

        success = (not username or ' ' not in username) and not (filt and self.model.find_one(filt, {"_id": 1}))
        if success and username:
            success = not username_ic.match(username) and not self.db["IZHero"].find_one({"username": username}, {"_id": 1})

        return jsonify(success=success)

    def post(self):
        if current_app.config.get('DISABLE_REGISTRATION'):
            return jsonify(success=False, errors={"registration": "disabled"})

        result = self._post()
        if result["success"] and self.teacher:
            pr = restful.reqparse.RequestParser()
            pr.add_argument("lang", type=str, store_missing=False)
            args = pr.parse_args()

            self.teacher.create_alt_izhero(True, "")  # "LG U+" if args.get("lang", "en") == "ko" else "Singtel")

            tmpl = "/activation.html"
            lang = args.get("lang", "en")
            lang = lang if lang in lang_list else "en"
            tmpl = (lang + tmpl) if lang in lang_list else "en" + tmpl

            title = {
                "ko": u"[DQ 월드] 귀하는 DQ 월드에 가입했습니다.",
                "en": "[DQ World] Activate your DQ World account!",
                "es": u"[DQ World] ¡Activa tu cuenta de DQ World™!"
            }

            sendmail(self.teacher["email"],
                     title[lang],
                     render_template(tmpl,
                                     url_root=os.path.dirname(request.url_root[:-1]) + '/',
                                     **self.teacher))
        return jsonify(result)

    def check_username(self, username):
        u = {"username": username}
        return not self.model.find_one(u, {"_id": 1}) and not self.db["IZHero"].find_one(u, {"_id": 1})

    def _formitem(self):
        item, err = super(TeacherRegistration, self)._formitem()
        if item is not None and not err:
            self.db["Country"].insert_school(item["country"], item["school"])

            item["username"] = self.model.normalize_username(item["username"])
            if not self.check_username(item["username"]):
                return None, {"username": "Username is already in used."}
            item["activationcode"] = model.generate_code()
            item["squads"] = None
            item["status"] = False
            self.teacher = item
        return item, err


@admin_teacher.resource
class TeacherAccessCode(restful.Resource):
    method_decorators = [acl.requires_role("Teacher")]

    def get(self):
        accesscodes = current_user.get("accesscode")
        count = 0
        assigned = 0
        if accesscodes:
            accesscodes = current_user["accesscode"]
            for ac in accesscodes:
                mem = self.db["SchoolMembership"].find_one({"code": ac, "userid": current_user.id})
                if mem is not None:
                    count += mem["membership"]["count"]
                    assigned += mem["membership"]["assigned"]
        return jsonify(count=count, assigned=assigned)

    def post(self):
        parser = restful.reqparse.RequestParser()
        parser.add_argument("membership", type=unicode, store_missing=False)
        args = parser.parse_args()

        if not args.get("membership"):
            return jsonify(success=False)

        mcode = membership.parse_code(args["membership"])
        has_membership = None

        if mcode:
            has_membership = self.db["SchoolMembership"].find_one({"code": mcode, "userid": None})
        if not has_membership:
            return jsonify(success=False, errors={"membership_code": "incorrect"})

        has_membership["userid"] = current_user["_id"]
        has_membership["username"] = current_user["username"]
        has_membership.save()
        if not current_user.get("accesscode"):
            current_user["accesscode"] = []
            self.db["IZHero"].collection.update({"username": current_user["username"]}, {"$set": {"fullaccess": True,
                                                                                                  "accesscode": mcode}})
        current_user["accesscode"].append(mcode)
        current_user.save()
        return jsonify(success=True, count=has_membership["membership"]["count"])


@admin_teacher.resource
class TeacherUpdate(crudmgo.ItemAPI):
    old_password = None
    method_decorators = [acl.requires_role("Teacher")]

    def put(self, itemid=None):
        self.old_password = current_user["password"]
        result = super(TeacherUpdate, self)._put(str(current_user.get("_id")))
        if result["success"]:
            self.db["IZHero"].collection.update({"username": current_user["username"]},
                                                {"$set": {"password": current_user["password"],
                                                          "country": current_user["country"],
                                                          "school": current_user["school"],
                                                          "familyname": current_user["familyname"],
                                                          "givenname": current_user["givenname"],
                                                          "username": current_user["username"]}})
        return jsonify(result)

    def _getitem(self, _):
        return current_user._get_current_object()

    def _updateitem(self, itemid, data):
        item, err = super(TeacherUpdate, self)._updateitem(itemid, data)

        if not err and item is not None:
            err = {}
            if item["password"] != self.old_password:
                pr = restful.reqparse.RequestParser()
                pr.add_argument("oldpassword", type=unicode, store_missing=False)
                args = pr.parse_args()
                newpass = item["password"]
                item["password"] = self.old_password
                if args.get("oldpassword") and item.authenticate(args["oldpassword"]):
                    item["password"] = newpass
                else:
                    err["password"] = "Incorrect password"
                    item = None

        return item, err


@admin_teacher.resource
class TeacherActivation(restful.Resource):
    db = None
    model = None

    def get(self, itemid=None):
        item = self.model.find_one({"_id": ObjectId(itemid)}) if itemid else None
        res = self.activate(item)
        pr = restful.reqparse.RequestParser()
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()

        if res["success"]:
            link = "/lang:%s/zone/menu?activated=1" % args.get('lang', 'en')  # url_for('client.index', _external=True)
        else:
            link = url_for('client.activate', lang=args.get('lang', 'en'), _external=True)

        return redirect(link, 303)

    def post(self, itemid=None):
        item = self.model.find_one({"_id": ObjectId(itemid)}) if itemid else None
        return jsonify(self.activate(item))

    def put(self, itemid=None):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("username", type=unicode, store_missing=False)
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()
        teach = None

        if args.get("username"):
            teach = self.model.find_one({"username": args.get("username")})
        elif itemid:
            itemid = ObjectId(itemid)
            teach = self.model.find_one({"_id": itemid})

        if not teach and current_user._get_current_object() and current_user.has_role("teacher"):
            teach = current_user
        elif not teach:
            return jsonify(success=False)

        if teach["activationcode"]:
            tmpl = "/activation.html"
            lang = args.get("lang", "en")
            lang = lang if lang in lang_list else "en"
            tmpl = (lang + tmpl) if lang in lang_list else "en" + tmpl

            title = {
                "ko": u"[DQ 월드] 귀하는 DQ 월드에 가입했습니다.",
                "en": "[DQ World] Activate your DQ World account!",
                "es": u"[DQ World] ¡Activa tu cuenta de DQ World™!"
            }
            sendmail(teach["email"],
                     title[lang],
                     render_template(tmpl,
                                     url_root=os.path.dirname(request.url_root[:-1]) + '/',
                                     **teach))

            return jsonify(success=True)
        return jsonify(success=False)

    def activate(self, item):
        parser = restful.reqparse.RequestParser()
        parser.add_argument("username", type=unicode, store_missing=False)
        parser.add_argument("id", type=str, store_missing=False)
        parser.add_argument("code", type=str, store_missing=False)
        args = parser.parse_args()

        if item is None and (args.get("username") or args.get("id")):
            username = args.get("username")
            uid = args.get("id")
            item = self.model.find_one({"username": self.model.normalize_username(username)} if username else {"_id": ObjectId(uid)})

        if item is not None:
            code = args.get("code")

            if code and code.strip() == item["activationcode"]:
                item["activationcode"] = ""
                item["status"] = True
                item.save()

                izhero = self.db["IZHero"].find_one({"username": item["username"]})
                if izhero:
                    izhero["activationcode"] = ""
                    izhero["guardiansack"] = True
                    izhero.save()

                current_app.auth.login_user(item)
                return dict(success=True, user=crudmgo.model_to_json(item))
            return dict(success=False, error="Incorrect activation code.")

        return dict(success=False, error="Account does not exists")


@admin_teacher.resource
class TeacherSquad(restful.Resource):
    method_decorators = [acl.requires_role("Teacher")]
    db = None
    model = None
    _teacherName = None

    def __init__(self, *args, **kargs):
        super(TeacherSquad, self).__init__(*args, **kargs)
        self._teacherName = {}

    def get(self, code=None):
        if not code:
            squads = []
            if current_user["squads"]:
                for s in current_user["squads"]:
                    squads.append(self._squadinfo(s))
            if current_user.get("assigned_squads"):
                for s in current_user["assigned_squads"]:
                    squads.append(self._squadinfo(s))
            return jsonify(squads=squads)
        elif current_user["squads"]:
            all_squads = current_user["squads"] + current_user.get("assigned_squads", [])
            for squad in all_squads:
                if squad["code"] == code:
                    return jsonify(self._squadinfo(squad))
        return jsonify({})

    def _squadinfo(self, squad):
        squad = squad.copy()
        squad["points"] = 0
        squad["dq_points"] = 0
        squad["donated"] = 0
        squad["members_count"] = 0
        squad["homeroom_teacher"] = str(squad.get("homeroom_teacher", ""))
        squad["homeroom_teacher_name"] = current_user["givenname"]

        if squad["homeroom_teacher"] and squad["homeroom_teacher"] != current_user["_id"]:
            if squad["homeroom_teacher"] in self._teacherName:
                squad["homeroom_teacher_name"] = self._teacherName[squad["homeroom_teacher"]]
            else:
                t = self.model.find_one({"_id": ObjectId(squad["homeroom_teacher"])})
                if t:
                    squad["homeroom_teacher_name"] = t.get("givenname", "")
                self._teacherName[squad["homeroom_teacher"]] = squad["homeroom_teacher_name"]

        for izhero in self.db["IZHero"].find({"squad.code": squad["code"]}):
            squad["points"] += izhero["points"]
            squad["dq_points"] += (izhero.get("dq_points") or 0)
            squad["donated"] += (izhero.get("donated") or 0)
            squad["members_count"] += 1
        return squad

    def post(self):
        if current_app.config.get('DISABLE_REGISTRATION'):
            return jsonify(success=False, errors={"registration": "disabled"})
        if current_user.get("hod"):
            return jsonify(success=False, errors={"account": "account is not a school account"})

        name, school, grade, mem_count, email, givenname, familyname, lang = self.get_reqvalues()
        if not school:
            school = current_user["school"]

        if name and school and grade:
            code = self.model.generate_squadcode()
            while self.model.find_one({"squads.code": code}) is not None:
                code = self.model.generate_squadcode()

            self.check_school(school)
            homeroom_teacher = current_user["_id"]

            if email and email != current_user["email"]:
                assigned_to = self.model.find_one({"email": email})
                a_squad = {
                    "code": code,
                    "name": name,
                    "school": school,
                    "grade": grade
                }
                if assigned_to:
                    if not assigned_to.get("hod"):
                        return jsonify(success=False,
                                       errors={"teacher": "teacher cannot be a school account"})
                    elif assigned_to["hod"] != current_user["_id"]:
                        return jsonify(success=False,
                                       errors={"teacher": "teacher is not under this school account"})

                    homeroom_teacher = assigned_to["_id"]
                    if not assigned_to.get("assigned_squads"):
                        assigned_to["assigned_squads"] = []
                    assigned_to["assigned_squads"].append(a_squad)
                    assigned_to.save()
                else:
                    assigned_to = self._create_teacher(lang, email, familyname, givenname, current_user["country"],
                                                       current_user["school"], current_user, a_squad)

                    if assigned_to:
                        homeroom_teacher = assigned_to["_id"]
                    else:
                        return jsonify(success=False,
                                       errors={"teacher": "an account with username of email exists"})

            squad = {"code": code, "name": name, "school": school, "grade": grade,
                     "homeroom_teacher": homeroom_teacher}
            if not current_user["squads"]:
                current_user["squads"] = [squad]
            else:
                current_user["squads"].append(squad)

            current_user.save()

            if mem_count:
                self.generate_members(squad, mem_count)

            return jsonify(success=True, code=code)

        errors = {}
        if not name:
            errors["name"] = "Name is required."
        if not school:
            errors["school"] = "School is required"
        if not grade:
            errors["grade"] = "Grade is required"

        return jsonify(success=False, errors=errors)

    def put(self, code):
        squad = None
        for s in current_user["squads"]:
            if s["code"] == code:
                squad = s
                break

        if squad is not None:
            name, school, grade, mem_count, email, givenname, familyname, lang = self.get_reqvalues()
            updated = False
            updated_sub = False

            if name and squad["name"] != name:
                squad["name"] = name
                updated = True
            if school and squad["school"] != school:
                self.check_school(school)
                squad["school"] = school
                updated = True
            if grade and squad["grade"] != grade:
                squad["grade"] = grade
                updated = True
            if email:
                t = self.model.find_one({"email": email})
                a_squad = {
                    "code": squad["code"],
                    "name": squad["name"],
                    "school": squad["school"],
                    "grade": squad["grade"]
                }
                if t is None:
                    t = self._create_teacher(lang, email, familyname, givenname, current_user.get("country"),
                                             current_user.get("school"), current_user, a_squad)
                    if t:
                        squad["homeroom_teacher"] = t["_id"]
                        updated_sub = True
                        updated = True
                elif t["_id"] != squad.get("homeroom_teacher") and (t.get("hod") == current_user["_id"] or
                                                                    t["_id"] == current_user["_id"]):
                    if squad.get("homeroom_teacher") and squad["homeroom_teacher"] != current_user["_id"]:
                        self.model.collection.update({"_id": squad["homeroom_teacher"]},
                                                     {"$pull": {"assigned_squads": {"code": squad["code"]}}})
                    squad["homeroom_teacher"] = t["_id"]
                    updated = True

                    if not t.has_squad(a_squad["code"]):
                        if not t.get("assigned_squads"):
                            t["assigned_squads"] = []
                        t["assigned_squads"].append(a_squad)
                        t.save()
                        updated_sub = True

            if updated:
                if not updated_sub:
                    self.model.collection.update({"assigned_squads.code": squad["code"]},
                                                 {"$set": {"assigned_squads.$.name": squad["name"],
                                                           "assigned_squads.$.school": squad["school"],
                                                           "assigned_squads.$.grade": squad["grade"]}})
                current_user.save()

            if mem_count and not current_app.config.get('DISABLE_REGISTRATION'):
                self.generate_members(squad, mem_count)

            return jsonify(success=True)

        return jsonify(success=False, error="Squad not found.")

    def check_school(self, school):
        if not school:
            return

        country = self.db["Country"].find_one({"name": current_user["country"]})
        if not country or school in country["schools"]:
            return

        if not country["schools_unverified"]:
            country["schools_unverified"] = [school]
        elif school not in country["schools_unverified"]:
            country["schools_unverified"].append(school)
        country.save()

    def generate_members(self, squad, mem_count):
        if not mem_count or not isinstance(mem_count, (int, long)) or mem_count < 0:
            return

        if mem_count > 1000:
            mem_count = 1000

        usernm_prefix = whitespace.sub("", squad["name"]) if whitespace.search(squad["name"]) else squad["name"]
        usernm_prefix = self.db["IZHero"].normalize_username(usernm_prefix)
        usernm_escape = "^" + re.escape(usernm_prefix) + "[\\d]{"
        namelen = len(usernm_prefix)
        mem_len = 2

        while True:
            expr = usernm_escape + unicode(mem_len) + "}$"
            last_member = self.db["IZHero"].find_one({"username": {"$regex": expr, "$options": "i"}},
                                                     sort=[("username", -1)])

            mem_digit = int(last_member["username"][namelen:]) if last_member and (mem_len == 2 or last_member["username"][namelen:namelen+1] != "0") else pow(10, mem_len-1)

            if not last_member and mem_digit == 10:
                mem_digit = 0

            if (mem_digit + mem_count) < pow(10, mem_len):
                break
            else:
                mem_len += 1
                expr = usernm_escape + unicode(mem_len) + "}$"
                first_member = self.db["IZHero"].find_one({"username": {"$regex": expr, "$options": "i"}},
                                                          sort=[("username", 1)])
                if (first_member and ((mem_digit + mem_count) < int(first_member["username"][namelen:])))\
                        or (not first_member and ((mem_digit + mem_count) < pow(10, mem_len))):
                    break
                elif not first_member:
                    found = True
                    while (mem_digit + mem_count) >= pow(10, mem_len):
                        mem_len += 1
                        expr = usernm_escape + unicode(mem_len) + "}$"
                        first_member = self.db["IZHero"].find_one({"username": {"$regex": expr, "$options": "i"}},
                                                                  sort=[("username", 1)])
                        if first_member and ((mem_digit + mem_count) > int(first_member["username"][namelen:])):
                            found = False
                    if found:
                        break

        izherocls = self.db["IZHero"]
        password = current_app.config.get("IZHERO_SQUAD_DEFAULT_PWD", izherocls.generate_password())
        hashedpwd = izherocls.hash_password(password)
        # accesscodes = []
        # mem_count_needed = mem_count
        # completed = False

        """
        if current_user.get("accesscode") and isinstance(current_user["accesscode"], (list, tuple)):
            codes = current_user["accesscode"]
            for ac in codes:
                mship = self.db["SchoolMembership"].find_one({"code": ac, "userid": current_user.id})
                if mship is not None and mship["membership"]["count"] > mship["membership"]["assigned"]:
                    available = mship["membership"]["count"] - mship["membership"]["assigned"]
                    if available >= mem_count_needed:
                        accesscodes.append({"code": mship["studentcode"],
                                            "sponsor": mship.get("sponsor", ""),
                                            "count": mem_count_needed})
                        filled = mem_count_needed
                        completed = True
                    else:
                        accesscodes.append({"code": mship["studentcode"],
                                            "sponsor": mship.get("sponsor", ""),
                                            "count": available})
                        mem_count_needed -= available
                        filled = available
                    self.db["SchoolMembership"].collection.update({"code": ac, "userid": current_user.id},
                                                                  {"$inc": {"membership.assigned": filled}})

                    if completed:
                        break
        else:
            return
        """

        for i in xrange(mem_count):
            mem_digit += 1
            usernm = usernm_prefix + "0" + unicode(mem_digit) if mem_digit < 10 else usernm_prefix + unicode(mem_digit)
            izhero = izherocls()
            izhero["username"] = usernm
            izhero["givenname"] = ""
            izhero["familyname"] = ""
            izhero["school"] = squad["school"]
            izhero["country"] = current_user.get("country")
            izhero["squad"] = {"code": squad["code"], "name": squad["name"]}
            izhero["genpwd"] = password
            izhero["password"] = hashedpwd
            """
            if accesscodes:
                izhero["accesscode"] = accesscodes[0]["code"]
                izhero["sponsor"] = accesscodes[0]["sponsor"]
                izhero["fullaccess"] = True
                accesscodes[0]["count"] -= 1
                if accesscodes[0]["count"] <= 0:
                    accesscodes = accesscodes[1:]
            else:
                break
            """
            izhero["sponsor"] = current_user.get("sponsor")
            izhero["fullaccess"] = True
            izhero.save()

    def _create_teacher(self, lang, email, familyname, givenname, country, school, hod, squad):
        assigned_to = self.model()
        if assigned_to.update_username(email) is None:
            pwd = self.db["IZHero"].generate_password()
            assigned_to["email"] = email
            assigned_to["familyname"] = familyname
            assigned_to["givenname"] = givenname
            assigned_to["password"] = self.db["IZHero"].hash_password(pwd)
            assigned_to["country"] = country
            assigned_to["school"] = school
            assigned_to["activationcode"] = ""
            assigned_to["status"] = True
            assigned_to["hod"] = hod["_id"]
            assigned_to["assigned_squads"] = [squad]
            if assigned_to.create_alt_izhero(fullaccess=True, sponsor=hod.get("sponsor"), hod=hod["_id"]):
                assigned_to.save()
                tmpl = "/teacher_account.html"
                lang = lang if lang and lang in lang_list else "en"
                tmpl = (lang + tmpl) if lang in lang_list else "en" + tmpl

                title = {
                    "ko": u"[DQ World] %s 님이 당신을 DQ 월드로 초대했습니다!" %
                          ((hod.get("familyname") or "") +
                           (hod.get("givenname") or "")),
                    "en": "[DQ World] %s has invited you to join DQ World!" % hod.get("givenname"),
                    "es": u"[DQ World] %s le ha invitado a unirse a DQ World™" % hod.get("givenname")
                }
                sendmail(email,
                         title[lang],
                         render_template(tmpl,
                                         url_root=os.path.dirname(request.url_root[:-1]) + '/',
                                         username=email,
                                         familyname=familyname,
                                         givenname=givenname,
                                         hod_familyname=hod.get("familyname"),
                                         hod_givenname=hod.get("givenname"),
                                         school=hod.get("school"),
                                         password=pwd))
                return assigned_to
        return None

    @staticmethod
    def get_reqvalues():
        parser = restful.reqparse.RequestParser()
        parser.add_argument("name", type=unicode, store_missing=False)
        parser.add_argument("school", type=unicode, store_missing=False)
        parser.add_argument("grade", type=unicode, store_missing=False)
        parser.add_argument("members_count", type=unicode, store_missing=False)
        parser.add_argument("teacher_email", type=unicode, store_missing=False)
        parser.add_argument("teacher_givenname", type=unicode, store_missing=False)
        parser.add_argument("teacher_familyname", type=unicode, store_missing=False)
        parser.add_argument("lang", type=str, store_missing=False)
        args = parser.parse_args()
        mem_count = args.get("members_count")
        if mem_count and mem_count.isdigit():
            mem_count = int(mem_count)
        return args.get("name"), args.get("school"), args.get("grade"), mem_count, \
            args.get("teacher_email"), (args.get("teacher_givenname") or ""), (args.get("teacher_familyname") or ""), \
            args.get("lang")


@admin_teacher.resource
class TeacherSquadName(restful.Resource):
    method_decorators = [acl.requires_role("Teacher")]

    def get(self):
        parser = restful.reqparse.RequestParser()
        parser.add_argument("squadname", type=unicode, store_missing=False)
        parser.add_argument("name", type=unicode, store_missing=False)
        parser.add_argument("school", type=unicode, store_missing=False)
        args = parser.parse_args()

        squadname = args.get("name") or args.get("squadname")
        if not squadname:
            return jsonify(success=True)

        return jsonify(success=not self.model.has_squadname(squadname, args.get("school")))


@admin_school.resource
class CountrySchools(restful.Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self, country=None):
        parser = restful.reqparse.RequestParser()
        parser.add_argument("country", type=unicode, store_missing=False)
        args = parser.parse_args()
        country = args.get("country", country)
        c = self.model.find_one({"name": country if country else current_user.get("country")})
        schools = sorted(c["schools"]) if c.get("schools") else []
        return jsonify(schools=schools)


@admin_izhero.resource
class SquadIZHeroes(crudmgo.ListAPI):
    limit = 0
    method_decorators = [acl.requires_role(["Teacher", "Administrator"])]

    def get(self, code=None):
        if not code:
            if current_user.has_role("administrator"):
                self.filter_by = {"squad.code": {"$ne": None}}
            elif current_user.get("squads") or current_user.get("assigned_squads"):
                squads = current_user.get("squads", []) + current_user.get("assigned_squads", [])
                self.filter_by = {"squad.code": {"$in": [sq["code"] for sq in squads]}}
            else:
                return jsonify(items=[], pages=0)
        else:
            self.filter_by = {"squad.code": code}
            if not current_user.has_role("administrator") and not current_user.has_squad(code):
                return abort(403)

        d = super(SquadIZHeroes, self)._get()
        for item in d["items"]:
            item["dq_completed"] = 0
            if item.get("dq_progress"):
                item["dq_completed"] = len(item["dq_progress"])
                if "messenger" in item["dq_progress"]:
                    item["dq_completed"] -= 1
                if "izpillars" in item["dq_progress"]:
                    item["dq_completed"] -= 1

            item.pop("dq_progress", None)
            item.pop("progress", None)
            item.pop("dq_coins_stage", None)
            item.pop("data", None)
            item.pop("coins_stage", None)
            item.pop("points_stage", None)
        return jsonify(d)

    def post(self, code=None):
        teach = self.db["Teacher"].find_one({"squads.code": code})
        if teach and (current_user.has_role("administrator") or current_user["_id"] == teach["_id"]):
            squad = None
            for s in teach["squads"]:
                if s["code"] == code:
                    squad = s
                    break

            self.filter_by = {"squad.code": code, "squad.name": squad["name"],
                              "country": teach.get("country"), "school": squad.get("school")}
            # TODO: accept DOB date
            super(SquadIZHeroes, self).post()


@admin_izhero.resource
class SquadIZHero(crudmgo.ItemAPI):
    method_decorators = [acl.requires_role("Teacher")]

    def _getitem(self, itemid):
        izhero = self.model.find_one({"_id": ObjectId(itemid)})
        cuser = current_user._get_current_object()

        if izhero is not None and "squad" in izhero and "code" in izhero["squad"] and \
                "squads" in cuser and cuser["squads"]:
            squadcode = izhero["squad"]["code"]
            if cuser.has_squad(squadcode):
                return izhero
        return None

    def _formdata(self):
        res, data = super(SquadIZHero, self)._formdata()

        # print res

        if res:
            newdata = {}
            if "givenname" in data:
                newdata["givenname"] = data["givenname"]

            if "familyname" in data:
                newdata["familyname"] = data["familyname"]

            if "password" in data:
                newdata["password"] = data["password"]

            data = newdata

        return res, data

    def delete(self, itemid=None):
        abort(404)


@admin_izhero.resource
class SquadIZHeroStatus(crudmgo.ToggleAPI):
    method_decorators = [acl.requires_role("Teacher")]
    toggle = "status"

    def _getitem(self, itemid):
        izhero = self.model.find_one({"_id": ObjectId(itemid)})
        cuser = current_user._get_current_object()

        if izhero is not None and "squad" in izhero and "code" in izhero["squad"] and \
                "squads" in cuser and cuser["squads"]:
            squadcode = izhero["squad"]["code"]
            if cuser.has_squad(squadcode):
                return izhero
        return None


@admin_country.resource
class Countries(restful.Resource):
    db = None
    model = None

    def get(self):
        # TODO: cache this
        countries = self.model.find(None, {"name": 1}).sort("name", 1)
        return jsonify(countries=[c["name"] for c in countries])


@admin_izhero.resource
class StudentResetDQ(restful.Resource):
    method_decorators = [acl.requires_role("administrator")]

    def post(self, itemid):
        if not ObjectId.is_valid(itemid):
            return jsonify(success=False)

        userid = ObjectId(itemid)
        self.model.collection.update({"_id": userid}, {"$set": {
            "dq_progress": {},
            "dq_points": 0,
            "dq_coins": 0,
            "dq_coins_stage": {},
            "dq_level": 1,
            "dq_level_progress": 0,
            "dq_has_leveled": False
        }})
        self.db["Messenger"].collection.remove({"userid": userid})
        self.db["ChatLog"].collection.remove({"userid": userid})
        self.db["DqUserMission"].collection.remove({"userid": userid})
        self.db["SurveyDQAnswer"].collection.remove({"created.by": userid})
        return jsonify(success=True)


apicountry = restful.Api(admin_country)
apicountry.add_resource(CountryList, '/', endpoint="countries")
apicountry.add_resource(CountryItem, '/item/<itemid>', endpoint="country")
apicountry.add_resource(Countries, '/list', endpoint='list')

apischool = restful.Api(admin_school)
apischool.add_resource(SchoolList, '/', endpoint='schools')
apischool.add_resource(SchoolList, '/<country>', endpoint='cschools')
apischool.add_resource(CountrySchools, '/list', endpoint='list')
apischool.add_resource(CountrySchools, '/list/<country>', endpoint='clist')
apischool.add_resource(SchoolUnverifList, '/unverif/<country>', endpoint='unverif_list')
apischool.add_resource(SchoolUnverifItem, '/unverif/<country>/<school>', endpoint='unverif')

apistudent = restful.Api(admin_izhero)
apistudent.add_resource(StudentList, '/', endpoint='students')
apistudent.add_resource(StudentItem, '/item/<itemid>', endpoint='student')
apistudent.add_resource(StudentStatus, '/status/<itemid>', endpoint='status')
apistudent.add_resource(StudentGuardAck, '/guardack/<itemid>', endpoint='guardack')
apistudent.add_resource(StudentExport, '/export', endpoint='export')
apistudent.add_resource(SquadIZHeroes, '/squad', endpoint='squad')
apistudent.add_resource(SquadIZHeroes, '/squad/<code>', endpoint='squadcode')
apistudent.add_resource(SquadIZHero, '/izhero/<itemid>', endpoint='izhero')
apistudent.add_resource(SquadIZHeroStatus, '/izstatus/<itemid>', endpoint='izstatus')
apistudent.add_resource(StudentUpdate, '/update/<itemid>', endpoint='update')
apistudent.add_resource(StudentResetDQ, '/resetdq/<itemid>', endpoint='resetdq')

apiteacher = restful.Api(admin_teacher)
apiteacher.add_resource(TeacherList, '/', endpoint='teachers')
apiteacher.add_resource(TeacherItem, '/item/<itemid>', endpoint='teacher')
apiteacher.add_resource(TeacherStatus, '/status/<itemid>', endpoint='status')
apiteacher.add_resource(TeacherExport, '/export', endpoint='export')
apiteacher.add_resource(TeacherRegistration, '/register', endpoint='register')
apiteacher.add_resource(TeacherActivation, '/activate', endpoint='activate')
apiteacher.add_resource(TeacherActivation, '/activate/<itemid>', endpoint='activateid')
apiteacher.add_resource(TeacherSquad, '/squads', endpoint='squads')
apiteacher.add_resource(TeacherSquad, '/squad/<code>', endpoint='squad')
apiteacher.add_resource(TeacherSquadName, '/squadname', endpoint='squadname')
apiteacher.add_resource(TeacherUpdate, '/update', endpoint='update')
apiteacher.add_resource(TeacherAccessCode, '/accesscode', endpoint='accesscode')
