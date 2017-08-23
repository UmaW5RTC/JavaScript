# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask.ext.wtf import Form
from flask import current_app
from wtforms import StringField, PasswordField, BooleanField, DateField, validators, SelectField
from mod_auth.model import generate_code, UserMgoMixin
from werkzeug.security import safe_str_cmp
from rest import crud, crudmgo
from dateutil import tz
from bson import ObjectId
import datetime
import bcrypt
import random
import memcache
import cPickle


_mc = memcache.Client(['127.0.0.1:11211'], debug=0)
_WORLD_POINTS_MC_KEY = "mongodb.model.izhero.world_points"
_WORLD_COINS_MC_KEY = "mongodb.model.izhero.world_coins"
_WORLD_CACHE_TIME = 300
LANGUAGES = ("en", "ko","es")

class SchoolForm(Form):
    name = StringField("School Name", [crud.put_optional, validators.DataRequired()])


class IZHeroForm(Form):
    username = StringField("Username", [crud.put_optional, validators.DataRequired()])
    familyname = StringField("Family Name", [crud.put_optional, validators.Optional()])  # validators.DataRequired()])
    givenname = StringField("Given Name", [crud.put_optional, validators.Optional()])  # validators.DataRequired()])
    password = PasswordField("Password", [crud.put_optional, validators.DataRequired(),
                                          # bcrypt has a max length of 72, including a terminating zero and 16 bytes of
                                          # random salt, we are left with 55 usable bytes
                                          validators.Length(min=8, max=55)])
    dob = DateField("Date of Birth", [crud.put_optional, validators.Optional()])  # validators.DataRequired()])
    country = StringField("Country", [crud.put_optional], default="Singapore")
    school = StringField("School", [crud.put_optional, validators.Optional()])
    parent_familyname = StringField("Family Name", [crud.put_optional, validators.Optional()])
    parent_givenname = StringField("Given Name", [crud.put_optional, validators.Optional()])
    parent_email = StringField("Email", [crud.put_optional, validators.Optional(), validators.Email()])
    parent_contact = StringField("Contact No.", [crud.put_optional, validators.Optional()])
    is_parent = BooleanField("is_parent", [crud.put_optional], default=False)
    gender = crud.NullSelectField("Gender", [crud.put_optional, validators.Optional(True)],
                                  choices=[("m", "m"), ("f", "f")])
    how = StringField("How did you hear about us?", [crud.put_optional, validators.Optional()])
    updates = BooleanField("Receive Updates", [crud.put_optional, validators.Optional()], default=False)
    lang = crud.NullSelectField("Language", [crud.put_optional, validators.Optional(True)],
                                choices=[(l, l) for l in LANGUAGES])

    def validate_username(self, field):
        if " " in field.data or "\t" in field.data or "\r" in field.data or "\n" in field.data:
            raise validators.ValidationError("Username cannot contain spaces")


class TeacherForm(Form):
    username = StringField("Username", [crud.put_optional, validators.DataRequired()])
    familyname = StringField("Family Name", [crud.put_optional, validators.DataRequired()])
    givenname = StringField("Family Name", [crud.put_optional, validators.DataRequired()])
    email = StringField("Username", [crud.put_optional, validators.DataRequired(), validators.Email()])
    password = PasswordField("Password", [crud.put_optional, validators.DataRequired(),
                                          validators.Length(min=8, max=55)])
    country = StringField("Country", [crud.put_optional, validators.DataRequired()])
    school = StringField("School", [crud.put_optional, validators.DataRequired()])
    contact = StringField("Contact No.", [crud.put_optional, validators.Optional()])
    referral = StringField("Referral Code", [crud.put_optional, validators.Optional()])

    def validate_username(self, field):
        if " " in field.data or "\t" in field.data or "\r" in field.data or "\n" in field.data:
            raise validators.ValidationError("Username cannot contain spaces")


