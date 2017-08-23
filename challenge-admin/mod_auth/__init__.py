# -*- coding: utf-8 -*-
import datetime

__author__ = 'n2m'

from flask import current_app, request
from werkzeug.local import LocalProxy
from .model import model_session, mgo_model_session
from bson.objectid import ObjectId
from dateutil import tz
import os
import flask
import hashlib
import datetime


current_session = LocalProxy(lambda: _get_session())
current_user = LocalProxy(lambda: _get_user())
current_userid = LocalProxy(lambda: _get_userid())

COOKIE_NAME = "auth_session_id"
SESSION_GLOBAL_NAME = "auth_session"
SESSION_GLOBAL_NAME_ALT = SESSION_GLOBAL_NAME + "_ALT"

LOGIN_INCORRECT_USERPWD_ERROR = (101, "Incorrect username and/or password.")
LOGIN_UNACTIVATED_ERROR = (201, "User account is not activated.")


class Auth(object):
    userdb = None
    subuserdb = None
    sessdb = None
    loader = False
    loader_prefix = ""
    loader_name = "loader.js"
    loader_full = False
    bp = False
    bp_prefix = ""
    cookie = None
    cookie_secure = False
    cookie_domain = None
    cookie_path = "/"
    cookie_httponly = True
    db = None
    mgo = None
    is_mgo = False
    mgo_username_lower = True

    def __init__(self, app=None, userdb=None, is_mgo=False, loader=True, loader_full=False, loader_prefix="",
                 loader_name="loader.js", bp=True, bp_prefix=""):
        self.set_config(userdb, is_mgo, loader, loader_full, loader_prefix, loader_name, bp, bp_prefix)
        if app is not None:
            self.init_app(app)

    def init_app(self, app, userdb=None, is_mgo=None, loader=None, loader_full=None, loader_prefix=None,
                 loader_name=None, bp=None, bp_prefix=None):
        app.auth = self
        self.set_config(userdb, is_mgo, loader, loader_full, loader_prefix, loader_name, bp, bp_prefix)

        self.cookie = app.config.get("AUTH_COOKIE_NAME", COOKIE_NAME)
        self.cookie_secure = app.config.get("AUTH_COOKIE_SECURE", False)
        self.cookie_domain = app.config.get("AUTH_COOKIE_DOMAIN", None)
        self.cookie_path = app.config.get("AUTH_COOKIE_PATH", "/")
        self.cookie_httponly = app.config.get("AUTH_COOKIE_HTTPONLY", True)
        self.mgo_username_lower = app.config.get("AUTH_MGO_USERNAME_LOWER", True)
        self.mgo = app.config.get("mgodb")
        self.db = app.config.get("db")
        if not self.mgo:
            app.config["model.auth_session"] = self.sessdb = model_session(self.db, self.userdb)
            app.before_first_request(self.session_cleanup)
        else:
            self.mgo.register(mgo_model_session(self.mgo if self.is_mgo else self.db, self.userdb, self.is_mgo))
        app.after_request(self._update_cookie)

        if self.loader:
            from .loader import Loader
            app.add_url_rule(self.loader_prefix + "/" + self.loader_name, view_func=Loader.as_view("auth_loader"))
        if self.bp:
            from .blueprint import auth_bp
            app.register_blueprint(auth_bp, url_prefix=self.bp_prefix)

    def session_cleanup(self):
        self.sessdb.query.filter(self.sessdb.expiry < datetime.datetime.now()).delete()
        self.db.session.commit()

    def set_config(self, userdb, is_mgo, loader, loader_full, loader_prefix, loader_name, bp, bp_prefix):
        if userdb is not None:
            if isinstance(userdb, (list, tuple)):
                self.userdb = userdb[0]
                self.subuserdb = userdb[1:]
            else:
                self.userdb = userdb
        if loader_prefix is not None:
            self.loader_prefix = loader_prefix[-1:] if loader_prefix and loader_prefix[-1:] == "/" else loader_prefix
        if bp_prefix is not None:
            self.bp_prefix = bp_prefix[-1:] if bp_prefix and bp_prefix[-1:] == "/" else bp_prefix
        if loader is not None:
            self.loader = loader
        if loader_full is not None:
            self.loader_full = loader_full
        if loader_name is not None:
            if loader_name[0] == "/":
                loader_name = loader_name[1:]
            self.loader_name = loader_name
        if is_mgo is not None:
            self.is_mgo = is_mgo
        if bp is not None:
            self.bp = bp

    @property
    def session(self):
        sess = flask.g.get(SESSION_GLOBAL_NAME, None)

        if sess is None:
            sessid = request.cookies.get(self.cookie, None)
            if sessid is not None:
                hashedid = hashlib.sha256(sessid).hexdigest()
                sess = self.mgo["Session"].find_one({"_id": hashedid}) if self.mgo else self.sessdb.query.get(hashedid)

            if sess is not None:
                # mongodb has a expiry index that auto deletes session doc
                if not self.mgo and sess.expiry < datetime.datetime.now():
                    self.db.session.delete(sess)
                    self.db.session.commit()
                else:
                    if self.is_mgo and sess.get("userdb"):
                        udb = sess["userdb"]
                        db_avail = [self.userdb]
                        if self.subuserdb:
                            db_avail = db_avail + self.subuserdb
                        if udb not in db_avail:
                            sess = None

                    if sess is not None:
                        sess.__cookie_sessid__ = sessid
                        setattr(flask.g, SESSION_GLOBAL_NAME, sess)
                        if sess.user and not sess.user.is_anonymous:
                            sess.user.__on_session_hit__(sess)

            if sess is None:
                sess = self.new_session(delete_old=False)

        return sess

    @property
    def user(self):
        sess = self.session
        if not sess.is_anonymous and sess.user:
            return sess.user
        return self.mgo[self.userdb].anonymous() if self.is_mgo else self.userdb.anonymous()

    @property
    def userid(self):
        sess = self.session
        if not sess.is_anonymous:
            return sess.userid
        return 0

    def login(self, username, password, remember=False):
        if self.is_mgo:
            if self.mgo_username_lower and username:
                if self.mgo[self.userdb] and callable(getattr(self.mgo[self.userdb], "normalize_username", None)):
                    username = self.mgo[self.userdb].normalize_username(username)
                else:
                    username = username.lower()
            u = self.mgo[self.userdb].find_one({self.mgo[self.userdb].__username_field__: username})
            if u is None and self.subuserdb:
                for udb in self.subuserdb:
                    u = self.mgo[udb].find_one({self.mgo[udb].__username_field__: username})
                    if u is not None:
                        break
        else:
            u = self.userdb.query.filter_by(**{self.userdb.__username_field__: username}).first()

        if u is not None and u.authenticate(password):
            if not u.is_active:
                return False, LOGIN_UNACTIVATED_ERROR

            if (self.is_mgo and str(self.userid) != str(u["_id"])) or\
                    (not self.is_mgo and str(self.userid) != str(u.id)):
                sess = self.new_session(user=u, remember=remember)
                u.__on_login__(sess)
            elif self.is_mgo:
                if remember:
                    self.persist_session(self.session)
                else:
                    self.depersist_session(self.session)
            return True, None
        return False, LOGIN_INCORRECT_USERPWD_ERROR

    def login_userid(self, userid):
        if self.is_mgo:
            u = self.mgo[self.userdb].find_one({"_id": ObjectId(userid)})
            if u is None and self.subuserdb:
                for udb in self.subuserdb:
                    u = self.mgo[udb].find_one({"_id": ObjectId(userid)})
                    if u is not None:
                        break
        else:
            u = self.userdb.query.get(userid)

        return self.login_user(u)

    def login_user(self, u):
        if u is not None and not u.is_active:
            return False, LOGIN_UNACTIVATED_ERROR
        elif u is not None:
            if (self.is_mgo and str(self.userid) != str(u["_id"])) or\
                    (not self.is_mgo and str(self.userid) != str(u.id)):
                sess = self.new_session(user=u)
                u.__on_login__(sess)
            return True, None
        return False, LOGIN_INCORRECT_USERPWD_ERROR

    def alt_login_user(self, u, cookie_cfg):
        sessid = gen_session_id()

        if self.mgo:
            sess = self.mgo["Session"]()
            sess.__is_new__ = True
            sess["_id"] = hashlib.sha256(sessid).hexdigest()
        else:
            sess = self.sessdb(hashlib.sha256(sessid).hexdigest())

        sess.user = u
        if not self.mgo:
            sess.userid = u.id
        sess.__cookie_sessid__ = sessid
        sess.__cookie_cfg__ = cookie_cfg
        setattr(flask.g, SESSION_GLOBAL_NAME_ALT, sess)

        return True, None

    def logout(self):
        sess = self.session
        if sess is not None and sess.userid and sess.user:
            sess.user.__on_logout__()
        self.new_session()

    def new_session(self, user=None, delete_old=True, remember=False):
        oldsess = flask.g.get(SESSION_GLOBAL_NAME, None)
        if delete_old and oldsess is not None and not oldsess.__is_new__:
            if self.mgo:
                oldsess.delete()
            else:
                self.db.session.delete(oldsess)
                self.db.session.commit()

        sessid = gen_session_id()

        if self.mgo:
            sess = self.mgo["Session"]()
            sess.__is_new__ = True
            sess["_id"] = hashlib.sha256(sessid).hexdigest()
        else:
            sess = self.sessdb(hashlib.sha256(sessid).hexdigest())

        if user is not None:
            sess.user = user
            if not self.mgo:
                sess.userid = user.id

        if remember and self.is_mgo:
            self.persist_session(sess)
        sess.__cookie_sessid__ = sessid
        setattr(flask.g, SESSION_GLOBAL_NAME, sess)

        return sess

    @staticmethod
    def persist_session(sess):
        if not sess.get("data"):
            sess["data"] = {}
        sess["data"]["login_persist"] = True
        sess["expiry"] = datetime.datetime.now(tz=tz.tzlocal()) + datetime.timedelta(days=365)

    @staticmethod
    def depersist_session(sess):
        if not sess.get("data"):
            return
        sess["data"].pop("login_persist", None)
        sess["expiry"] = sess.default_values["expiry"]()

    def _update_cookie(self, response):
        def send_sess(sess):
            sess.save()
            if isinstance(sess.__cookie_cfg__, dict):
                cookie = sess.__cookie_cfg__.get("AUTH_COOKIE_NAME", self.cookie)
                domain = sess.__cookie_cfg__.get("AUTH_COOKIE_DOMAIN", self.cookie_domain)
                path = sess.__cookie_cfg__.get("AUTH_COOKIE_PATH", self.cookie_path)
                secure = sess.__cookie_cfg__.get("AUTH_COOKIE_PATH", self.cookie_secure)
                httponly = sess.__cookie_cfg__.get("AUTH_COOKIE_HTTPONLY", self.cookie_httponly)
            else:
                cookie = self.cookie
                domain = self.cookie_domain
                path = self.cookie_path
                secure = self.cookie_secure
                httponly = self.cookie_httponly

            remember = sess.get("data") and sess["data"].get("login_persist")
            if request.cookies.get(cookie, "") != sess.__cookie_sessid__ or\
                    (remember and sess["expiry"] < datetime.datetime.now(tz=tz.tzlocal())+datetime.timedelta(days=182)):
                d = {
                    "value": sess.__cookie_sessid__,
                    "domain": domain,
                    "path": path,
                    "secure": secure,
                    "httponly": httponly}
                if remember:
                    d["expires"] = sess["expiry"]
                    d["max_age"] = 60*60*24*365
                response.set_cookie(cookie, **d)

        send_sess(self.session)
        if flask.g.get(SESSION_GLOBAL_NAME_ALT, False):
            send_sess(flask.g.get(SESSION_GLOBAL_NAME_ALT))

        return response


def gen_session_id():
    return os.urandom(32).encode("hex")


def _get_session():
    return current_app.auth.session


def _get_user():
    return current_app.auth.user


def _get_userid():
    return current_app.auth.userid