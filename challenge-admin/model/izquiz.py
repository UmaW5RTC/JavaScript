# -*- coding: utf-8 -*-
__author__ = 'n2m'


def model_izquiz(db):
    class IZQuiz(db.Model):
        __tablename__ = "users_izquiz_champ"
        __crud_searchfield__ = ("champion", "user.name",)
        __json_foreign__ = ("user:name,firstname,lastname",)

        id = db.Column(db.Integer, primary_key=True)
        champion = db.Column(db.String(255), default="")
        userid = db.Column(db.Integer, db.ForeignKey("users.id"))
        user = db.relationship("User", lazy="joined")
        dtime = db.Column(db.DateTime, default=db.func.now())

        def __init__(self, **kargs):
            self.champion = kargs.get("champion")
            self.userid = kargs.get("userid")

    return IZQuiz