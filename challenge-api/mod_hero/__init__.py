# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask.ext import restful
from flask import jsonify, request, render_template, redirect
from mod_auth import current_user, acl, model, current_app, current_userid, current_session
from mod_sendmail import sendmail
from rest import crudmgo
from bson.objectid import ObjectId
from werkzeug.datastructures import MultiDict
from werkzeug.contrib.cache import SimpleCache
from model import membership
from dateutil.relativedelta import relativedelta
import datetime
import os
import urllib
import re
import string
import pymongo


izhero_izhero = crudmgo.CrudMgoBlueprint("izhero_izhero", __name__, model="IZHero", template_folder="templates")
username_ic = re.compile(r"^[sgt]?[\.\/\\]?[\d]{7}[\.\/\\]?[a-z]?$", re.I)
username_email_trail = re.compile(r"@[a-z0-9\-]+\.[a-z]+(\.[a-z]+)?", re.I)

lang_list = ("en", "ko", "es")


@izhero_izhero.resource
class IZheroRegister(crudmgo.ListAPI):
    izhero = None

    def get(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("username", type=unicode, store_missing=False)
        pr.add_argument("email", type=unicode, store_missing=False)
        args = pr.parse_args()
        username = args.get("username")
        email = args.get("email")
        success = True

        if username:
            success = not (' ' in username or username_ic.match(username) or (len(username) >= 3 and
                           self.model.find_one({"username": self.model.normalize_username(username)}, {"_id": 1})))
            if not success and current_user._get_current_object() and current_user.get("username") and current_user["username"] == username:
                success = True
        if success and email:
            success = len(email) >= 3 and not self.model.find_one({"parent.email": email, "is_parent": True})\
                and not self.model.find_one({"username": email})

        return jsonify(success=success)

    def post(self):
        if current_app.config.get('DISABLE_REGISTRATION'):
            return jsonify(success=False, errors={"registration": "disabled"})

        pr = restful.reqparse.RequestParser()
        pr.add_argument("membership", type=str, store_missing=False)
        pr.add_argument("lg_access", type=bool, store_missing=False)
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()
        has_membership = False
        mcode = ""

        if args.get("membership"):
            mcode = membership.parse_code(args["membership"])
            if mcode:
                has_membership = self.db["Membership"].find_one({"code": mcode, "userid": None})
            if not has_membership:
                return jsonify(success=False, errors={"membership_code": "incorrect"})

        result = self._post()
        if result["success"]:
            # self.izhero["activationcode"] = ""
            # self.izhero["guardiansack"] = True

            if has_membership and not self.izhero.get("is_parent"):
                has_membership["userid"] = self.izhero["_id"]
                has_membership["username"] = self.izhero["username"]
                has_membership["started"] = crudmgo.localtime()
                if has_membership["duration"] > 0:
                    has_membership["expiry"] = has_membership["started"] + relativedelta(years=has_membership["duration"])
                has_membership.save()
                self.izhero["accesscode"] = mcode
                self.izhero["fullaccess"] = True
                self.izhero["sponsor"] = has_membership.get("sponsor", "")
                self.izhero.save()
            elif args.get("lg_access") and not self.izhero.get("is_parent"):
                self.izhero["fullaccess"] = True
                self.izhero["sponsor"] = "LG U+"
                self.izhero.save()
            else:  # by default all singtel sponsor, NOTE: if removing remember to save activation
                self.izhero["fullaccess"] = True
                self.izhero["sponsor"] = ""  # "LG U+" if args.get("lang", "en") == "ko" else "Singtel"
                self.izhero.save()

            # elif not self.izhero.get("is_parent"):

            if not self.izhero.get("is_parent"):
                tmpl = "/activation.html"
                lang = args.get("lang", "en")
                lang = lang if lang in lang_list else "en"
                tmpl = (lang + tmpl) if lang in lang_list else "en" + tmpl

                title = {
                    "ko": u"[DQ 월드] 귀하의 자녀가 DQ World™에 회원 가입 했습니다",
                    "en": u"[DQ World] Your child has signed up for DQ World™",
                    "es": u"[DQ World] Su hijo(a) se acaba de inscribir en DQ World™"
                }

                sendmail(self.izhero["parent"]["email"],
                         title[lang],
                         render_template(tmpl,
                                         url_root=os.path.dirname(request.url_root[:-1]) + '/',
                                         **self.izhero))

            current_app.auth.login_user(self.izhero)
        return jsonify(result)

    def _formitem(self):
        item, err = super(IZheroRegister, self)._formitem()
        if item and not err:
            self.db["Country"].insert_school(item["country"], item["school"])
            item["activationcode"] = model.generate_code()
            item["status"] = True
            item["guardiansack"] = False
            item["points"] = 0
            item["coins"] = 0
            item["progress"] = []
            item["data"] = {}

            err = {}
            parent = item.get("parent")

            # if not item.get("is_parent"):
            #     if not parent or not parent.get("familyname"):
            #         err["parent_familyname"] = "Parent's family name is required."
            #     if not parent or not parent.get("givenname"):
            #         err["parent_givenname"] = "Parent's given name is required."
            if item.get("is_parent"):
                item["guardiansack"] = True

            if not parent or not parent.get("email"):
                err["parent_email"] = "Parent's email is required."
            # if not parent or not parent.get("contact"):
            #     err["parent_contact"] = "Parent's contact number is required."

            if err:
                item = None
            self.izhero = item

        return item, err


@izhero_izhero.resource
class IZHeroMembership(restful.Resource):
    db = None
    model = None

    def get(self, itemid=None):
        itemid = membership.parse_code(itemid or request.args.get("membership"))
        mem = None
        if itemid:
            mem = self.db["Membership"].find_one({"code": itemid, "userid": None})
        return jsonify(success=bool(mem))


@izhero_izhero.resource
class IZHeroActivation(restful.Resource):
    db = None
    model = None

    def get(self, itemid=None):
        item = self.model.find_one({"_id": ObjectId(itemid)}) if itemid else None
        res = self.activate(item)
        if not res["success"]:
            pr = restful.reqparse.RequestParser()
            pr.add_argument("username", type=unicode, store_missing=False)
            pr.add_argument("code", type=str, store_missing=False)
            pr.add_argument("lang", type=str, store_missing=False)
            args = pr.parse_args()
            qstr = urllib.urlencode({"username": args.get("username", current_user["username"] if current_userid else ""),
                                     "code": args.get("code", "")})
            link = '/lang:' + args.get('lang', 'en') + ('/#!/landing/activate?%s' % qstr if not current_userid
                                                        else '/#!/iZHQ?activated=false&%s' % qstr)
        else:
            pr = restful.reqparse.RequestParser()
            pr.add_argument("lang", type=str, store_missing=False)
            args = pr.parse_args()
            link = ('/lang:%s/zone/menu?activated=1' if current_userid else '/lang:%s/#!/landing/login?activated=1') % args.get('lang', 'en')

        return redirect(link, 303)

    def post(self, itemid=None):
        item = self.model.find_one({"_id": ObjectId(itemid)}) if itemid else None
        return jsonify(self.activate(item))

    def put(self, itemid=None):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("username", type=unicode, store_missing=False)
        pr.add_argument("renew_tnc", type=bool, store_missing=False)
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()

        izhero = None

        if args.get("username"):
            izhero = self.model.find_one({"username": self.model.normalize_username(args.get("username"))})

        if not izhero and current_userid:
            izhero = current_user
        elif not izhero:
            return jsonify(success=False)

        if izhero.get("teacher"):
            izhero = self.db["Teacher"].find_one({"username": self.model.normalize_username(args.get("username"))})
            email_addr = izhero["email"]
        else:
            email_addr = izhero.get("parent", {}).get("email")
            if email_addr and args.get("renew_tnc") and izhero.get("data", {}).get("renew_tnc")\
                    and not izhero.get("activationreset"):
                izhero["guardiansack"] = bool(isinstance(izhero.get("squad"), dict) and izhero["squad"].get("code"))
                izhero["activationreset"] = crudmgo.localtime()
                izhero["activationcode"] = izhero["activationcode"] or model.generate_code()
                izhero.save()

        if izhero["activationcode"] and email_addr:
            tmpl = "/activation.html"
            lang = args.get("lang", "en")
            lang = lang if lang in lang_list else "en"
            tmpl = (lang + tmpl) if lang in lang_list else "en" + tmpl

            title = {
                "ko": u"[DQ 월드] 귀하의 자녀가 DQ World™에 회원 가입 했습니다",
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

    def activate(self, item):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("username", type=unicode, store_missing=False)
        pr.add_argument("id", type=str, store_missing=False)
        pr.add_argument("code", type=str, store_missing=False)
        pr.add_argument("parent_contact", type=unicode, store_missing=False)
        pr.add_argument("parent_username", type=unicode, store_missing=False)
        pr.add_argument("parent_password", type=unicode, store_missing=False)
        pr.add_argument("parent_givenname", type=unicode, store_missing=False)
        pr.add_argument("parent_familyname", type=unicode, store_missing=False)
        args = pr.parse_args()

        if item is None and (args.get("username") or args.get("id")):
            username = args.get("username")
            uid = args.get("id")
            item = self.model.find_one({"username": self.model.normalize_username(username)} if username else {"_id": ObjectId(uid)})
        elif item is None and current_userid._get_current_object():
            item = self.model.find_one({"_id": ObjectId(current_userid._get_current_object())})

        if item is not None:
            code = args.get("code")

            if item["guardiansack"]:
                return dict(success=True, user={"username": item["username"]})
            elif item.get("teacher"):
                teacher = self.db["Teacher"].find_one({"username": item["username"]})

                if teacher and teacher["status"]:
                    item["activationcode"] = ""
                    item["guardiansack"] = True
                    item.save()
                    return dict(success=True, user={"username": item["username"]})

                if teacher and code and code.strip() == teacher["activationcode"]:
                    teacher["activationcode"] = ""
                    teacher["status"] = True
                    teacher.save()
                    item["activationcode"] = ""
                    item["guardiansack"] = True
                    item.save()
                    current_app.auth.login_user(item)
                    return dict(success=True, user=crudmgo.model_to_json(item))

            elif code and code.strip() == item["activationcode"]:
                parent = item.get("teacher") or self.model.create_parent(args.get("parent_username"),
                                                                         args.get("parent_password"),
                                                                         item["parent"]["email"],
                                                                         args.get("parent_givenname"),
                                                                         args.get("parent_familyname"),
                                                                         args.get("parent_contact"),
                                                                         item["country"])

                item["activationcode"] = ""
                item["guardiansack"] = True
                item.save()
                current_app.auth.login_user(item)
                return dict(success=True, user=crudmgo.model_to_json(item))
            return dict(success=False, error="Incorrect activation code.", errcode=200)
        return dict(success=False, error="Account does not exists", errcode=100)


@izhero_izhero.resource
class IZHeroSquad(restful.Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def get(self, code=None):
        code = self.get_code(code)
        if not code and current_user.get("squad") and "code" in current_user["squad"]:
            code = current_user["squad"]["code"]

        if code:
            teacher = self.db["Teacher"].find_teacher_of_squad(code, True)

            if teacher:
                agg = self.db["IZHero"].collection.aggregate([
                    {"$match": {"squad.code": code}},
                    {"$group": {"_id": None,
                                "points": {"$sum": "$points"},
                                "coins": {"$sum": "$coins"},
                                "donated": {"$sum": "$donated"}}}
                ])
                squad = crudmgo.to_flat_value(teacher["squads"][0])
                squad["teacher"] = {"username": teacher["username"],
                                    "familyname": teacher["familyname"],
                                    "givenname": teacher["givenname"],
                                    "lastlogin": teacher["lastlogin"]}
                squad.update(agg["result"][0])
                mem = self.db["IZHero"].collection.find({"squad.code": code, "$or": [{"genpwd": "1"}, {"genpwd": ""}, {"genpwd": None}]},
                                                        {"username": 1, "familyname": 1, "givenname": 1, "points": 1,
                                                         "coins": 1, "donated": 1, "lastlogin": 1})
                squad["members"] = [crudmgo.to_flat_value(m) for m in mem]
                return jsonify(squad=squad)
        return jsonify({})

    def post(self, code=None):
        izhero = current_user._get_current_object()
        code = self.get_code(code)

        if izhero.get("squad") and izhero["squad"].get("code"):
            return jsonify(success=False, error="Already in a squad.")

        if code:
            teacher = self.db["Teacher"].collection.find_one({"squads.code": code}, {"squads.$": 1, "country": 1})
            if not teacher:
                return jsonify(success=False, error="Squad not found.")

            squad = teacher["squads"][0]
            izhero["squad"] = {"code": squad["code"], "name": squad["name"]}
            izhero["school"] = squad["school"]
            izhero["country"] = teacher["country"]
            izhero.save()
        return jsonify(success=True, squad=izhero["squad"])

    def put(self, code=None):
        izhero = current_user._get_current_object()
        code = self.get_code(code)
        if "squad" in izhero and "code" in izhero["squad"] and izhero["squad"]["code"]:
            newsquad = izhero.get("newsquad")
            timenow = crudmgo.localtime()
            if newsquad and isinstance(newsquad, dict) and newsquad.get("code") and newsquad.get("time"):
                if newsquad["time"] > timenow:
                    return jsonify(success=False, error="Account already in the process of switching squad.")

                teacher = self.db["Teacher"].collection.find_one({"squads.code": newsquad["code"]},
                                                                 {"squads.$": 1, "country": 1})
                if teacher:
                    izhero["squad"] = {"code": newsquad["code"],
                                       "name": teacher["squads"][0].get("name")}

            if code != izhero["squad"]["code"]:
                izhero["newsquad"] = {"code": code, "time": timenow + datetime.timedelta(days=7)}

            return jsonify(success=True)
        return jsonify(success=False, error="Current squad not found.")

    @staticmethod
    def get_code(code):
        if not code:
            pr = restful.reqparse.RequestParser()
            pr.add_argument("code", type=str, store_missing=False)
            args = pr.parse_args()
            code = args.get("code")
        return code


@izhero_izhero.resource
class IZHeroUpdate(crudmgo.ItemAPI):
    method_decorators = [acl.requires_login]
    activation_mail = False
    old_password = None
    username = None

    def get(self, itemid=None):
        return super(IZHeroUpdate, self).get(itemid or str(current_user.get("_id")))

    def put(self, itemid=None):
        parent = current_user.get("parent")
        self.username = current_user["username"]
        if not parent or not parent.get("email"):
            self.activation_mail = True
        self.old_password = current_user["password"]

        result = super(IZHeroUpdate, self)._put(str(current_user.get("_id")))

        if result["success"] and current_user.get("teacher"):
            pr = restful.reqparse.RequestParser()
            pr.add_argument("contact", type=unicode, store_missing=False)
            pr.add_argument("email", type=unicode, store_missing=False)
            args = pr.parse_args()

            updating = {"password": current_user["password"],
                        "country": current_user["country"],
                        "school": current_user["school"],
                        "familyname": current_user["familyname"],
                        "givenname": current_user["givenname"]}

            if args.get("contact"):
                updating["contact"] = args["contact"]
            # TODO: check for email uniqueness
            #if args.get("email"):
            #    updating["email"] = args["email"]

            self.db["Teacher"].collection.update({"username": current_user["username"]},
                                                 {"$set": updating})

        if result["success"] and self.activation_mail and current_user.get("parent") and "email" in current_user["parent"]:
            pr = restful.reqparse.RequestParser()
            pr.add_argument("lang", type=str, store_missing=False)
            args = pr.parse_args()

            tmpl = "/activation.html"
            lang = args.get("lang", "en")
            lang = lang if lang in lang_list else "en"
            tmpl = (lang + tmpl) if lang in lang_list else "en" + tmpl

            title = {
                "ko": u"[DQ 월드] 귀하의 자녀가 DQ World™에 회원 가입 했습니다",
                "en": u"[DQ World] Your child has signed up for DQ World™",
                "es": u"[DQ World] Su hijo(a) se acaba de inscribir en DQ World™"
            }
            sendmail(current_user["parent"]["email"],
                     title[lang],
                     render_template(tmpl,
                                     url_root=os.path.dirname(request.url_root[:-1]) + '/',
                                     **current_user._get_current_object()))
        if result["success"] and self.username != current_user["username"]:
            self.db["File"].collection.update({'created.by': current_user["_id"]},
                                              {'$set': {'created.username': current_user['username']}})

        return jsonify(result)

    def _getitem(self, _):
        return current_user._get_current_object()

    def _updateitem(self, itemid, data):
        item, err = super(IZHeroUpdate, self)._updateitem(itemid, data)
        if not err and item is not None:
            err = {}

            # if not item.get("teacher") and not item.get("is_parent"):
            #     parent = item.get("parent")
            #     if not parent or not parent.get("familyname"):
            #         err["parent_familyname"] = "Parent's family name is required."
            #     if not parent or not parent.get("givenname"):
            #         err["parent_givenname"] = "Parent's given name is required."
            #     if not parent or not parent.get("email"):
            #         err["parent_email"] = "Parent's email is required."
            #     if not parent or not parent.get("contact"):
            #         err["parent_contact"] = "Parent's contact number is required."

            if err:
                item.reload()
                self.activation_mail = False
                return None, err

            if self.username != item["username"]:
                if not item["genpwd"]:
                    item["username"] = self.username

            if not item["genpwd"] and item["password"] != self.old_password:
                pr = restful.reqparse.RequestParser()
                pr.add_argument("old_password", type=unicode, store_missing=False)
                args = pr.parse_args()
                newpass = item["password"]
                item["password"] = self.old_password
                if args.get("old_password") and item.authenticate(args["old_password"]):
                    item["password"] = newpass

            if item["genpwd"]:
                new_username = item["username"] != self.username
                parent_info = isinstance(item.get("parent"), dict) and item["parent"].get("email")
                new_password = item["password"] != self.old_password

                if new_username or parent_info or new_password:
                    item["genpwd"] = ""

            # item["genpwd"] = ""

            if self.activation_mail and not item.get("activationcode"):
                item["activationcode"] = model.generate_code()
        else:
            self.activation_mail = False

        return item, err


@izhero_izhero.resource
class IZHeroResetPwd(restful.Resource):
    method_decorators = [acl.requires_anonymous]
    db = None
    model = None

    def get(self):
        res = {"success": False}

        pr = restful.reqparse.RequestParser()
        pr.add_argument("username", type=unicode, store_missing=False)
        pr.add_argument("code", type=unicode, store_missing=False)
        args = pr.parse_args()

        username, code = args.get("username"), args.get("code")

        if username and code:
            username = self.model.normalize_username(username)
            izhero = self.model.find_one({"username": username, "pwdreset.code": code})
            res["success"] = izhero and izhero["pwdreset"]["expiry"] and izhero["pwdreset"]["expiry"] > crudmgo.utctime()

        return jsonify(res)

    def post(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("username", type=unicode, store_missing=False)
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()
        username = args.get("username")

        if username:
            username = self.model.normalize_username(username)
            izhero = self.model.find_one({"username": username})
            if izhero:
                if (not izhero.get("parent") or not izhero["parent"].get("email")) and not izhero.get("teacher"):
                    return jsonify(success=False, error="Account does not have an email address.")

                izhero["pwdreset"] = {"code": model.generate_code(10),
                                      "expiry": crudmgo.localtime() + datetime.timedelta(days=7)}
                izhero.save()

                if izhero.get("teacher"):
                    teach = self.db["Teacher"].find_one({"username": izhero["username"]})
                    email_addr = teach["email"]
                else:
                    email_addr = izhero["parent"]["email"]

                tmpl = "/resetpwd.html"
                lang = args.get("lang", "en")
                lang = lang if lang in lang_list else "en"
                tmpl = (lang + tmpl) if lang in lang_list else "en" + tmpl

                title = {
                    "ko": "[DQ 월드] 비밀번호 찾기",
                    "en": "[DQ World] Forgot Password!",
                    "es": "[DQ World] Olvidé Contraseña"
                }

                sendmail(email_addr,
                         title[lang],
                         render_template(tmpl,
                                         url_root=os.path.dirname(request.url_root[:-1])+'/',
                                         **izhero))
                return jsonify(success=True)
        return jsonify(success=False, error="Account not found.")

    def put(self):
        res = {"success": False}

        pr = restful.reqparse.RequestParser()
        pr.add_argument("username", type=unicode, store_missing=False)
        pr.add_argument("code", type=unicode, store_missing=False)
        pr.add_argument("password", type=unicode, store_missing=False)
        args = pr.parse_args()
        username, code, password = args.get("username"), args.get("code"), args.get("password")

        if username and code and password:
            username = self.model.normalize_username(username)
            izhero = self.model.find_one({"username": username, "pwdreset.code": code})
            if izhero:
                if izhero["pwdreset"]["expiry"] and izhero["pwdreset"]["expiry"] > crudmgo.localtime():
                    izhero["pwdreset"] = None
                    izhero.update_password(password)
                    izhero.save()
                    if izhero.get("teacher"):
                        self.db["Teacher"].collection.update({"username": izhero["username"]},
                                                             {"$set": {"password": izhero["password"]}})
                    current_app.auth.login_user(izhero)
                    res["success"] = True
                else:
                    izhero["pwdreset"] = None
                    izhero.save()
                    res["error"] = "Code has already expired."
            else:
                res["error"] = "Incorrect username and/or code."
        else:
            res["error"] = "Missing username, code, and/or password."

        return jsonify(res)


@izhero_izhero.resource
class IZHeroSendUserName(restful.Resource):
    method_decorators = [acl.requires_anonymous]
    db = None
    model = None

    def post(self):
        res = {"success": False}

        pr = restful.reqparse.RequestParser()
        pr.add_argument("email", type=unicode, store_missing=False)
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()

        email = args.get("email")

        if email:
            teach = self.db["Teacher"].find_one({"email": email})
            izheroes = list(self.model.find({"parent.email": email}))

            if len(izheroes) > 0 or teach:
                if teach:
                    izheroes.append(teach)

                tmpl = "/senduser.html"
                lang = args.get("lang", "en")
                lang = lang if lang in lang_list else "en"
                tmpl = (lang + tmpl) if lang in lang_list else "en" + tmpl

                title = {
                    "ko": u"[DQ 월드] 사용자아이디 찾기",
                    "en": "[DQ World] Forgot Username!",
                    "es": "[DQ World] Olvidé Nombre de Usuario"
                }

                sendmail(email,
                         title[lang],
                         render_template(tmpl,
                                         url_root=os.path.dirname(request.url_root[:-1])+'/',
                                         accounts=izheroes))
                res["success"] = True

        return jsonify(res)


@izhero_izhero.resource
class IZHeroEmailMediaRules(restful.Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def post(self):
        res = {"success": False}

        pr = restful.reqparse.RequestParser()
        pr.add_argument("message", type=unicode, store_missing=False)
        pr.add_argument("cam", type=unicode, store_missing=False)
        pr.add_argument("profile", type=unicode, store_missing=False)
        pr.add_argument("when", type=unicode, store_missing=False)
        pr.add_argument("play", type=unicode, store_missing=False)
        pr.add_argument("lang", type=str, store_missing=False)
        pr.add_argument("cam_noone", type=str, store_missing=False)
        pr.add_argument("profile_noone", type=str, store_missing=False)
        pr.add_argument("message_ans", type=int, store_missing=False)
        pr.add_argument("cam_ans", type=int, store_missing=False)
        pr.add_argument("profile_ans", type=int, store_missing=False)
        pr.add_argument("doonline_noone", type=str, store_missing=False)
        pr.add_argument("addfriend_noone", type=str, store_missing=False)
        pr.add_argument("dqmission", type=int, store_missing=False)
        args = pr.parse_args()

        email = current_user.get('parent') and current_user['parent'].get('email')

        if email:
            tmpl = "/" + ("dq_" if args.get("dqmission", 0) == 1 else "") + "mediarules.html"
            lang = args.get("lang", "en")
            lang = lang if lang in lang_list else "en"
            tmpl = (lang + tmpl) if lang in lang_list else "en" + tmpl

            title = {
                "ko": u"[DQ World] 당신이 자녀와 함께 DQWorld.net에서 작성한 디지털 미디어 서약서입니다!",
                "en": u"[DQ World] You’ve set the media rules with your kid on DQWorld.net!",
                "es": u"[DQ World] ¡Ha establecido las reglas para el uso de los medios digitales con su hijo(a) en DQWorld.net!"
            }

            sendmail(email,
                     title[lang],
                     render_template(tmpl,
                                     url_root=os.path.dirname(request.url_root[:-1]) + '/',
                                     name=current_user.get_name(),
                                     message=args.get("message"),
                                     cam=args.get("cam"),
                                     profile=args.get("profile"),
                                     when=args.get("when"),
                                     play=args.get("play"),
                                     cam_ans=args.get("cam_ans", 0),
                                     profile_ans=args.get("profile_ans", 0),
                                     message_ans=args.get("message_ans", 0),
                                     cam_noone="noone" if args.get("cam_noone", "false").lower() == "true" else "normal",
                                     profile_noone="noone" if args.get("profile_noone", "false").lower() == "true" else "normal",
                                     doonline_noone="noone" if args.get("doonline_noone", "false").lower() == "true" else "normal",
                                     addfriend_noone="noone" if args.get("addfriend_noone", "false").lower() == "true" else "normal"))
            res["success"] = True

        return jsonify(res)


@izhero_izhero.resource
class IZHeroEmailBalanceScreen(restful.Resource):
    method_decorators = [acl.requires_login]
    db = None
    model = None

    def post(self):
        res = {"success": False}

        pr = restful.reqparse.RequestParser()
        pr.add_argument("days", type=unicode, store_missing=False)
        pr.add_argument("time", type=unicode, store_missing=False)
        pr.add_argument("when", type=unicode, store_missing=False)
        pr.add_argument("when_noone", type=str, store_missing=False)
        pr.add_argument("lang", type=str, store_missing=False)
        pr.add_argument("dqmission", type=int, store_missing=False)
        args = pr.parse_args()

        email = current_user.get('parent') and current_user['parent'].get('email')

        if email:
            tmpl = "/dq_balancescreen.html"
            lang = args.get("lang", "en")
            lang = lang if lang in lang_list else "en"
            tmpl = lang + tmpl

            title = {
                "ko": u"[DQ World] %s 님이 DQWorld.net에서 스크린 타임 서약을 했습니다!",
                "en": u"[DQ World] %s has set a Screen Time Pledge on DQWorld.net!",
                "es": u"[DQ World] ¡%s ha establecido un Pacto de Tiempo en la Pantalla en DQWorld.net!"
            }

            sendmail(email,
                     title[lang] % current_user.get_name(),
                     render_template(tmpl,
                                     url_root=os.path.dirname(request.url_root[:-1]) + '/',
                                     name=current_user.get_name(),
                                     days=args.get("days"),
                                     time=args.get("time"),
                                     when=args.get("when"),
                                     when_noone="noone" if args.get("when_noone", "false").lower() == "true" else "normal"))
            res["success"] = True

        return jsonify(res)


@izhero_izhero.resource
class Countries(restful.Resource):
    db = None
    model = None
    cache = SimpleCache()

    def get(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()
        lang = args.get("lang")

        cc = self.cache.get("countries.l.%s" % lang)

        if not cc:
            fields = {"name": 1} if not lang else {"name": 1, "lang": 1}
            countries = self.db["Country"].find(None, fields).sort("name", pymongo.ASCENDING)
            if lang:
                cc = [{"id": c["name"], "name": (c.get("lang") or {}).get(lang, c["name"])} for c in countries]
            else:
                cc = [c["name"] for c in countries]
            self.cache.set("countries.l.%s" % lang, cc, timeout=3600)

        return jsonify(countries=cc)


@izhero_izhero.resource
class Schools(restful.Resource):
    db = None
    model = None
    cache = SimpleCache()

    def get(self, country=None):
        if not country:
            pr = restful.reqparse.RequestParser()
            pr.add_argument("country", type=unicode, store_missing=False)
            args = pr.parse_args()
            country = args.get("country")

        sch = self.cache.get("schools.c.%s" % country)

        if not sch:
            c = self.db["Country"].find_one({"name": country}, {"schools": 1})
            sch = sorted(c["schools"]) if c["schools"] else []
            self.cache.set("schools.c.%s" % country, sch, timeout=(3600 if len(sch) > 0 else 300))

        return jsonify(schools=sch)


@izhero_izhero.resource
class IZHeroName(restful.Resource):
    method_decorators = [acl.requires_login]

    def post(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("givenname", type=unicode, store_missing=False)
        pr.add_argument("familyname", type=unicode, store_missing=False)
        args = pr.parse_args()

        updated = False
        if not current_user["givenname"]:
            current_user["givenname"] = args.get("givenname", "")
            updated = True
        if not current_user["familyname"]:
            current_user["familyname"] = args.get("familyname", "")
            updated = True

        if updated:
            current_user.save()

        return jsonify(success=True)


@izhero_izhero.resource
class IZHeroData(restful.Resource):
    method_decorators = [acl.requires_login]

    def get(self):
        return jsonify(data=current_user.get("data") or {})

    def post(self):
        izhero = current_user._get_current_object()

        data = MultiDict(request.json) if request.json is not None else request.form
        data = data.to_dict() if data else {}
        newdata, namespace = self._searchdata(izhero, data, clear=True)

        if not namespace:
            d = {}
            for k, v in data.iteritems():
                key = "data.%s" % k
                d[key] = v
            izhero.collection.update({"_id": izhero["_id"]}, {"$set": d})
        else:
            key = "data.%s" % namespace
            izhero.collection.update({"_id": izhero["_id"]},
                                     {"$set": {key: data}})
        izhero.reload()
        # newdata.update(data)
        # izhero.save()
        return jsonify(success=True, data=izhero["data"])

    def put(self):
        izhero = current_user._get_current_object()

        data = MultiDict(request.json) if request.json is not None else request.form
        if data:
            data = data.to_dict()
            newdata, namespace = self._searchdata(izhero, data)
            d = {}
            for k, v in data.iteritems():
                key = ("data.%s.%s" % (namespace, k)) if namespace else ("data.%s" % k)
                d[key] = v
            izhero.collection.update({"_id": izhero["_id"]}, {"$set": d})
            izhero.reload()
            # newdata.update(data)
            # izhero.save()
        return jsonify(success=True, data=izhero.get("data", {}))

    def delete(self):
        izhero = current_user._get_current_object()

        data = request.args

        if data:
            data = data.to_dict()
            key = None
            if "__namespace__" in data and len(data) == 1:
                if "." in data["__namespace__"]:
                    data["__namespace__"], key = data["__namespace__"].rsplit(".", 1)
                else:
                    key = data.pop("__namespace__")

            newdata, _ = self._searchdata(izhero, data)

            if len(data) == 0:
                if key:
                    newdata.pop(key, None)
                else:
                    newdata.clear()
            else:
                for k in data.iterkeys():
                    newdata.pop(k, None)

            izhero.save()
        return jsonify(success=True, data=izhero["data"])

    @staticmethod
    def _searchdata(izhero, data, clear=False):
        if not izhero.get("data"):
            izhero["data"] = {}
        newdata = izhero["data"]

        namespace = data.pop("__namespace__", None)
        if namespace:
            if "." in namespace:
                splitted = namespace.split(".")
                for s in splitted:
                    if s not in newdata:
                        newdata[s] = {}
                    newdata = newdata[s]
            else:
                if namespace not in newdata:
                    newdata[namespace] = {}
                newdata = newdata[namespace]

            if clear:
                newdata.clear()

        return newdata, namespace


@izhero_izhero.resource
class IZHeroChild(crudmgo.ListAPI):
    limit = 0
    method_decorators = [acl.requires_role("parent")]

    def get(self):
        if not current_user.get("guardiansack"):
            return jsonify(items=[], pages=0)
        self.filter_by = {"parent.email": current_user["parent"]["email"]}
        children = super(IZHeroChild, self)._get()
        for c in children["items"]:
            if c.get("is_parent"):
                children["items"].remove(c)
                break
        return jsonify(children)

    def post(self):
        if not current_user.get("guardiansack"):
            return jsonify(success=False)
        return super(IZHeroChild, self).post()

    def _formitem(self):
        item, err = super(IZHeroChild, self)._formitem()
        if item and not err:
            self.db["Country"].insert_school(current_user["country"], item["school"])
            item["status"] = True
            item["guardiansack"] = True
            item["points"] = 0
            item["coins"] = 0
            item["progress"] = []
            item["data"] = {}
            item["country"] = current_user["country"]
            item["parent"] = {
                "familyname": current_user["familyname"],
                "givenname": current_user["givenname"],
                "email": current_user["parent"]["email"],
                "contact": current_user["parent"]["contact"]
            }
        return item, err


@izhero_izhero.resource
class IZHeroParentToChild(restful.Resource):
    method_decorators = [acl.requires_role("parent")]

    def post(self, childid):
        childid = ObjectId(childid)
        child = self.model.find_one({"_id": childid, "parent.email": current_user["parent"]["email"]})
        if child:
            parent_id = str(current_user["_id"])
            current_app.auth.login_user(child)
            if not current_session.get("data"):
                current_session["data"] = {}
            current_session["data"]["parent_account"] = parent_id
            if not current_user.get("data"):
                current_user["data"] = {}
            current_user["data"]["parent_account"] = True
            current_user.save()
            return jsonify(success=True)
        return jsonify(success=False)


@izhero_izhero.resource
class IZHeroChildToParent(restful.Resource):
    method_decorators = [acl.requires_login]

    def post(self):
        child = current_user._get_current_object()
        if child.get("data") and child["data"].pop("parent_account", None):
            child.save()

        if child and (current_session.get("data") or {}).get("parent_account"):
            parent = self.model.find_one({"_id": ObjectId(current_session["data"]["parent_account"])})

            if parent and parent["parent"].get("email") == child["parent"].get("email"):
                current_app.auth.login_user(parent)
                return jsonify(success=True)
        return jsonify(success=False)


@izhero_izhero.resource
class IZHeroRanking(restful.Resource):
    db = None
    model = None
    cache = SimpleCache()

    def get(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()
        lang = args.get("lang", "en")

        ranks = self.cache.get("izhero.ranking." + lang)

        if ranks is None:
            d = {}

            if lang == "ko":
                d["country"] = "Korea, Republic Of"
            elif lang == "en":
                d["country"] = {"$ne": "Korea, Republic Of"}

            agg = self.model.collection.aggregate
            topizp = [{"_id": str(i["_id"]),
                       "points": i["points"],
                       "username": self.stripemail(i["username"])} for i in self.model.find(d).sort("points", -1).limit(10)]
            topsizp = [{"school": i["_id"],
                        "points": i["points"]} for i in agg([{"$group": {"_id": "$school",
                                                                         "points": {"$sum": "$points"}}},
                                                            {"$sort": {"points": -1}},
                                                            {"$limit": 10}])["result"]]
            topsdonate = [{"school": i["_id"],
                           "donated": i["donated"]} for i in agg([{"$group": {"_id": "$school",
                                                                                     "donated": {"$sum": "$donated"}}},
                                                                  {"$sort": {"donated": -1}},
                                                                  {"$limit": 10}])["result"]]

            ranks = jsonify(top_points=topizp, top_school_points=topsizp, top_school_donated=topsdonate)
            self.cache.set("izhero.ranking." + lang, ranks, timeout=3600)
        return ranks

    @staticmethod
    def stripemail(username):
        return username_email_trail.sub("", username)


@izhero_izhero.resource
class IZHeroDQRanking(restful.Resource):
    db = None
    model = None
    cache = SimpleCache()

    def get(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("lang", type=str, store_missing=False)
        args = pr.parse_args()
        lang = args.get("lang", "en")

        ranks = self.cache.get("dqworld.ranking.l." + lang)

        if ranks is None:
            d = {
                "teacher": False
            }

            if lang == "ko":
                d["country"] = "Korea, Republic Of"
            elif lang == "en":
                d["country"] = {"$ne": "Korea, Republic Of"}

            agg = self.model.collection.aggregate
            topizp = [{"_id": str(i["_id"]),
                       "dq_points": i.get("dq_points", 0),
                       "username": self.stripemail(i["username"])}
                      for i in self.model.find(d).sort("dq_points", -1).limit(10)]
            topsizp = [{"school": i["_id"],
                        "username": i["_id"],
                        "dq_points": i["dq_points"]}
                       for i in agg([{"$group": {"_id": "$school",
                                                 "dq_points": {"$sum": "$dq_points"}}},
                                     {"$sort": {"dq_points": -1}},
                                     {"$limit": 12}])["result"]
                       if bool(i["_id"])][:10]

            ranks = dict(top_points=topizp, top_school_points=topsizp)
            self.cache.set("dqworld.ranking.l." + lang, ranks, timeout=1800)

        if not current_user.is_anonymous and \
                (current_user.get("school") or isinstance(current_user.get("squad"), dict)):

            squadcode = ""
            if current_user["squad"].get("code"):
                squadcode = current_user["squad"]["code"]
            school = current_user.get("school") or ""
            sranks = self.cache.get("dqworld.ranking.s." + school + ";" + squadcode)

            if sranks is None:
                sranks = {}
                if school:
                    sranks["top_school_users"] = [{"_id": str(i["_id"]),
                                                   "dq_points": i.get("dq_points", 0),
                                                   "username": self.stripemail(i["username"])}
                                                  for i in self.model.find({"school": school, "teacher": False}).sort("dq_points", -1)
                                                  .limit(10)]
                if squadcode:
                    sranks["top_squad_users"] = [{"_id": str(i["_id"]),
                                                  "dq_points": i.get("dq_points", 0),
                                                  "username": self.stripemail(i["username"])}
                                                 for i in self.model.find({"squad.code": squadcode, "teacher": False}).sort("dq_points", -1)
                                                 .limit(10)]

                self.cache.set("dqworld.ranking.s." + school + ";" + squadcode, sranks, timeout=1800)
            ranks.update(sranks)
        return jsonify(ranks)

    @staticmethod
    def stripemail(username):
        return username_email_trail.sub("", username)


@izhero_izhero.resource
class IZHeroFeedback(restful.Resource):
    method_decorators = [acl.requires_login]

    def post(self):
        pr = restful.reqparse.RequestParser()
        pr.add_argument("body", type=unicode, store_missing=False)
        body = pr.parse_args().get("body", "").strip()

        if body:
            feedback = self.db["Message"]()
            feedback["title"] = "iZ HERO Feedback"
            feedback.update_body(body)
            feedback.save()

            return jsonify(success=True)
        return jsonify(success=False)


@izhero_izhero.resource
class DqHasLeveled(restful.Resource):
    method_decorators = [acl.requires_login]

    def get(self):
        return jsonify(dq_has_leveled=current_user.get("dq_has_leveled", False))

    def delete(self):
        current_user["dq_has_leveled"] = False
        current_user.collection.update({"_id": current_user["_id"]}, {"$set": {"dq_has_leveled": False}})
        return jsonify(success=True)


@izhero_izhero.resource
class IZHeroSupport(restful.Resource):
    method_decorators = [acl.requires_login]

    @staticmethod
    def post():
        email = current_user.get('parent') and current_user['parent'].get('email')

        if email:
            pr = restful.reqparse.RequestParser()
            pr.add_argument("lang", type=str, store_missing=False)
            args = pr.parse_args()
            name = current_user.get('givenname') or current_user.get("username")
            lang = args.get("lang", "en")

            sendmail(email,
                     "%s feels like they’ve been cyberbullied and needs your support." % name,
                     render_template("%s/givesupport.html" % (lang if lang in lang_list else "en"),
                                     url_root=os.path.dirname(request.url_root[:-1]) + '/',
                                     name=name))

        return jsonify(success=True)


@izhero_izhero.resource
class IZheroSTChar(restful.Resource):
    method_decorators = [acl.requires_login]

    def get(self, action=None):
        usr = current_user._get_current_object()
        if not usr.get("data"):
            usr["data"] = {}
        if not usr["data"].get("zones"):
            usr["data"]["zones"] = {}
        if not usr["data"]["zones"].get("screentime"):
            usr["data"]["zones"]["screentime"] = {}

        zone_st = usr["data"]["zones"]["screentime"]

        if action == "disciplinepoll" or action == "lupoll":
            pr = restful.reqparse.RequestParser()
            pr.add_argument("lang", type=str, store_missing=False)
            args = pr.parse_args()
            q, c = self.db["PollResult"].get_results(action, lang=args.get("lang", "en"))
            return jsonify(success=True, results=[crudmgo.model_to_json(r, is_list=True) for r in q], total=c)
        elif action == "nanatrade":
            myshelf = self.db["CollectionShelf"].getshelf(usr["_id"])
            card = self.db["Card"].find_one({"code": "izcourage"})
            return jsonify(success=bool(not zone_st.get("nanatrade") and myshelf.has_card(card["_id"])))

        return jsonify(success=False)

    def post(self, action=None):
        usr = current_user._get_current_object()
        if not usr.get("data"):
            usr["data"] = {}
        if not usr["data"].get("zones"):
            usr["data"]["zones"] = {}
        if not usr["data"]["zones"].get("screentime"):
            usr["data"]["zones"]["screentime"] = {}

        zone_st = usr["data"]["zones"]["screentime"]
        basekey = "data.zones.screentime."

        if action == "hiddencoin":
            if not zone_st.get("hiddencoin"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "hiddencoin": True}})
                # usr.save()
                usr.add_dq_coins_points(1, 0)
                return jsonify(success=True)
        elif action == "brutuschallenge":
            if not zone_st.get("brutuschallenge"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "brutuschallenge": True}})
                # usr.save()
                usr.add_dq_coins_points(2, 0)
                return jsonify(success=True)
        elif action == "disciplinepoll":
            pr = restful.reqparse.RequestParser()
            pr.add_argument("ans", type=unicode, store_missing=False)
            pr.add_argument("lang", type=str, store_missing=False)
            args = pr.parse_args()
            ans = args.get("ans", "").strip()
            lang = args.get("lang", "en")
            if not zone_st.get("disciplinepoll") and ans:
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "disciplinepoll": True}})
                usr.reload()
                # usr.save()
                self.db["PollResult"].add_result("disciplinepoll",
                                                 re.sub("[\\s\\-'\",.?/!%&:;+*=@#\\^()]", "", ans.lower()),
                                                 string.capwords(ans),
                                                 lang=lang)
                q, c = self.db["PollResult"].get_results("disciplinepoll", lang=lang)
                return jsonify(success=True, results=[crudmgo.model_to_json(r, is_list=True) for r in q], total=c)
        elif action == "snoopertrick":
            if not zone_st.get("snoopertrick"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "snoopertrick": True}})
                # usr.save()
                pr = restful.reqparse.RequestParser()
                pr.add_argument("ans", type=int, store_missing=False)
                args = pr.parse_args()
                ans = args.get("ans", 0)
                if ans:
                    usr.add_dq_coins_points(-5, 0)
                else:
                    usr.add_dq_coins_points(1, 0)
                return jsonify(success=True)
        elif action == "jjmom":
            if not zone_st.get("jjmom"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "jjmom": True}})
                usr.reload()
                card = self.db["Card"].find_one({"code": "izsafety"})
                if card is not None:
                    myshelf = self.db["CollectionShelf"].getshelf(usr["_id"])
                    myshelf.add_card(card["_id"])
                return jsonify(success=True)
        elif action == "booleetrick":
            if not zone_st.get("booleetrick"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "booleetrick": True}})
                usr.reload()
                pr = restful.reqparse.RequestParser()
                pr.add_argument("ans", type=unicode, store_missing=False)
                args = pr.parse_args()
                ans = args.get("ans")
                if ans is None:
                    usr.add_dq_coins_points(2, 0)
                else:
                    pass
                return jsonify(success=True)
        elif action == "jjmobile":
            if not zone_st.get("jjmobile") and "dq_items" in usr["data"] and "izmobile" in usr["data"]["dq_items"]:
                # usr["data"]["dq_items"]["izmobile"] = -1
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "jjmobile": True,
                                                                     "data.dq_items.izmobile": -1}})
                usr.reload()
                card = self.db["Card"].find_one({"code": "jj"})
                if card is not None:
                    myshelf = self.db["CollectionShelf"].getshelf(usr["_id"])
                    myshelf.add_card(card["_id"])
                return jsonify(success=True)
        elif action == "nanatrade":
            myshelf = self.db["CollectionShelf"].getshelf(usr["_id"])
            card = self.db["Card"].find_one({"code": "izcourage"})
            if not zone_st.get("nanatrade") and myshelf.has_card(card["_id"]):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "nanatrade": True}})
                usr.reload()
                myshelf.remove_card(card["_id"])
                card = self.db["Card"].find_one({"code": "izhonor"})
                myshelf.add_card(card["_id"])
                return jsonify(success=True)
        elif action == "lupoll":
            pr = restful.reqparse.RequestParser()
            pr.add_argument("ans", type=int, store_missing=False)
            args = pr.parse_args()
            ans = args.get("ans")
            if not zone_st.get("lupoll") and ans:
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "lupoll": True}})
                usr.reload()
                self.db["PollResult"].add_result("lupoll", re.sub(r"\W", "", str(ans).lower()), "")
                q, c = self.db["PollResult"].get_results("lupoll")
                return jsonify(success=True, results=[crudmgo.model_to_json(r, is_list=True) for r in q], total=c)
        elif action == "drparkinfo":
            if not zone_st.get("drparkinfo") and "dq_items" in usr["data"] and "pinfo" in usr["data"]["dq_items"]:
                # usr["data"]["dq_items"]["pinfo"] = -1
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "drparkinfo": True,
                                                                     "data.dq_items.pinfo": -1}})
                # usr.save()
                usr.add_dq_coins_points(5, 0)
                return jsonify(success=True)

        return jsonify(success=False)