class Country(crudmgo.RootDocument):
    __collection__ = "countries"
    __crud_searchfield__ = ("name",)
    __form__ = SchoolForm

    structure = {
        "name": basestring,
        "schools": [basestring],
        "schools_unverified": [basestring],
        "created": datetime.datetime
    }
    indexes = [
        {"fields": "name",
         "unique": True},
        {"fields": "schools"},
        {"fields": "schools_unverified"}
    ]
    required = ["name"]
    default_values = {"created": crudmgo.localtime, "schools": [], "schools_unverified": []}

    def insert_school(self, country, school):
        if not school:
            return

        ctry = self.find_one({"name": country})
        if not ctry or school in ctry["schools"]:
            return

        if not ctry["schools_unverified"]:
            ctry["schools_unverified"] = [school]
        elif school not in ctry["schools_unverified"]:
            ctry["schools_unverified"].append(school)
        ctry.save()


class Teacher(crudmgo.RootDocument, UserMgoMixin):
    __collection__ = "teachers"
    __json_omit__ = ("password", "activationcode")
    __name_field__ = "givenname"
    __crud_searchfield__ = ("username", "givenname", "familyname", "email")
    __form__ = TeacherForm

    structure = {
        "username": basestring,
        "password": basestring,
        "familyname": basestring,
        "givenname": basestring,
        "email": basestring,
        "country": basestring,
        "school": basestring,
        "contact": basestring,
        "squads": [{
            "code": basestring,
            "name": basestring,
            "school": basestring,
            "grade": basestring,
            "level": int,
            "homeroom_teacher": ObjectId
        }],
        "assigned_squads": [{
            "code": basestring,
            "name": basestring,
            "school": basestring,
            "grade": basestring
        }],
        "activationcode": basestring,
        "accesscode": [basestring],
        "status": bool,
        "created": datetime.datetime,
        "lastlogin": datetime.datetime,
        "hod": ObjectId,
        "referral": basestring,
        "lang": basestring
    }
    indexes = [
        {"fields": "username",
         "unique": True},
        {"fields": "email",
         "unique": True},
        {"fields": "squads.code",
         "unique": True,
         "check": False},
        {"fields": "country"}
    ]
    required = ["username", "email", "password", "familyname", "givenname", "contact"]
    default_values = {"activationcode": generate_code, "created": crudmgo.localtime,
                      "status": False, "squads": [], "assigned_squads": [], "lang": "en"}

    @property
    def role(self):
        return "Teacher" if self.get("_id", None) else None

    def __on_login__(self, _):
        self["lastlogin"] = crudmgo.localtime()
        self.save()
        db = self.collection.database
        izhero = db["IZHero"].find_one({"username": self["username"]})
        if izhero and izhero["password"] == self["password"]:
            current_app.auth.alt_login_user(izhero, {"AUTH_COOKIE_NAME": "auth_session_id"})
        elif not izhero:
            izhero = self.create_alt_izhero()
            if izhero:
                current_app.auth.alt_login_user(izhero, {"AUTH_COOKIE_NAME": "auth_session_id"})

    def create_alt_izhero(self, fullaccess=False, sponsor=None, hod=None):
        try:
            izhero = self.collection.database["IZHero"]()
            izhero["username"] = self["username"]
            izhero["familyname"] = self["familyname"]
            izhero["givenname"] = self["givenname"]
            izhero["password"] = self["password"]
            izhero["country"] = self["country"]
            izhero["school"] = self.get("school")
            izhero["guardiansack"] = self["status"]
            izhero["status"] = True
            izhero["teacher"] = True
            izhero["hod"] = hod
            if fullaccess:
                izhero["fullaccess"] = True
                if sponsor:
                    izhero["sponsor"] = sponsor
            izhero.save()
            return izhero
        except Exception as e:
            print(e)
            pass

        return False

    def authenticate(self, pwd):
        pwd = pwd.encode("utf-8") if isinstance(pwd, unicode) else pwd
        password = self["password"].encode("utf-8") if isinstance(self["password"], unicode) else self["password"]
        return safe_str_cmp(bcrypt.hashpw(pwd, password), password)

    def update_password(self, pwd):
        self["password"] = IZHero.hash_password(pwd)
        # TODO: update IZHero's password

    def update_country(self, country):
        return self._update_isin_field(("Country", "name"), "country", country, "Invalid country selected.")

    def update_username(self, username):
        return self._update_unique_field("username", self.normalize_username(username),
                                         "Username is already in use.")

    def update_email(self, email):
        err = self._update_unique_field("email", email, "Email is already in use.")
        if err is None:
            self["username"] = self.normalize_username(email)
        return err

    def has_squad(self, squadcode, anyone=False):
        is_squad = False

        if squadcode:
            squads = self["squads"] + self.get("assigned_squads", [])
            if squads:
                if not isinstance(squadcode, (list, tuple)):
                    squadcode = (squadcode,)

                for sc in squadcode:
                    for sq in squads:
                        if sq and sq["code"] == sc:
                            is_squad = True
                            break
                    else:
                        if not anyone:
                            break
                        continue

                    if anyone:
                        break
        return is_squad

    def has_squadname(self, squadname, school=None):
        if not school and self.get("school"):
            school = self["school"]

        count = self.collection.find({"squads.school": school, "squads.name": squadname}).count()
        if count == 0:
            count = self.collection.find({"assigned_squads.school": school, "assigned_squads.name": squadname}).count()
        return count > 0

    def find_teacher_of_squad(self, code, subset=False):
        if subset:
            teacher = self.collection.find_one({"assigned_squads.code": code},
                                               {"assigned_squads.$": 1, "username": 1,
                                                "familyname": 1, "givenname": 1,
                                                "lastlogin": 1})
            if not teacher:
                teacher = self.collection.find_one({"squads.code": code},
                                                   {"squads.$": 1, "username": 1,
                                                    "familyname": 1, "givenname": 1,
                                                    "lastlogin": 1})
        else:
            teacher = self.find_one({"assigned_squads.code": code}) or self.find_one({"squads.code": code})
        return teacher

    @staticmethod
    def generate_squadcode():
        # i, l, 1, o, 0, u, v, 5, S, 2, Z are not included because they look similar and might confuse kids.
        l = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'M', 'N', 'P', 'Q', 'R', 'T', 'W', 'X', 'Y',
             '3', '4', '6', '7', '8', '9']
        code = ""
        for i in xrange(6):
            code += random.choice(l)
        return code


