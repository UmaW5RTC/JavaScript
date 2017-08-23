# -*- coding: utf-8 -*-
__author__ = 'n2m'

from rest import crudmgo
from flask.ext.wtf import Form
from wtforms import StringField, validators
import datetime


class MailForm(Form):
    email = StringField("Email", [validators.DataRequired(), validators.Email()])


class MailSubscription(crudmgo.RootDocument):
    __collection__ = "mailsubscriptions"
    __form__ = MailForm

    structure = {
        "email": basestring,
        "createdon": datetime.datetime
    }
    default_values = {"createdon": crudmgo.localtime}
