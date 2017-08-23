# -*- coding: utf-8 -*-
__author__ = 'n2m'

from rest import crud
from dateutil.tz import tzlocal


def model_mission(db):
    class Mission(db.Model):
        __tablename__ = "missions"
        __crud_searchfield__ = ("name",)

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(255), default="")
        hits = db.Column(db.Integer)
        maxhits = db.Column(db.Integer)
        points = db.Column(db.Integer)
        status = db.Column(db.String(45))
        createdate = db.Column(db.TIMESTAMP)
        users = db.relationship("UsersMission")

        @property
        def totalhits(self):
            umission = crud.get_relationship_model(self.__class__, "users")
            return int(umission.query.filter_by(missionid=self.id).
                       with_entities(db.func.sum(umission.hits)).scalar())

        def __init__(self, **kargs):
            self.name = kargs.get("name")
            self.hits = kargs.get("hits")
            self.maxhits = kargs.get("maxhits")
            self.points = kargs.get("points")
            self.status = kargs.get("status")

        def json(self):
            createdate = self.createdate.replace(tzinfo=tzlocal()) if not self.createdate.tzinfo else self.createdate
            return {"id": self.id,
                    "name": self.name,
                    "hits": self.hits,
                    "maxhits": self.maxhits,
                    "points": self.points,
                    "createdate": createdate.isoformat(),
                    "totalhits": self.totalhits}

    return Mission


def model_upload(db):
    class Upload(db.Model):
        __tablename__ = "uploads"

        id = db.Column(db.Integer, primary_key=True)
        userid = db.Column(db.Integer, db.ForeignKey("users.id"))
        missionid = db.Column(db.Integer, db.ForeignKey("users_mission.id"))
        file = db.Column(db.String(250), default="")
        agree = db.Column(db.String(10), default="")
        inputtext = db.Column(db.String(255), default="")
        createdate = db.Column(db.TIMESTAMP)

    return Upload


def model_users_mission(db):
    class UsersMission(db.Model):
        __tablename__ = "users_mission"
        __crud_searchfield__ = ("user.name",)
        __json_foreign__ = ("user:name,firstname,lastname",)

        id = db.Column(db.Integer, primary_key=True)
        userid = db.Column(db.Integer, db.ForeignKey("users.id"))
        user = db.relationship("User", lazy="joined")
        hits = db.Column(db.Integer)
        points = db.Column(db.Integer)
        firstdate = db.Column(db.DateTime)
        lastdate = db.Column(db.DateTime)
        missionid = db.Column(db.Integer, db.ForeignKey("missions.id"))
        uploads = db.relationship("Upload")

        @property
        def uploadscount(self):
            uploads = crud.get_relationship_model(self.__class__, "uploads")
            return uploads.query.filter_by(missionid=self.missionid, userid=self.userid).count()

        def __init__(self, **kargs):
            self.userid = kargs.get("userid")
            self.hits = kargs.get("hits")
            self.points = kargs.get("points")
            self.firstdate = kargs.get("firstdate")
            self.lastdate = kargs.get("lastdate")
            self.missionid = kargs.get("missionid")

        def json(self):
            firstdate = None
            lastdate = None
            if self.firstdate is not None:
                firstdate = self.firstdate.replace(tzinfo=tzlocal())\
                    if not self.firstdate.tzinfo else self.firstdate
                firstdate = firstdate.isoformat()
            if self.lastdate is not None:
                lastdate = self.lastdate.replace(tzinfo=tzlocal())\
                    if self.lastdate and not self.lastdate.tzinfo else self.lastdate
                lastdate = lastdate.isoformat()
            return {"id": self.id,
                    "userid": self.userid,
                    "hits": self.hits,
                    "points": self.points,
                    "firstdate": firstdate,
                    "lastdate": lastdate,
                    "missionid": self.missionid,
                    "uploadscount": self.uploadscount,
                    "user": {"id": self.user.id,
                             "name": self.user.name,
                             "firstname": self.user.firstname,
                             "lastname": self.user.lastname}}

    return UsersMission