class IZHero(crudmgo.RootDocument, UserMgoMixin):
    __collection__ = "izheroes"
    __json_omit__ = ("password", "activationcode", "pwdreset", "accesscode", "lang")
    __crud_searchfield__ = ("username", "givenname", "familyname", "parent.email", "squad.code")
    __form__ = IZHeroForm
    __name_field__ = "givenname"

    structure = {
        "username": basestring,
        "familyname": basestring,
        "givenname": basestring,
        "password": basestring,
        "genpwd": basestring,
        "dob": datetime.datetime,
        "country": basestring,
        "school": basestring,
        "parent": {
            "familyname": basestring,
            "givenname": basestring,
            "email": basestring,
            "contact": basestring
        },
        "squad": {
            "code": basestring,
            "name": basestring
        },
        "newsquad": {
            "code": basestring,
            "time": datetime.datetime
        },
        "activationcode": basestring,
        "guardiansack": bool,
        "status": bool,
        "points": int,
        "points_stage": {"e0": int, "e1": int, "e2": int, "e3": int, "e4": int, "e5": int, "e6": int, "e7": int},
        "coins": int,
        "coins_stage": {"e0": int, "e1": int, "e2": int, "e3": int, "e4": int, "e5": int, "e6": int, "e7": int},
        "donated": int,
        "progress": [],
        "data": {},
        "created": datetime.datetime,
        "lastlogin": datetime.datetime,
        "mystery_cd": int,
        "mystery_gift": int,
        "pwdreset": {
            "code": basestring,
            "expiry": datetime.datetime
        },
        "teacher": bool,
        "is_parent": bool,
        "no_counsel": bool,
        "how": basestring,
        "updates": bool,
        "gender": basestring,
        "hod": ObjectId,

        # dq fields
        "unopened_cards": int,
        "dq_points": int,
        "dq_coins": int,
        # "dq_points_stage": {}, # points earned by each mission are standard and only once
        "dq_coins_stage": {},
        "dq_progress": {},
        "dq_level": int,
        "dq_level_progress": int,
        "dq_has_leveled": bool,
        "accesscode": basestring,
        "fullaccess": bool,
        "sponsor": basestring,
        "activationreset": datetime.datetime,
        "lang": basestring
    }
    indexes = [
        {"fields": "username",
         "unique": True},
        {"fields": "squad.code"},
        {"fields": ["status", "username"]},
        {"fields": "parent.email"},
        {"fields": "school"},
        {"fields": ["country", "school"]}
    ]
    required = ["username", "password"]
    default_values = {"activationcode": generate_code, "created": crudmgo.localtime, "points": 0, "coins": 0,
                      "status": True, "guardiansack": False, "progress": [], "data": {}, "mystery_gift": 0,
                      "mystery_cd": 0, "donated": 0, "teacher": False, "is_parent": False, "no_counsel": False,

                      "unopened_cards": 0, "dq_points": 0, "dq_coins": 0, "dq_coins_stage": {}, "dq_progress": {},
                      "dq_level": 1, "dq_level_progress": 0, "dq_has_leveled": False, "lang": "en"}

    @property
    def role(self):
        if self.get("_id", None):
            if self.get("teacher"):
                return "Teacher"
            if self.get("is_parent"):
                return "Parent"
            return "Student"
        return None

    @property
    def is_active(self):
        if self.is_anonymous:
            return True

        activated = self.get("guardiansack", False)

        if not activated:

            squad = self.get("squad")
            if isinstance(squad, dict) and squad.get("code"):
                activated = True
                
                # if self["parent"].get("email"):
                #     activated = False

                # if self.get("teacher"):
                #     activated = True
                # school --> must need activation,too by JK

            else:
                created = self.get("activationreset") or self.get("created")
                if not isinstance(created, datetime.datetime):
                    created = None
                elif not created.tzinfo:
                    created.replace(tzinfo=tz.tzutc())

                if created and (created + datetime.timedelta(days=7)) > crudmgo.localtime():
                    activated = True
                    
                # /school --> must need activation by JK

        return self.get("status", False) and activated

    @property
    def world_points(self):
        points = _mc.get(_WORLD_POINTS_MC_KEY)

        if points:
            points = cPickle.loads(points)
        else:
            agg = self.collection.aggregate([{"$group": {"_id": None,
                                                         "e1": {"$sum": "$points_stage.e1"},
                                                         "e2": {"$sum": "$points_stage.e2"},
                                                         "e3": {"$sum": "$points_stage.e3"},
                                                         "e4": {"$sum": "$points_stage.e4"},
                                                         "e5": {"$sum": "$points_stage.e5"},
                                                         "e6": {"$sum": "$points_stage.e6"},
                                                         "e7": {"$sum": "$points_stage.e7"}}}])
            points = agg["result"][0]
            _mc.set(_WORLD_POINTS_MC_KEY, cPickle.dumps(points), _WORLD_CACHE_TIME)
        return points

    @property
    def world_coins(self):
        coins = _mc.get(_WORLD_COINS_MC_KEY)

        if coins:
            coins = cPickle.loads(coins)
        else:
            agg = self.collection.aggregate([{"$group": {"_id": None,
                                                         "e1": {"$sum": "$coins_stage.e1"},
                                                         "e2": {"$sum": "$coins_stage.e2"},
                                                         "e3": {"$sum": "$coins_stage.e3"},
                                                         "e4": {"$sum": "$coins_stage.e4"},
                                                         "e5": {"$sum": "$coins_stage.e5"},
                                                         "e6": {"$sum": "$coins_stage.e6"},
                                                         "e7": {"$sum": "$coins_stage.e7"}}}])
            coins = agg["result"][0]
            _mc.set(_WORLD_COINS_MC_KEY, cPickle.dumps(coins), _WORLD_CACHE_TIME)
        return coins

    @property
    def squadcode(self):
        return self.get("squad", None) and self["squad"].get("code", None)

    def auth_loader_values(self):
        d = {  # "world_points": self.world_points,
             }
        if self.get("teacher") and self.get("username"):
            db = self.collection.database
            teach = db["Teacher"].find_one({"username": self["username"]})
            if teach:
                d["__email__"] = teach["email"]
                d["__contact__"] = teach["contact"]
        return d

    def authenticate(self, pwd):
        pwd = pwd.encode("utf-8") if isinstance(pwd, unicode) else pwd
        password = self["password"].encode("utf-8") if isinstance(self["password"], unicode) else self["password"]
        return safe_str_cmp(bcrypt.hashpw(pwd, password), password)

    def update_password(self, pwd):
        self["password"] = self.hash_password(pwd)

    def update_parent_email(self, email):
        self.init_parent()
        self["parent"]["email"] = email

    def update_parent_familyname(self, name):
        self.init_parent()
        self["parent"]["familyname"] = name

    def update_parent_givenname(self, name):
        self.init_parent()
        self["parent"]["givenname"] = name

    def update_parent_contact(self, contact):
        self.init_parent()
        self["parent"]["contact"] = contact

    def update_dob(self, dob):
        return self._update_datetime("dob", dob)

    def update_country(self, country):
        return self._update_isin_field(("Country", "name"), "country", country, "Invalid country selected.")

    def update_username(self, username):
        return self._update_unique_field("username", self.normalize_username(username),
                                         "Username is already in use.")

    def init_parent(self):
        if not self["parent"]:
            self["parent"] = {"familyname": "", "givenname": "", "email": "", "contact": ""}

    def __on_login__(self, _):
        pwd = self.get("genpwd")
        if pwd and pwd != "1":
            self["genpwd"] = "1"
        self["lastlogin"] = crudmgo.localtime()
        self.save()

        if self.get("teacher"):
            db = self.collection.database
            teach = db["Teacher"].find_one({"username": self["username"], "password": self["password"], "status": True})
            if teach:
                current_app.auth.alt_login_user(teach, {"AUTH_COOKIE_NAME": "auth_admin_session_id"})

    def add_coins(self, coins):
        if self.get("_id") and isinstance(coins, (int, long, float)):
            self.collection.update({"_id": self["_id"]},
                                   {"$inc": {"coins": coins}})
            self["coins"] = self["coins"] + coins if self.get("coins") else coins
            return True
        return False

    def add_points(self, points):
        if self.get("_id") and isinstance(points, (int, long, float)):
            self.collection.update({"_id": self["_id"]},
                                   {"$inc": {"points": points}})
            self["points"] = self["points"] + points if self.get("points") else points
            return True
        return False

    def add_coins_points(self, coins, points):
        if self.get("_id") and isinstance(coins, (int, long, float)) and isinstance(points, (int, long, float)):
            self.collection.update({"_id": self["_id"]},
                                   {"$inc": {"coins": coins, "points": points}})
            self["coins"] = self["coins"] + coins if self.get("coins") else coins
            self["points"] = self["points"] + points if self.get("points") else points
            return True
        return False

    def add_dq_coins_points(self, coins, points, mission=None):
        if self.get("_id") and isinstance(coins, (int, long, float)) and isinstance(points, (int, long, float)):
            coins = int(coins)
            points = int(points)

            if self.get("dq_coins") is None or self.get("dq_points") is None:
                d = {}
                if self.get("dq_coins") is None:
                    d["dq_coins"] = 0
                    self["dq_coins"] = 0
                if self.get("dq_points") is None:
                    d["dq_points"] = 0
                    self["dq_points"] = 0

                self.collection.update({"_id": self["_id"]},
                                       {"$set": d})

            d = {"$inc": {"dq_coins": coins, "dq_points": points}}
            if isinstance(mission, (str, unicode)):
                d["$set"] = {"dq_coins_stage." + mission.lower(): coins}

            self.collection.update({"_id": self["_id"]}, d)
            self.reload()
            d = {"$set": {}}
            if self["dq_coins"] < 0:
                d["$set"]["dq_coins"] = 0
                self["dq_coins"] = 0
            if self["dq_points"] < 0:
                d["$set"]["dq_points"] = 0
                self["dq_points"] = 0
            if len(d["$set"]) > 0:
                self.collection.update({"_id": self["_id"]}, d)

            if points:
                pre_level = self.get("dq_level") or 1
                level, prog = self.calc_level()

                """if pre_level < 16:
                    unopened_cards = level - 16 if level > 16 else 0

                    if pre_level < 16 <= level:
                        unopened_cards += 1
                    if pre_level < 14 <= level:
                        unopened_cards += 1
                    if pre_level < 12 <= level:
                        unopened_cards += 1
                    if pre_level < 10 <= level:
                        unopened_cards += 1
                    if pre_level < 7 <= level:
                        unopened_cards += 1
                    if pre_level < 4 <= level:
                        unopened_cards += 1
                else:
                    unopened_cards = (level - pre_level) if level > pre_level else 0"""
                unopened_cards = (level - pre_level)

                # checks dq_points as a requirement to prevent racing condition.
                res = self.collection.update({"_id": self["_id"], "dq_points": self["dq_points"]},
                                             {"$set": {"dq_level": level,
                                                       "dq_level_progress": prog,
                                                       "dq_has_leveled": level > pre_level},
                                              "$inc": {"unopened_cards": unopened_cards}})
                if res and res.get("nModified"):
                    self.reload()
            return True
        return False

    def calc_level(self):
        points = int(self.get("dq_points") or 0)
        # level_points = [(10, 10), (20, 5), (30, 2), (40, 6), (50, 10), (100, 10), (200, 7)]
        level_points = [(30, 17), (40, 6), (50, 10), (100, 10), (200, 7)]
        points_needed = 0
        level = 1
        prog = 0
        for i in level_points:
            # [0] is points increment per level.
            # [1] is total number of continuous levels that uses this increment value.
            diff = i[0] * i[1]
            if points <= points_needed + diff:
                gains = (points - points_needed) / i[0]
                level += gains
                prog = (points - points_needed - (gains * i[0])) * 100 / i[0]
                break
            else:
                level += i[1]
                points_needed += diff

        return level, prog

    def update_dq_progress(self, mission, save=True):
        if not self.get("_id"):
            return False

        mission = mission.lower()
        timenow = crudmgo.localtime()

        if not isinstance(self.get("dq_progress"), dict):
            self["dq_progress"] = {}
        if mission not in self["dq_progress"]:
            self["dq_progress"][mission] = {"first": timenow,
                                            "hits": 0,
                                            "last": None}

        self["dq_progress"][mission]["hits"] += 1
        self["dq_progress"][mission]["last"] = timenow
        if save:
            self.save()
        return True

    def donate_coins(self, coins):
        # TODO: refactor this number out as a config
        mystery = 10
        if self.get("_id") and isinstance(coins, (int, long, float)) and coins > 0 and self.get("coins") and self["coins"] >= coins:
            res = self.collection.update({"_id": self["_id"], "coins": {"$gte": coins}},
                                         {"$inc": {"coins": -coins, "donated": coins}})

            if res and res.get("nModified"):
                self["coins"] -= coins
                self["donated"] = self["donated"] + coins if self.get("donated") else coins

                self["mystery_cd"] = self["mystery_cd"] + coins if self.get("mystery_cd") else coins
                if not self.get("mystery_gift"):
                    self["mystery_gift"] = 0
                earned_gift = self["mystery_cd"] >= mystery

                while self["mystery_cd"] >= mystery:
                    self["mystery_gift"] += 1
                    self["mystery_cd"] -= mystery

                mystery = 0 if earned_gift else mystery - self["mystery_cd"]
                self.collection.update({"_id": self["_id"]},
                                       {"$set": {"mystery_cd": self["mystery_cd"],
                                                 "mystery_gift": self["mystery_gift"]}})
                return True, mystery
        return False, mystery

    @staticmethod
    def generate_password(length=8):
        l = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'M', 'N', 'P', 'Q', 'R', 'T', 'W', 'X', 'Y',
             'a', 'b', 'c', 'd', 'e', 'f', 'h', 'j', 'm', 'n', 'p', 'q', 'r', 's', 'w', 'x', 'y', 'z',
             '3', '4', '6', '7', '8',
             '@', '#', '%', '&', '-', '_', '=', '?', '.']
        pwd = ""
        for i in xrange(length):
            pwd += random.choice(l)
        return pwd

    @staticmethod
    def hash_password(pwd):
        password = pwd.encode("utf-8") if isinstance(pwd, unicode) else pwd
        return bcrypt.hashpw(password, bcrypt.gensalt())

    def anonymous(self):
        user = self()
        user["_id"] = None
        user["id"] = None
        user["givenname"] = "Anonymous"
        return user

    def create_parent(self, username, password, email, givenname, familyname, contact, country):
        parent = self.find_one({"parent.email": email, "is_parent": True})

        if not parent and username and contact and password and givenname\
                and familyname and not self.find({"username": username}).count():
            parent = self()
            parent["is_parent"] = True
            parent["guardiansack"] = True
            parent["status"] = True
            parent["activationcode"] = ""
            parent["username"] = username
            parent["givenname"] = givenname
            parent["familyname"] = familyname
            parent["country"] = country
            parent["parent"] = {
                "email": email,
                "contact": contact
            }
            parent.update_password(password)
            parent.save()
        elif not parent:
            parent = None

        return parent

    def is_child_of(self, parent):
        return parent.has_role("parent") and self.get("parent") and parent.get("parent") and\
            self["parent"].get("email") == parent["parent"].get("email")

    def has_squad(self, squadcode):
        if self.get("teacher"):
            db = self.collection.database
            teach = db["Teacher"].find_one({"username": self["username"], "password": self["password"]})
            if teach:
                return teach.has_squad(squadcode)
        return False


