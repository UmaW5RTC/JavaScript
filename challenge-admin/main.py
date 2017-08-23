# app uses flask-restful and flask-sqlalchemy extensions
from flask import Flask, g, request
from flask_sslify import SSLify
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.babel import Babel
import jinja_config
from model import administrator, user, whatsyourpower, survey, mission, izquiz, izhero, file, izstory,\
                  ann, gallery, power, encyclopedia, card, dqmission, surveydq, messenger, membership,\
                  dqresult, lesson
from mod_user import admin_user
#from mod_power import admin_power
from mod_admin import admin_admin
from mod_survey import admin_presurvey, admin_postsurvey
from mod_mission import admin_mission
from mod_izquiz import admin_izquiz
from mod_izhero import admin_school, admin_teacher, admin_izhero, admin_country
from mod_squadstory import admin_squadstory
from mod_izann import admin_ann
from mod_izgallery import admin_gallery
from mod_stats import admin_stats, admin_stats_school
from mod_lessons import admin_powers, admin_missions, admin_competencies, admin_cwtopics, \
    admin_cwvalues, teacher_powers, teacher_competencies, teacher_cwtopics, teacher_cwvalues, \
    teacher_missions, admin_lessons
from mod_izsquad import admin_izsquad
from mod_inbox import admin_annce, admin_message
from mod_auth import Auth
from mod_izencyclopedia import admin_encyclopedia, admin_encycloarticle
from mod_izmember import admin_izmember, admin_iztemember
from mod_client import client, SUPPORTED_LANG
from mod_izdqreport import dqresult_rcode
from mod_izmission import admin_izmission
from flask.ext.mongokit import MongoKit
from flask.ext.mandrill import Mandrill


def nocache(response):
    if request.headers.get('Origin') and (request.headers['Origin'].endswith('izhero.net') or
                                          request.headers['Origin'].endswith('dqworld.net')):
        response.headers['Access-Control-Allow-Origin'] = request.headers['Origin']
    if request.headers.get('Access-Control-Request-Methods'):
        response.headers['Access-Control-Allow-Methods'] = request.headers.get('Access-Control-Request-Methods')
    if request.headers.get('Access-Control-Request-Headers'):
        response.headers['Access-Control-Allow-Headers'] = request.headers.get('Access-Control-Request-Headers')

    if hasattr(response, "mimetype") and response.mimetype in ("text/javascript", "application/json"):
        response.headers['Cache-Control'] = 'no-cache, no-store, max-age=0'
        response.headers['Pragma'] = 'no-cache'
    return response

# TO RUN: create file "cfg.py". insert lines below:
# SQLALCHEMY_DATABASE_URI = "mysql://username:password@server/izchallenge" # change sql user, password, and server info
# DEBUG = True # set to True/False to enable/disable flask debugging
app = Flask(__name__)
#sslify = SSLify(app)

babel = Babel(app, default_timezone="Asia/Singapore")