@izhero_izhero.resource
class IZheroPrivChar(restful.Resource):
    method_decorators = [acl.requires_login]

    def get(self, action=None):
        usr = current_user._get_current_object()
        if not usr.get("data"):
            usr["data"] = {}
        if not usr["data"].get("zones"):
            usr["data"]["zones"] = {}
        if not usr["data"]["zones"].get("privacy"):
            usr["data"]["zones"]["privacy"] = {}

        zone_st = usr["data"]["zones"]["privacy"]

        return jsonify(success=False)

    def post(self, action=None):
        usr = current_user._get_current_object()
        if not usr.get("data"):
            usr["data"] = {}
        if not usr["data"].get("zones"):
            usr["data"]["zones"] = {}
        if not usr["data"]["zones"].get("privacy"):
            usr["data"]["zones"]["privacy"] = {}

        zone_st = usr["data"]["zones"]["privacy"]
        basekey = "data.zones.privacy."

        if action == "snooperchallenge":
            if not zone_st.get("snooperchallenge"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "snooperchallenge": True}})
                # usr.save()
                usr.add_dq_coins_points(2, 0)
                return jsonify(success=True)
        elif action == "boo1":
            if not zone_st.get("boo1"):
                usr.collection.update({"_id": usr["_id"], basekey + "boo1": {"$ne": True}},
                                      {"$set": {basekey + "boo1": True},
                                       "$inc": {basekey + "boo_found": 1}})
                usr.reload()
                if usr["data"]["zones"]["privacy"]["boo_found"] == 6:
                    usr.add_dq_coins_points(0, 20)
                return jsonify(success=True)
        elif action == "boo2":
            if not zone_st.get("boo2"):
                usr.collection.update({"_id": usr["_id"], basekey + "boo2": {"$ne": True}},
                                      {"$set": {basekey + "boo2": True},
                                       "$inc": {basekey + "boo_found": 1}})
                usr.reload()
                if usr["data"]["zones"]["privacy"]["boo_found"] == 6:
                    usr.add_dq_coins_points(0, 20)
                return jsonify(success=True)
        elif action == "lujail":
            if not zone_st.get("lujail") and usr["data"].get("dq_items", {}).get("key"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "lujail": True,
                                                                     "data.dq_items.key": -1}})
                usr.reload()
                card = self.db["Card"].find_one({"code": "magui"})
                myshelf = self.db["CollectionShelf"].getshelf(usr["_id"])
                myshelf.add_card(card["_id"])
                return jsonify(success=True)

        return jsonify(success=False)


