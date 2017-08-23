# -*- coding: utf-8 -*-
__author__ = 'n2m'


def model_whatsyourpower(db):
    class WhatsYourPower(db.Model):
        __tablename__ = "whatsyourpower"
        __json_foreign__ = ("user:name,firstname,lastname",)
        __crud_searchfield__ = ("description", "user.name")

        id = db.Column(db.Integer, primary_key=True)
        description = db.Column(db.String(3000), default="")
        image = db.Column(db.String(255), default="")
        youtube = db.Column(db.Text, default="")
        share = db.Column(db.String(45))
        userid = db.Column(db.Integer, db.ForeignKey("users.id"))
        user = db.relationship("User", lazy="joined")
        status = db.Column(db.String(45))
        createdate = db.Column(db.TIMESTAMP)

        def __init__(self, **kargs):
            self.description = kargs.get("description")
            self.image = kargs.get("image")
            self.youtube = kargs.get("youtube")
            self.share = kargs.get("share")
            self.userid = kargs.get("userid")
            self.status = kargs.get("status")

    return WhatsYourPower