app.config.from_object('version')
app.config.from_object('cfg')
app.config["AUTH_COOKIE_NAME"] = "auth_admin_session_id"
app.config["db"] = db = SQLAlchemy(app)
app.config["mgodb"] = mgodb = MongoKit(app)
app.config["model.administrator"] = administrator.model_administrator(db)
app.config["model.user"] = user.model_user(db)
app.config["model.whatsyourpower"] = whatsyourpower.model_whatsyourpower(db)
app.config["model.survey"] = survey.model_survey(db)
app.config["model.surveyanswer"] = survey.model_survey_answer(db)
app.config["model.mission"] = mission.model_mission(db)
app.config["model.upload"] = mission.model_upload(db)
app.config["model.users_mission"] = mission.model_users_mission(db)
app.config["model.izquiz"] = izquiz.model_izquiz(db)
mgodb.register(izhero.Country)
mgodb.register(izhero.Teacher)
mgodb.register(izhero.IZHero)
mgodb.register(administrator.Administrator)
mgodb.register(file.File)
mgodb.register(file.JustLoveEmailLog)
mgodb.register(izstory.IZStory)
mgodb.register(ann.Announcement)
mgodb.register(ann.Message)
mgodb.register(ann.Inbox)
mgodb.register(gallery.Gallery)
mgodb.register(power.Power)
mgodb.register(power.SELCompetency)
mgodb.register(power.CWTopic)
mgodb.register(power.CWValue)
mgodb.register(power.Mission)
mgodb.register(lesson.Lesson)
mgodb.register(encyclopedia.EncycloCategory)
mgodb.register(encyclopedia.EncycloArticle)
mgodb.register(card.Card)
mgodb.register(dqmission.DqUserMission)
mgodb.register(surveydq.SurveyDQ)
mgodb.register(surveydq.SurveyDQAnswer)
mgodb.register(messenger.Messenger)
mgodb.register(messenger.ChatLog)
mgodb.register(membership.Membership)
mgodb.register(membership.SchoolMembership)
mgodb.register(membership.DQReportAccess)
mgodb.register(dqresult.PreDQResult)
mgodb.register(dqresult.ScreentimeDQResult)
mgodb.register(dqresult.PrivacyDQResult)
mgodb.register(dqresult.CyberbullyingDQResult)
mgodb.register(dqresult.DigitalcitizensDQResult)
mgodb.register(dqresult.DigitalfootprintDQResult)
mgodb.register(dqresult.SecurityDQResult)
mgodb.register(dqresult.CriticalthinkingDQResult)
mgodb.register(dqresult.EmpathyDQResult)
mgodb.register(dqresult.RiskEnvPersonalDQResult)
mgodb.register(dqresult.DQX)
mgodb.register(dqresult.DQY)
# app.config["model.school"] = izhero.model_school(db)
# app.config["model.izhero"] = izhero.model_izhero(db)
#app.register_blueprint(admin_power, url_prefix="/powers")
app.register_blueprint(admin_user, url_prefix="/users")
app.register_blueprint(admin_admin, url_prefix="/admins")
app.register_blueprint(admin_presurvey, url_prefix="/presurveys")
app.register_blueprint(admin_postsurvey, url_prefix="/postsurveys")
app.register_blueprint(admin_mission, url_prefix="/missions")
app.register_blueprint(admin_izquiz, url_prefix="/izquizes")
app.register_blueprint(admin_country, url_prefix="/countries")
app.register_blueprint(admin_school, url_prefix="/schools")
app.register_blueprint(admin_teacher, url_prefix="/teachers")
app.register_blueprint(admin_izhero, url_prefix="/students")
app.register_blueprint(admin_squadstory, url_prefix="/stickers")
app.register_blueprint(admin_ann, url_prefix="/news")
app.register_blueprint(admin_gallery, url_prefix="/gallery")
app.register_blueprint(admin_stats, url_prefix="/stats")
app.register_blueprint(admin_stats_school, url_prefix="/stats/schools")
app.register_blueprint(admin_powers, url_prefix="/powers")
app.register_blueprint(admin_missions, url_prefix="/powers/missions")
app.register_blueprint(admin_competencies, url_prefix="/powers/competencies")
app.register_blueprint(admin_cwtopics, url_prefix="/powers/topics")
app.register_blueprint(admin_cwvalues, url_prefix="/powers/values")
app.register_blueprint(teacher_powers, url_prefix="/lessons/powers")
app.register_blueprint(teacher_missions, url_prefix="/lessons")
app.register_blueprint(teacher_competencies, url_prefix="/lessons/competencies")
app.register_blueprint(teacher_cwtopics, url_prefix="/lessons/topics")
app.register_blueprint(teacher_cwvalues, url_prefix="/lessons/values")
app.register_blueprint(admin_izsquad, url_prefix="/izsquads")
app.register_blueprint(admin_annce, url_prefix="/anns")
app.register_blueprint(admin_message, url_prefix="/messages")
app.register_blueprint(admin_encyclopedia, url_prefix="/encyclopedia")
app.register_blueprint(admin_encycloarticle, url_prefix="/encyclopedia/pages")
app.register_blueprint(admin_izmember, url_prefix="/members")
app.register_blueprint(admin_iztemember, url_prefix="/schoolmembers")
app.register_blueprint(dqresult_rcode, url_prefix="/dqresults/pretest")
app.register_blueprint(admin_lessons, url_prefix="/dqlessons")
app.register_blueprint(admin_izmission, url_prefix="/dqmissions")
app.register_blueprint(client, url_prefix="/lang:<lang>")
app.register_blueprint(client)
app.after_request(nocache)
jinja_config.configure(app)
app.mandrill = Mandrill(app)

# Auth(app, userdb=app.config["model.administrator"], bp_prefix="/acct")
Auth(app, is_mgo=True, userdb=["Administrator", "Teacher"], loader_name="user.js", loader_full=True, bp_prefix="/acct")


@babel.localeselector
def get_locale():
    return (hasattr(g, "lang") and g.lang) or request.accept_languages.best_match(SUPPORTED_LANG)

if __name__ == "__main__":
    raise Exception('Execute run.py instead')