@izhero_izhero.resource
class IZheroCBChar(restful.Resource):
    method_decorators = [acl.requires_login]

    def get(self, action=None):
        usr = current_user._get_current_object()
        if not usr.get("data"):
            usr["data"] = {}
        if not usr["data"].get("zones"):
            usr["data"]["zones"] = {}
        if not usr["data"]["zones"].get("cyberbullying"):
            usr["data"]["zones"]["cyberbullying"] = {}

        zone_st = usr["data"]["zones"]["cyberbullying"]

        return jsonify(success=False)

    def post(self, action=None):
        usr = current_user._get_current_object()
        if not usr.get("data"):
            usr["data"] = {}
        if not usr["data"].get("zones"):
            usr["data"]["zones"] = {}
        if not usr["data"]["zones"].get("cyberbullying"):
            usr["data"]["zones"]["cyberbullying"] = {}
        if not usr["data"]["zones"].get("privacy"):
            usr["data"]["zones"]["privacy"] = {}

        zone_st = usr["data"]["zones"]["cyberbullying"]
        # zone_pv = usr["data"]["zones"]["privacy"]
        basekey = "data.zones.cyberbullying."
        basekey_pv = "data.zones.privacy."

        if action == "hiddencoin":
            if not zone_st.get("hiddencoin"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "hiddencoin": True}})
                # usr.save()
                usr.add_dq_coins_points(1, 0)
                return jsonify(success=True)
        elif action == "booleechallenge":
            if not zone_st.get("booleechallenge"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "booleechallenge": True}})
                # usr.save()
                usr.add_dq_coins_points(2, 0)
                return jsonify(success=True)
        elif action == "boo1":
            if not zone_st.get("boo1"):
                usr.collection.update({"_id": usr["_id"], basekey + "boo1": {"$ne": True}},
                                      {"$set": {basekey + "boo1": True},
                                       "$inc": {basekey_pv + "boo_found": 1}})
                usr.reload()
                if usr["data"]["zones"]["privacy"]["boo_found"] == 6:
                    usr.add_dq_coins_points(0, 20)
                return jsonify(success=True)
        elif action == "boo2":
            if not zone_st.get("boo2"):
                usr.collection.update({"_id": usr["_id"], basekey + "boo2": {"$ne": True}},
                                      {"$set": {basekey + "boo2": True},
                                       "$inc": {basekey_pv + "boo_found": 1}})
                usr.reload()
                if usr["data"]["zones"]["privacy"]["boo_found"] == 6:
                    usr.add_dq_coins_points(0, 20)
                return jsonify(success=True)
        elif action == "boo3":
            if not zone_st.get("boo3"):
                usr.collection.update({"_id": usr["_id"], basekey + "boo3": {"$ne": True}},
                                      {"$set": {basekey + "boo3": True},
                                       "$inc": {basekey_pv + "boo_found": 1}})
                usr.reload()
                if usr["data"]["zones"]["privacy"]["boo_found"] == 6:
                    usr.add_dq_coins_points(0, 20)
                return jsonify(success=True)
        elif action == "boo4":
            if not zone_st.get("boo4"):
                usr.collection.update({"_id": usr["_id"], basekey + "boo4": {"$ne": True}},
                                      {"$set": {basekey + "boo4": True},
                                       "$inc": {basekey_pv + "boo_found": 1}})
                usr.reload()
                if usr["data"]["zones"]["privacy"]["boo_found"] == 6:
                    usr.add_dq_coins_points(0, 20)
                return jsonify(success=True)
        elif action == "inzomb1cage":
            pr = restful.reqparse.RequestParser()
            pr.add_argument("ans", type=unicode, store_missing=False)
            ans = pr.parse_args().get("ans")
            if not zone_st.get("inzomb1cage") and ans and ans.replace(" ", "").lower() == "b4772":
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "inzomb1cage": True}})
                # usr.save()
                usr.add_dq_coins_points(10, 0)
                return jsonify(success=True)
        elif action == "inzomb2cage":
            pr = restful.reqparse.RequestParser()
            pr.add_argument("ans", type=unicode, store_missing=False)
            ans = pr.parse_args().get("ans")
            if not zone_st.get("inzomb2cage") and ans and ans.replace(" ", "").lower() == "b773":
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "inzomb2cage": True}})
                # usr.save()
                usr.add_dq_coins_points(10, 0)
                return jsonify(success=True)

        return jsonify(success=False)


