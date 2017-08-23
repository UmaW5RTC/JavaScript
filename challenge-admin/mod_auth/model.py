# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import request
from werkzeug.security import safe_str_cmp
from bson.objectid import ObjectId
from rest import crud, crudmgo
from dateutil.tz import tzlocal
import cPickle
import datetime
import random
import string
import unicodedata

SESSION_TIMEOUT = 21600


def generate_code(i=6):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in xrange(i))


class UserMixin(object):
    __name_field__ = "name"
    __username_field__ = "username"
    __password_field__ = "password"
    __status_field__ = "status"
    __role_field__ = "role"

    @property
    def is_active(self):
        if self.is_anonymous:
            return True

        if hasattr(self, self.__status_field__):
            active = getattr(self, self.__status_field__)
        else:
            active = True

        return active if isinstance(active, bool) else str(active).lower() in ("active", "on", "1", "true", "t")

    @property
    def is_anonymous(self):
        return not self.id

    def authenticate(self, pwd):
        if not hasattr(self, self.__password_field__):
            raise NotImplementedError("Authentication is not implemented")
        return not self.is_anonymous and safe_str_cmp(pwd, getattr(self, self.__password_field__))

    def get_role(self):
        if self.is_anonymous:
            return None

        if hasattr(self, self.__role_field__):
            return getattr(self, self.__role_field__)
        return None

    def has_role(self, role):
        r = self.get_role()
        if r:
            r = r.lower()

            if isinstance(role, (tuple, list)):
                for x in role:
                    if x.lower() == r:
                        return True
            else:
                return role.lower() == r

        return False

    def get_username(self):
        if self.is_anonymous:
            return ""
        if hasattr(self, self.__username_field__):
            return getattr(self, self.__username_field__) or ""

        raise NotImplementedError("Username not found.")

    def get_name(self):
        if self.is_anonymous:
            return "Anonymous"
        if hasattr(self, self.__name_field__):
            return getattr(self, self.__name_field__) or ""

        raise NotImplementedError("Name not found.")

    @classmethod
    def anonymous(cls):
        user = cls()
        user.id = 0
        user.name = "Anonymous"
        return user

    def __on_login__(self, sess):
        pass

    def __on_session_hit__(self, sess):
        pass

    def __on_logout__(self):
        pass


class UserMgoMixin(object):
    __name_field__ = "name"
    __username_field__ = "username"
    __password_field__ = "password"
    __status_field__ = "status"
    __role_field__ = "role"

    @property
    def id(self):
        return self["_id"]

    @property
    def is_active(self):
        if self.is_anonymous:
            return True

        active = self.get(self.__status_field__, True)
        return active if isinstance(active, bool) else str(active).lower() in ("active", "on", "1", "true", "t", "yes")

    @property
    def is_anonymous(self):
        return not self.get("_id", None)

    def authenticate(self, pwd):
        if not hasattr(self, self.__password_field__):
            raise NotImplementedError("Authentication is not implemented")
        return not self.is_anonymous and safe_str_cmp(pwd, self.get(self.__password_field__, ""))

    def get_role(self):
        if self.is_anonymous:
            return None

        return getattr(self, self.__role_field__) if hasattr(self, self.__role_field__)\
            else self.get(self.__role_field__, None)

    def has_role(self, role):
        r = self.get_role()
        if r:
            r = r.lower()

            if isinstance(role, (tuple, list)):
                for x in role:
                    if x.lower() == r:
                        return True
            else:
                return role.lower() == r

        return False

    def get_username(self):
        if self.is_anonymous:
            return ""
        return self.get(self.__username_field__) or ""

    def get_name(self):
        if self.is_anonymous:
            return "Anonymous"

        return self.get(self.__name_field__) or ""

    @classmethod
    def anonymous(cls):
        user = cls()
        user["_id"] = 0
        user["name"] = "Anonymous"
        return user

    @staticmethod
    def normalize_username(username):
        if isinstance(username, basestring):
            atindex = username.find("@")
            atrindex = username.rfind("@")
            dotindex = username.rfind(".")

            if atindex > 0 and atindex == atrindex and \
               dotindex > atindex + 1 and len(username) > dotindex + 2:

                username = username[:atindex + 1] + username[atindex + 1:].lower()
            else:
                if not isinstance(username, unicode):
                    username = unicode(username)
                username = unicodedata.normalize("NFKC", username)
                username = username.lower()
        return username

    def __on_login__(self, sess):
        pass

    def __on_session_hit__(self, sess):
        pass

    def __on_logout__(self):
        pass


