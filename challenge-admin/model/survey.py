# -*- coding: utf-8 -*-
__author__ = 'n2m'


def model_survey(db):
    class Survey(db.Model):
        __tablename__ = "users_survey"
        __crud_searchfield__ = ("user.name",)
        __json_foreign__ = ("user:name,firstname,lastname",)
        __json_single_foreign__ = ("answers",)

        id = db.Column(db.Integer, primary_key=True)
        userid = db.Column(db.Integer, db.ForeignKey("users.id"))
        user = db.relationship("User", lazy="joined")
        surveyid = db.Column(db.Integer)
        compldate = db.Column(db.DateTime)
        status = db.Column(db.Integer, default=0)
        answers = db.relationship("SurveyAnswer")

        def __init__(self, **kargs):
            self.surveyid = kargs.get("surveyid")
            self.status = kargs.get("status")
            self.compldate = kargs.get("compldate")
            self.userid = kargs.get("userid")

    return Survey


def model_survey_answer(db):
    class SurveyAnswer(db.Model):
        __tablename__ = "users_survey_answer"

        id = db.Column(db.Integer, primary_key=True)
        usurveyid = db.Column(db.Integer, db.ForeignKey("users_survey.id"))
        qns = db.Column(db.Integer, default=1)
        ansnum = db.Column(db.Integer)
        anstext = db.Column(db.Text)

        def __init__(self, **kargs):
            self.usurveyid = kargs.get("usurveyid")
            self.qns = kargs.get("qns")
            self.ansnum = kargs.get("ansnum")
            self.anstext = kargs.get("anstext")

    return SurveyAnswer