@izhero_izhero.resource
class IZheroDCChar(restful.Resource):
    method_decorators = [acl.requires_login]

    def get(self, action=None):
        usr = current_user._get_current_object()
        if not usr.get("data"):
            usr["data"] = {}
        if not usr["data"].get("zones"):
            usr["data"]["zones"] = {}
        if not usr["data"]["zones"].get("digitalcitizens"):
            usr["data"]["zones"]["digitalcitizens"] = {}

        zone_st = usr["data"]["zones"]["digitalcitizens"]

        return jsonify(success=False)

    def post(self, action=None):
        usr = current_user._get_current_object()
        if not usr.get("data"):
            usr["data"] = {}
        if not usr["data"].get("zones"):
            usr["data"]["zones"] = {}
        if not usr["data"]["zones"].get("digitalcitizens"):
            usr["data"]["zones"]["digitalcitizens"] = {}

        zone_st = usr["data"]["zones"]["digitalcitizens"]
        basekey = "data.zones.digitalcitizens."

        if action == "hiddencoin":
            if not zone_st.get("hiddencoin"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "hiddencoin": True}})
                # usr.save()
                usr.add_dq_coins_points(1, 0)
                return jsonify(success=True)
        elif action == "jugochallenge":
            if not zone_st.get("jugochallenge"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "jugochallenge": True}})
                # usr.save()
                usr.add_dq_coins_points(2, 0)
                return jsonify(success=True)
        elif action == "honortrade":
            if not zone_st.get("honortrade") and usr.get("dq_coins") >= 30:
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "honortrade": True}})
                # usr.save()
                usr.add_dq_coins_points(-30, 0)
                card = self.db["Card"].find_one({"code": "naam"})
                myshelf = self.db["CollectionShelf"].getshelf(usr["_id"])
                myshelf.add_card(card["_id"])
                return jsonify(success=True)
        elif action == "joytrade":
            if not zone_st.get("joytrade") and usr.get("dq_coins") >= 20:
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "joytrade": True}})
                # usr.save()
                usr.add_dq_coins_points(-20, 0)
                card = self.db["Card"].find_one({"code": "naam"})
                myshelf = self.db["CollectionShelf"].getshelf(usr["_id"])
                myshelf.add_card(card["_id"])
                return jsonify(success=True)

        return jsonify(success=False)