def mgo_model_session(db, userdb, is_mgo=True):
    class Session(crudmgo.RootDocument):
        __collection__ = "auth_sessions"
        __cookie_sessid__ = None
        __cookie_cfg__ = None

        structure = {
            "_id": basestring,
            "userid": basestring,
            "expiry": datetime.datetime,
            "lastseen": datetime.datetime,
            "created": datetime.datetime,
            "ipaddr": basestring,
            "useragent": basestring,
            "userdb": basestring,
            "data": {}
        }
        indexes = [
            {"fields": "expiry",
             "expireAfterSeconds": 0}
        ]
        use_dot_notation = True
        default_values = {"created": crudmgo.localtime, "lastseen": crudmgo.localtime,
                          "expiry": lambda: crudmgo.localtime() + datetime.timedelta(seconds=SESSION_TIMEOUT),
                          "ipaddr": lambda: request.remote_addr, "useragent": lambda: request.user_agent.string}
        _user = None
        __is_new__ = False

        @property
        def user(self):
            if self._user is None and self.userid:
                self._user = db[self.get("userdb", userdb)].find_one({"_id": ObjectId(self["userid"])}) if is_mgo\
                    else userdb.query.get(self.userid)
            elif self._user:
                if (is_mgo and str(self._user["_id"]) != str(self["userid"])) or\
                        (not is_mgo and str(self._user.id) != str(self["userid"])):
                    self._user = None
            return self._user

        @user.setter
        def user(self, u):
            self._user = u
            if u:
                self["userid"] = str(u["_id"]) if is_mgo else u.id
                if is_mgo:
                    self["userdb"] = u.__class__.__name__

        @property
        def is_anonymous(self):
            return not self["userid"]

        def touch(self, now=None):
            if now is None:
                now = datetime.datetime.now(tzlocal())
            self["lastseen"] = now
            self["expiry"] = now + datetime.timedelta(seconds=SESSION_TIMEOUT)

        def save(self, *args, **kargs):
            self.touch()
            if self.__is_new__:
                self.__is_new__ = False
            super(Session, self).save(*args, **kargs)

    return Session


def model_session(db, userdb):
    """
    CREATE TABLE auth_session (
    id VARCHAR(64) NOT NULL PRIMARY KEY,
    userid INT(11),
    expiry DATETIME,
    lastseen DATETIME,
    created DATETIME,
    ipaddr VARCHAR(40) NOT NULL DEFAULT '',
    useragent VARCHAR(255) NOT NULL DEFAULT '',
    data TEXT,
    INDEX(userid)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
    """
    class Session(db.Model):
        __tablename__ = "auth_session"
        id = db.Column(db.String(64), primary_key=True)
        userid = db.Column(db.Integer, db.ForeignKey((userdb.__tablename__
                                                      if hasattr(userdb, "__tablename__") and userdb.__tablename__
                                                      else userdb.__name__.lower()) + ".id"))
        user = db.relationship(userdb.__name__, lazy="joined")
        expiry = db.Column(db.DateTime, default=lambda: datetime.datetime.now() + datetime.timedelta(seconds=SESSION_TIMEOUT))
        lastseen = db.Column(db.DateTime, default=db.func.now())
        created = db.Column(db.DateTime, default=db.func.now())
        ipaddr = db.Column(db.String(40), default=lambda: request.remote_addr)
        useragent = db.Column(db.String(255), default=lambda: request.user_agent.string)
        _data = db.Column("data", db.Text, default="")
        _datadict = None
        __cookie_sessid__ = None
        __data_changed__ = False
        __is_new__ = False
        __json_omit__ = ("id", "expiry")

        @property
        def data(self):
            if self._datadict is None or not isinstance(self._datadict, dict):
                self._datadict = cPickle.loads(str(self._data)) if self._data else {}
            return self._datadict

        @data.setter
        def data(self, value):
            if isinstance(value, dict):
                self._datadict = value
                self._data = cPickle.dumps(value)
                self.touch()
                self.__data_changed__ = False

        @property
        def is_anonymous(self):
            return not self.userid

        def __init__(self, sessid=None, **kargs):
            if sessid is not None:
                self.id = sessid
                self.__is_new__ = True
            self.userid = kargs.get("userid", None)
            self.expiry = kargs.get("expiry", None)
            self.ipaddr = kargs.get("ipaddr", None)
            self.useragent = kargs.get("useragent", None)

        def touch(self, now=None):
            if now is None:
                now = datetime.datetime.now()
            self.lastseen = now
            self.expiry = now + datetime.timedelta(seconds=SESSION_TIMEOUT)

        def save(self):
            now = datetime.datetime.now()

            if self.__data_changed__:
                self.data = self._datadict
            elif not self.lastseen or self.lastseen + datetime.timedelta(minutes=5) < now:
                self.touch(now)
            if self.__is_new__:
                self.__is_new__ = False
                db.session.add(self)

            db.session.commit()

        def __getitem__(self, key):
            return self.data[key]

        def __setitem__(self, key, value):
            self.set(key, value)

        def __delitem__(self, key):
            self.delete(key)

        def __len__(self):
            return len(self.data)

        def __contains__(self, item):
            return item in self.data

        def __iter__(self):
            return self.data.__iter__()

        def get(self, key, default=None):
            return self.data.get(key, default)

        def set(self, key, value):
            self.data[key] = value
            self.__data_changed__ = True

        def delete(self, key):
            self.data.pop(key, None)
            self.__data_changed__ = True

        def keys(self):
            return self.data.keys()

        def values(self):
            return self.data.values()

        def items(self):
            return self.data.items()

        def has_key(self, key):
            return self.data.has_key(key)

        def clear(self):
            self.data.clear()
            self.__data_changed__ = True

        def update(self, *args, **kwargs):
            self.data.update(*args, **kwargs)
            self.__data_changed__ = True

        def setdefault(self, key, default=None):
            self.__data_changed__ = True
            return self.data.setdefault(key, default)

        def pop(self, key, default=None):
            self.__data_changed__ = True
            return self.data.pop(key, default)

        def popitem(self):
            self.__data_changed__ = True
            return self.data.popitem()

        def iteritems(self):
            return self.data.iteritems()

        def iterkeys(self):
            return self.data.iterkeys()

        def itervalues(self):
            return self.data.itervalues()

    return Session