# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask.ext.wtf import Form
from sqlalchemy.orm import validates
from wtforms import StringField, PasswordField, RadioField, SelectField, IntegerField, validators
from rest import crud
import string
import random
import os

with open(os.path.dirname(__file__) + "/countries.txt", "r") as f:
    countries = f.readlines()


class UserForm(Form):
    name = StringField("Username", [crud.put_optional, validators.DataRequired()])
    guardiansemail = StringField("Guardian's Email", [crud.put_optional, validators.DataRequired(), validators.Email()])
    type = RadioField("Account Type", [crud.put_optional],
                      choices=[("Individual", "Individual"), ("Class/Group", "Class/Group")])
    firstname = StringField("First Name", [crud.put_optional, validators.DataRequired()])
    lastname = StringField("Last Name", [crud.put_optional, validators.DataRequired()])
    schoolname = StringField("School Code")
    classname = StringField("Class Name")
    password = PasswordField("Password", [crud.put_optional, validators.DataRequired(),
                                          validators.Length(min=8, max=83)])
    country = SelectField("Country", [crud.put_optional], choices=((cty, cty) for cty in countries))
    points = IntegerField("Points")
    status = RadioField("Status", [validators.Optional(False)],
                        choices=[("active", "Active"), ("inactive", "Inactive")])
    guardiansack = RadioField("Guardian's Acknowledgement", [validators.Optional(False)],
                              choices=[(1, "Active"), (0, "Inactive")])

    def validate_name(self, field):
        if " " in field.data or "\t" in field.data or "\r" in field.data or "\n" in field.data:
            raise validators.ValidationError("Username cannot contain spaces")


def model_user(db):
    class User(db.Model):
        __tablename__ = "users"
        __json_omit__ = ("password", "activationcode")
        __crud_searchfield__ = ("name", "firstname", "lastname", "guardiansemail")
        __form__ = UserForm

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(250))
        email = db.Column(db.String(250), default="")
        type = db.Column(db.String(250), default="Individual")
        guardiansemail = db.Column(db.String(250))
        firstname = db.Column(db.String(250))
        lastname = db.Column(db.String(250))
        schoolname = db.Column(db.String(250), default="")
        classname = db.Column(db.String(250), default="")
        _password = db.Column("password", db.String(250))
        activationcode = db.Column(db.String(250), default=generate_code)
        createdate = db.Column(db.TIMESTAMP)
        lastlogindate = db.Column(db.DateTime, default=db.func.now())
        status = db.Column(db.String(45), default="active")
        points = db.Column(db.Integer, default=0)
        country = db.Column(db.String(250))
        boolee = db.Column(db.Integer, default=0)
        raz = db.Column(db.Integer, default=0)
        guardiansack = db.Column(db.Integer, default=0)

        @property
        def password(self):
            return decpass(self._password) if self._password else None

        @password.setter
        def password(self, pwd):
            self._password = encpass(pwd) if pwd else None

        def __init__(self, **kargs):
            self.name = kargs.get("name")
            self.email = kargs.get("email")
            self.type = kargs.get("type")
            self.guardiansemail = kargs.get("guardiansemail")
            self.firstname = kargs.get("firstname")
            self.lastname = kargs.get("lastname")
            self.schoolname = kargs.get("schoolname")
            self.classname = kargs.get("classname")
            self.password = kargs.get("password")
            self.activationcode = kargs.get("activationcode")
            self.status = kargs.get("status")
            self.points = kargs.get("points")
            self.country = kargs.get("country")
            self.boolee = kargs.get("boolee")
            self.raz = kargs.get("raz")
            self.guardiansack = kargs.get("guardiansack")
            self.lastlogindate = kargs.get("lastlogindate")

        @validates("name")
        def validate_name(self, _, value):
            if self.name != value and self.query.filter_by(name=value).count() > 0:
                raise ValueError({"name": "Username is already in use. Please choose another username."})
            return value

    return User


def generate_code():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in xrange(6))


def encpass(pwd):
    epass = ""
    for c in pwd:
        num = ord(c) * 3
        if num < 10:
            num = "0" + str(num)
        elif num < 100:
            num = "0" + str(num)

        epass += str(num)
    return epass


def decpass(pwd):
    dpass = ""
    for x in xrange(len(pwd)/3):
        offset = x * 3
        c = int(pwd[offset:offset+3])
        dpass += chr(c/3)
    return dpass