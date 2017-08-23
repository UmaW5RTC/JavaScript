# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import current_app
from flask.ext.wtf import Form
from sqlalchemy.orm import validates
from wtforms import StringField, PasswordField, SelectField, validators
from mod_auth.model import UserMixin, UserMgoMixin
from user import encpass, decpass
from rest import crud, crudmgo
from werkzeug.security import safe_str_cmp
import datetime
import bcrypt
import hashlib


class AdminForm(Form):
    name = StringField("Name", [crud.put_optional, validators.DataRequired()])
    email = StringField("Email", [crud.put_optional, validators.DataRequired(), validators.Email()])
    password = PasswordField("Password", [crud.put_optional, validators.DataRequired(),
                                          validators.Length(min=6, max=55)])
    role = SelectField("Role", [validators.Optional(True)],
                       choices=[("Administrator", "Administrator"), ("Counselor", "Counselor")])


class Administrator(crudmgo.RootDocument, UserMgoMixin):
    __collection__ = "administrators"
    __json_omit__ = ("password",)
    __crud_searchfield__ = ("name", "email")
    __form__ = AdminForm
    __username_field__ = "email"

    structure = {
        "name": basestring,
        "email": basestring,
        "password": basestring,
        "created": datetime.datetime,
        "lastlogin": datetime.datetime,
        "status": bool,
        "role": basestring
    }
    indexes = [
        {"fields": "email",
         "unique": True},
        {"fields": ["status", "email"]}
    ]
    default_values = {"created": crudmgo.localtime, "lastlogin": crudmgo.localtime, "status": True,
                      "role": "Administrator"}

    @property
    def role(self):
        return (self.get("role") or "Administrator") if self.get("_id", None) else None

    def auth_loader_values(self):
        s256 = hashlib.sha256()
        d = {}
        if self.role == "Counselor":
            secret_key = current_app.config.get("SECRET_KEY", "")
            if secret_key is None:
                secret_key = ""
            secret = secret_key + datetime.datetime.now().strftime("%y%m%d") + str(self["_id"]).encode()
            s256.update(secret)
            d = {"token": s256.hexdigest()}
        return d

    @role.setter
    def role(self, value):
        self['role'] = value

    def __on_login__(self, _):
        self["lastlogin"] = datetime.datetime.now()
        self.save()

    def authenticate(self, pwd):
        pwd = pwd.encode("utf-8") if isinstance(pwd, unicode) else pwd
        password = self["password"].encode("utf-8") if isinstance(self["password"], unicode) else self["password"]
        return safe_str_cmp(bcrypt.hashpw(pwd, password), password)

    def update_raw(self, d):
        if "name" in d:
            self["name"] = d["name"]
        if "email" in d:
            self["email"] = self.normalize_username(d["email"])
        if "password" in d:
            password = d["password"].encode("utf-8") if isinstance(d["password"], unicode) else d["password"]
            self["password"] = bcrypt.hashpw(password, bcrypt.gensalt())
        if "status" in d:
            self["status"] = d["status"] is True or str(d["status"]).lower() in ("1", "on", "true", "t", "active")
        if "role" in d:
            self["role"] = d["role"]


def model_administrator(db):
    class Administrator(db.Model, UserMixin):
        __tablename__ = "administrator"
        __json_omit__ = ("password",)
        __crud_searchfield__ = ("name", "email")
        __form__ = AdminForm
        __username_field__ = "email"

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(250))
        email = db.Column(db.String(250))
        _password = db.Column("password", db.String(250))
        createdate = db.Column(db.TIMESTAMP)
        lastlogindate = db.Column(db.DateTime, default=db.func.now())
        status = db.Column(db.String(45), default="active")

        @property
        def role(self):
            return "Administrator" if self.id else None

        @property
        def password(self):
            return decpass(self._password) if self._password else None

        @password.setter
        def password(self, pwd):
            self._password = encpass(pwd) if pwd else None

        def __init__(self, **kargs):
            self.name = kargs.get("name")
            self.email = kargs.get("email")
            self.password = kargs.get("password")
            self.lastlogindate = kargs.get("lastlogindate")
            self.status = kargs.get("status")

        @validates("email")
        def validate_email(self, _, value):
            if self.email != value and self.query.filter_by(email=value).count() > 0:
                raise ValueError({"name": "Email is already in use. Please choose another email."})
            return value

        def __on_login__(self, _):
            self.lastlogindate = datetime.datetime.now()
            db.session.commit()

    return Administrator