from flask import Flask, request
from urlparse import urlparse
from flask_sslify import SSLify
from flask.ext.mongokit import MongoKit
from flask.ext.mandrill import Mandrill
from model import izhero, shield, izstory, comic, gallery, ann, file, encyclopedia, card, dqmission, surveydq,\
                  messenger, membership, msubscribe, dqresult
from mod_auth import Auth
from mod_hero import izhero_izhero
from mod_stage import stage_progress
from mod_upload import Upload
from mod_drawing import Drawing, drawing_sticker
from mod_shield import shield_code
from mod_donate import donate_coin
from mod_story import izhero_story
from mod_coinlog import coinlog
from mod_comic import comic_shelf
from mod_gallery import gallery_sticker
from mod_ann import izhero_ann
from mod_game import game_shelf
from mod_encyclopedia import iz_encyclopedia, iz_encycloarticle
from mod_facebook import facebook
from mod_card import card_shelf
from mod_dqmission import dqmission_progress
from mod_dqsurvey import survey, answer
from mod_messenger import dq_messenger, dq_messengerlog
from mod_subscribe import izhero_sub
from mod_dqreport import survey_rcode
from mod_member import api_member
from mod_certificate import Certificate


def nocache(response):
    if request.headers.get('Origin') and (request.headers['Origin'].endswith('izhero.net') or
                                          request.headers['Origin'].endswith('dqworld.net')):
        response.headers['Access-Control-Allow-Origin'] = request.headers['Origin']
    if request.headers.get('Access-Control-Request-Methods'):
        response.headers['Access-Control-Allow-Methods'] = request.headers.get('Access-Control-Request-Methods')
    if request.headers.get('Access-Control-Request-Headers'):
        response.headers['Access-Control-Allow-Headers'] = request.headers.get('Access-Control-Request-Headers')
    response.headers['Cache-Control'] = 'no-cache, no-store, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

app = Flask(__name__)
#sslify = SSLify(app)

app.config.from_pyfile('version.py')
app.config.from_pyfile('cfg.py')
app.config["mgodb"] = mgodb = MongoKit(app)
mgodb.register(izhero.Country)
mgodb.register(izhero.Teacher)
mgodb.register(izhero.IZHero)
mgodb.register(izhero.CoinLog)
mgodb.register(shield.ShieldCode)
mgodb.register(izstory.IZStory)
mgodb.register(comic.CollectionShelf)
mgodb.register(comic.Comic)
mgodb.register(gallery.Gallery)
mgodb.register(gallery.GalleryLike)
mgodb.register(ann.Announcement)
mgodb.register(ann.Message)
mgodb.register(ann.Inbox)
mgodb.register(file.JustLoveEmailLog)
mgodb.register(encyclopedia.EncycloCategory)
mgodb.register(encyclopedia.EncycloArticle)
mgodb.register(card.Card)
mgodb.register(dqmission.DqUserMission)
mgodb.register(surveydq.SurveyDQ)
mgodb.register(surveydq.SurveyDQAnswer)
mgodb.register(surveydq.QuizResult)
mgodb.register(surveydq.PollAnswer)
mgodb.register(surveydq.PollResult)
mgodb.register(messenger.Messenger)
mgodb.register(messenger.ChatLog)
mgodb.register(membership.Membership)
mgodb.register(membership.SchoolMembership)
mgodb.register(membership.DQReportAccess)
mgodb.register(msubscribe.MailSubscription)
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
app.register_blueprint(izhero_izhero, url_prefix="/izhero")
app.register_blueprint(stage_progress, url_prefix="/stage")
app.register_blueprint(drawing_sticker, url_prefix="/drawing")
app.register_blueprint(shield_code, url_prefix="/shield")
app.register_blueprint(donate_coin, url_prefix="/donate")
app.register_blueprint(izhero_story, url_prefix="/izstory")
app.register_blueprint(coinlog, url_prefix="/coinlog")
app.register_blueprint(comic_shelf, url_prefix="/comic")
app.register_blueprint(gallery_sticker, url_prefix="/gallery")
app.register_blueprint(izhero_ann, url_prefix="/news")
app.register_blueprint(game_shelf, url_prefix="/games")
app.register_blueprint(iz_encyclopedia, url_prefix="/encyclopedia")
app.register_blueprint(iz_encycloarticle, url_prefix="/encyclopedia/pages")
app.register_blueprint(facebook, url_prefix="/share")
app.register_blueprint(card_shelf, url_prefix="/cards")
app.register_blueprint(dqmission_progress, url_prefix="/dqmissions")
app.register_blueprint(survey, url_prefix="/dqsurveys/item")
app.register_blueprint(answer, url_prefix="/dqsurveys/answer")
app.register_blueprint(dq_messenger, url_prefix="/messengers")
app.register_blueprint(dq_messengerlog, url_prefix="/messages")
app.register_blueprint(izhero_sub, url_prefix="/subscribe")
app.register_blueprint(survey_rcode, url_prefix="/dqresult")
app.register_blueprint(api_member, url_prefix="/memberships")
app.after_request(nocache)
Auth(app, is_mgo=True, userdb="IZHero", loader_name="user.js", loader_full=True, bp_prefix="/acct")
Upload(app, public_folders=["stickers", "comics", "encyclopedia", "lessons", "resources", "certificate"])
Drawing(app)
Certificate(app)
app.mandrill = Mandrill(app)

if __name__ == "__main__":
    raise Exception('Execute run.py instead')