class CoinLog(crudmgo.RootDocument):
    __collection__ = "coinlogs"

    structure = {
        "_id": ObjectId,
        "missions": [{
            "stage": int,
            "mission": basestring,
            "sub_mission": basestring,
            "coins": int,
            "on": datetime.datetime
        }],
        "donations": [{
            "name": basestring,
            "coins": int,
            "on": datetime.datetime
        }],
        "purchases": [{
            "name": basestring,
            "type": basestring,
            "on": datetime.datetime
        }]
    }
    default_values = {"missions": [], "donations": []}

    def getlog(self, userid):
        try:
            if not isinstance(userid, ObjectId):
                userid = ObjectId(userid)
            logger = self.find_one({"_id": userid})
            if not logger:
                logger = self()
                logger["_id"] = userid
            return logger
        except Exception:
            pass

        return None

    def log_mission(self, coins, stage, mission, sub_mission=None):
        if self.get("_id") and coins:
            log = {
                "stage": stage,
                "mission": mission,
                "sub_mission": sub_mission,
                "coins": coins,
                "on": crudmgo.utctime()
            }
            if not self["missions"]:
                self["missions"] = []
            self["missions"].append(log)
            self.save()
            return True
        return False

    def log_donation(self, coins, name=None):
        if self.get("_id") and coins:
            log = {
                "name": name,
                "coins": coins,
                "on": crudmgo.utctime()
            }
            if not self["donations"]:
                self["donations"] = []
            self["donations"].append(log)
            self.save()
            return True
        return False

    def log_purchase(self, coins, name, kind=None):
        if self.get("_id") and coins:
            log = {
                "name": name,
                "kind": kind,
                "on": crudmgo.utctime()
            }
            if not self.get("purchases"):
                self["purchases"] = []
            self["purchases"].append(log)
            self.save()
            return True
        return False