@izhero_izhero.resource
class IZheroDFChar(restful.Resource):
    method_decorators = [acl.requires_login]
    razanswer = ("footprint", u"디지털발자국", "huella")

    def get(self, action=None):
        usr = current_user._get_current_object()
        if not usr.get("data"):
            usr["data"] = {}
        if not usr["data"].get("zones"):
            usr["data"]["zones"] = {}
        if not usr["data"]["zones"].get("digitalfootprint"):
            usr["data"]["zones"]["digitalfootprint"] = {}

        zone_st = usr["data"]["zones"]["digitalfootprint"]

        return jsonify(success=False)

    def post(self, action=None):
        usr = current_user._get_current_object()
        if not usr.get("data"):
            usr["data"] = {}
        if not usr["data"].get("zones"):
            usr["data"]["zones"] = {}
        if not usr["data"]["zones"].get("digitalfootprint"):
            usr["data"]["zones"]["digitalfootprint"] = {}

        zone_st = usr["data"]["zones"]["digitalfootprint"]
        basekey = "data.zones.digitalfootprint."

        if action == "hiddencoin":
            if not zone_st.get("hiddencoin"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "hiddencoin": True}})
                # usr.save()
                usr.add_dq_coins_points(1, 0)
                return jsonify(success=True)
        elif action == "razpuzzle":
            pr = restful.reqparse.RequestParser()
            pr.add_argument("ans", type=unicode, store_missing=False)
            ans = pr.parse_args().get("ans")
            if not zone_st.get("razpuzzle") and ans and ans.replace(" ", "").lower() in self.razanswer:
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "razpuzzle": True}})
                # usr.save()
                usr.add_dq_coins_points(5, 0)
                return jsonify(success=True)

        return jsonify(success=False)


@izhero_izhero.resource
class IZheroSecChar(restful.Resource):
    method_decorators = [acl.requires_login]

    def get(self, action=None):
        usr = current_user._get_current_object()
        if not usr.get("data"):
            usr["data"] = {}
        if not usr["data"].get("zones"):
            usr["data"]["zones"] = {}
        if not usr["data"]["zones"].get("security"):
            usr["data"]["zones"]["security"] = {}

        zone_st = usr["data"]["zones"]["security"]

        if action == "newheartpoll":
            q, c = self.db["PollResult"].get_results(action)
            return jsonify(success=True, results=[crudmgo.model_to_json(r, is_list=True) for r in q], total=c)

        return jsonify(success=False)

    def post(self, action=None):
        usr = current_user._get_current_object()
        if not usr.get("data"):
            usr["data"] = {}
        if not usr["data"].get("zones"):
            usr["data"]["zones"] = {}
        if not usr["data"]["zones"].get("security"):
            usr["data"]["zones"]["security"] = {}

        zone_st = usr["data"]["zones"]["security"]
        basekey = "data.zones.security."

        if action == "hiddencoin":
            if not zone_st.get("hiddencoin"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "hiddencoin": True}})
                # usr.save()
                usr.add_dq_coins_points(1, 0)
                return jsonify(success=True)
        elif action == "scamrock":
            if not zone_st.get("scamrock"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "scamrock": True}})
                # usr.save()
                usr.add_dq_coins_points(-10, 0)
                return jsonify(success=True)
        elif action == "spamrock":
            if not zone_st.get("spamrock"):
                pr = restful.reqparse.RequestParser()
                pr.add_argument("ans", type=int, store_missing=False)
                ans = pr.parse_args().get("ans", 0)
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "spamrock": True}})
                # usr.save()
                usr.add_dq_coins_points((-2 if ans else 1), 0)
                return jsonify(success=True)
        elif action == "razgift":
            if not zone_st.get("razgift"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "razgift": True}})
                usr.reload()
                card = self.db["Card"].find_one({"code": "jugo"})
                myshelf = self.db["CollectionShelf"].getshelf(usr["_id"])
                myshelf.add_card(card["_id"])
                return jsonify(success=True)
        elif action == "newheartpoll":
            pr = restful.reqparse.RequestParser()
            pr.add_argument("ans", type=int, store_missing=False)
            args = pr.parse_args()
            ans = args.get("ans")
            if not zone_st.get("newheartpoll") and ans:
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "newheartpoll": True}})
                usr.reload()
                self.db["PollResult"].add_result("newheartpoll", re.sub(r"\W", "", str(ans).lower()), "")
                q, c = self.db["PollResult"].get_results("newheartpoll")
                return jsonify(success=True, results=[crudmgo.model_to_json(r, is_list=True) for r in q], total=c)
        elif action == "safecheck":
            pr = restful.reqparse.RequestParser()
            pr.add_argument("ans", type=unicode, store_missing=False)
            args = pr.parse_args()
            ans = args.get("ans")
            if not zone_st.get("safecheck") and ans:
                createpwds = self.db["SurveyDQ"].find_one({"name": "createpwd"}) or {}
                createpwd = list(self.db["SurveyDQAnswer"].find({"surveyid": createpwds.get("_id"),
                                                                 "created.by": usr.id}).sort("_id", pymongo.DESCENDING)
                                                                                       .limit(1))
                createpwd = (createpwd and createpwd[0]) or None
                if createpwd is not None and len(createpwd.get("answers", 0)) > 0 and \
                   createpwd["answers"][0]["ans"] == ans:
                    usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "safecheck": True}})
                    usr.reload()
                    card = self.db["Card"].find_one({"code": "izprotect"})
                    myshelf = self.db["CollectionShelf"].getshelf(usr["_id"])
                    myshelf.add_card(card["_id"])
                    return jsonify(success=True)

        return jsonify(success=False)


@izhero_izhero.resource
class IZheroCTChar(restful.Resource):
    method_decorators = [acl.requires_login]

    def get(self, action=None):
        usr = current_user._get_current_object()
        if not usr.get("data"):
            usr["data"] = {}
        if not usr["data"].get("zones"):
            usr["data"]["zones"] = {}
        if not usr["data"]["zones"].get("criticalthinking"):
            usr["data"]["zones"]["criticalthinking"] = {}

        zone_st = usr["data"]["zones"]["criticalthinking"]

        if action == "secretpoll":
            q, c = self.db["PollResult"].get_results(action)
            return jsonify(success=True, results=[crudmgo.model_to_json(r, is_list=True) for r in q], total=c)

        return jsonify(success=False)

    def post(self, action=None):
        usr = current_user._get_current_object()
        if not usr.get("data"):
            usr["data"] = {}
        if not usr["data"].get("zones"):
            usr["data"]["zones"] = {}
        if not usr["data"]["zones"].get("criticalthinking"):
            usr["data"]["zones"]["criticalthinking"] = {}

        zone_st = usr["data"]["zones"]["criticalthinking"]
        basekey = "data.zones.criticalthinking."

        if action == "hiddencoin":
            if not zone_st.get("hiddencoin"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "hiddencoin": True}})
                # usr.save()
                usr.add_dq_coins_points(1, 0)
                return jsonify(success=True)
        elif action == "discernheartgift":
            if not zone_st.get("discernheartgift"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "discernheartgift": True}})
                usr.reload()
                card = self.db["Card"].find_one({"code": "izshield"})
                myshelf = self.db["CollectionShelf"].getshelf(usr["_id"])
                myshelf.add_card(card["_id"])
                return jsonify(success=True)
        elif action == "jjwater":
            if not zone_st.get("jjwater") and "dq_items" in usr["data"] and "bucket-water" in usr["data"]["dq_items"]:
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "jjwater": True,
                                                                     "data.dq_items.bucket-water": -1}}),
                # usr.save()
                usr.add_dq_coins_points(10, 0)
                return jsonify(success=True)
        elif action == "sirenchallenge":
            if not zone_st.get("sirenchallenge"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "sirenchallenge": True}})
                # usr.save()
                usr.add_dq_coins_points(2, 0)
                return jsonify(success=True)
        elif action == "secretpoll":
            pr = restful.reqparse.RequestParser()
            pr.add_argument("ans", type=int, store_missing=False)
            args = pr.parse_args()
            ans = args.get("ans")
            if not zone_st.get("secretpoll") and ans:
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "secretpoll": True}})
                usr.reload()
                self.db["PollResult"].add_result("secretpoll", re.sub(r"\W", "", str(ans).lower()), "")
                q, c = self.db["PollResult"].get_results("secretpoll")
                return jsonify(success=True, results=[crudmgo.model_to_json(r, is_list=True) for r in q], total=c)
        elif action == "waterfountain":
            if not zone_st.get("waterfountain") and "dq_items" in usr["data"] and "bucket" in usr["data"]["dq_items"]:
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "waterfountain": True,
                                                                     "data.dq_items.bucket": -1,
                                                                     "data.dq_items.bucket-water": 1}})
                usr.reload()
                return jsonify(success=True)

        return jsonify(success=False)


@izhero_izhero.resource
class IZheroEmChar(restful.Resource):
    method_decorators = [acl.requires_login]
    # TODO: create an admin page to insert allowed answers.
    mabelans = (u"dontworryiknowhowyoufeel", u"걱정하지마나도네기분이해해",
                u"notepreocupesyosécómotesientes", u"notepreocupesyosecomotesientes")

    def get(self, action=None):
        usr = current_user._get_current_object()
        if not usr.get("data"):
            usr["data"] = {}
        if not usr["data"].get("zones"):
            usr["data"]["zones"] = {}
        if not usr["data"]["zones"].get("empathy"):
            usr["data"]["zones"]["empathy"] = {}

        zone_st = usr["data"]["zones"]["empathy"]

        if action == "secretpoll":
            q, c = self.db["PollResult"].get_results(action)
            return jsonify(success=True, results=[crudmgo.model_to_json(r, is_list=True) for r in q], total=c)

        return jsonify(success=False)

    def post(self, action=None):
        usr = current_user._get_current_object()
        if not usr.get("data"):
            usr["data"] = {}
        if not usr["data"].get("zones"):
            usr["data"]["zones"] = {}
        if not usr["data"]["zones"].get("empathy"):
            usr["data"]["zones"]["empathy"] = {}

        zone_st = usr["data"]["zones"]["empathy"]
        basekey = "data.zones.empathy."

        if action == "hiddencoin":
            if not zone_st.get("hiddencoin"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "hiddencoin": True}})
                # usr.save()
                usr.add_dq_coins_points(1, 0)
                return jsonify(success=True)
        elif action == "jimmybully":
            if not zone_st.get("jimmybully"):
                pr = restful.reqparse.RequestParser()
                pr.add_argument("ans", type=int, store_missing=False)
                ans = pr.parse_args().get("ans", 0)
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "jimmybully": True}})
                # usr.save()
                usr.add_dq_coins_points(-2 if ans else 1, 0)
                return jsonify(success=True)
        elif action == "sophiabully":
            if not zone_st.get("sophiabully"):
                pr = restful.reqparse.RequestParser()
                pr.add_argument("ans", type=int, store_missing=False)
                ans = pr.parse_args().get("ans", 0)
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "sophiabully": True}})
                # usr.save()
                usr.add_dq_coins_points(-2 if ans else 1, 0)
                return jsonify(success=True)
        elif action == "yarotrick":
            if not zone_st.get("yarotrick"):
                pr = restful.reqparse.RequestParser()
                pr.add_argument("ans", type=int, store_missing=False)
                ans = pr.parse_args().get("ans", 0)
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "yarotrick": True}})
                # usr.save()
                usr.add_dq_coins_points(-2 if ans else 1, 0)
                return jsonify(success=True)
        elif action == "mabelconsole":
            pr = restful.reqparse.RequestParser()
            pr.add_argument("ans", type=unicode, store_missing=False)
            ans = pr.parse_args().get("ans")
            if not zone_st.get("mabelconsole") and ans and\
               ans.replace(".", "").replace(",", "").replace("!", "").replace(u"¡", "").\
               replace(" ", "").replace("'", "").replace(u"’", "").lower() in self.mabelans:
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "mabelconsole": True}})
                usr.reload()
                card = self.db["Card"].find_one({"code": "izearspillar"})
                myshelf = self.db["CollectionShelf"].getshelf(usr["_id"])
                myshelf.add_card(card["_id"])
                return jsonify(success=True)
        elif action == "wickeechallenge":
            if not zone_st.get("wickeechallenge"):
                usr.collection.update({"_id": usr["_id"]}, {"$set": {basekey + "wickeechallenge": True}})
                # usr.save()
                usr.add_dq_coins_points(2, 0)
                return jsonify(success=True)

        return jsonify(success=False)


apistudent = restful.Api(izhero_izhero)
apistudent.add_resource(IZHeroUpdate, "/profile", endpoint="profile")
apistudent.add_resource(IZHeroName, "/name", endpoint="name")
apistudent.add_resource(IZheroRegister, "/register", endpoint="register")
apistudent.add_resource(IZHeroMembership, "/membership", endpoint="membership")
apistudent.add_resource(IZHeroActivation, "/activate", endpoint="activate")
apistudent.add_resource(IZHeroActivation, "/activate/<itemid>", endpoint="activateid")
apistudent.add_resource(IZHeroSquad, "/squad", endpoint="squad")
apistudent.add_resource(IZHeroSquad, "/squad/<code>", endpoint="squadcode")
apistudent.add_resource(Countries, "/countries", endpoint="countries")
apistudent.add_resource(Schools, "/schools", endpoint="schools")
apistudent.add_resource(Schools, "/schools/<country>", endpoint="cschools")
apistudent.add_resource(IZHeroResetPwd, "/resetpwd", endpoint="resetpwd")
apistudent.add_resource(IZHeroSendUserName, "/sendusername", endpoint="sendusername")
apistudent.add_resource(IZHeroEmailMediaRules, "/emailmediarules", endpoint="emailmediarules")
apistudent.add_resource(IZHeroEmailBalanceScreen, "/emailbalancescreen", endpoint="emailbalancescreen")
apistudent.add_resource(IZHeroData, "/data", endpoint="data")
apistudent.add_resource(IZHeroChild, "/child", endpoint="child")
apistudent.add_resource(IZHeroParentToChild, "/child/login/<childid>", endpoint="child_login")
apistudent.add_resource(IZHeroChildToParent, "/parent/login", endpoint="parent_login")
apistudent.add_resource(IZHeroRanking, "/rank", endpoint="rank")
apistudent.add_resource(IZHeroDQRanking, "/dqrank", endpoint="dqrank")
apistudent.add_resource(IZHeroFeedback, "/feedback", endpoint="feedback")
apistudent.add_resource(DqHasLeveled, "/dqhasleveled", endpoint="dqhasleveled")
apistudent.add_resource(IZHeroSupport, "/givesupport", endpoint="givesupport")
apistudent.add_resource(IZheroSTChar, "/screentime/<action>", endpoint="screentime_action")
apistudent.add_resource(IZheroPrivChar, "/privacy/<action>", endpoint="privacy_action")
apistudent.add_resource(IZheroCBChar, "/cyberbullying/<action>", endpoint="cyberbullying_action")
apistudent.add_resource(IZheroDCChar, "/digitalcitizens/<action>", endpoint="digitalcitizens_action")
apistudent.add_resource(IZheroDFChar, "/digitalfootprint/<action>", endpoint="digitalfootprints_action")
apistudent.add_resource(IZheroSecChar, "/security/<action>", endpoint="security_action")
apistudent.add_resource(IZheroCTChar, "/criticalthinking/<action>", endpoint="criticalthinking_action")
apistudent.add_resource(IZheroEmChar, "/empathy/<action>", endpoint="empathy_action")
