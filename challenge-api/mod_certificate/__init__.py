# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import current_app, request, render_template, url_for
from mod_auth import current_user
from mod_sendmail import sendmail
import os
import re

invalid_dir_chars = re.compile('[' + re.escape(r'\/:*?"<>|.') + ']')
lang_list = ("en", "ko", "es")

badge_name = {
    "en": {
        "screentimebadge": "Screen Time Management",
        "privacybadge": "Privacy Management",
        "cyberbullyingbadge": "Cyber Bullying Management",
        "digitalcitizensbadge": "Digital Citizen Identity",
        "digitalfootprintbadge": "Digital Footprints",
        "securitybadge": "Cyber Security Management",
        "criticalthinkingbadge": "Critical Thinking",
        "empathybadge": "Digital Empathy"
    },
    "ko": {
        "screentimebadge": u"디지털 이용 시간 조절 능력",
        "privacybadge": u"온라인 사생활 관리 능력",
        "cyberbullyingbadge": u"사이버 폭력 대처 능력",
        "digitalcitizensbadge": u"온라인 인격 형성 능력",
        "digitalfootprintbadge": u"디지털 발자국 관리 능력",
        "securitybadge": u"사이버 보안 능력",
        "criticalthinkingbadge": u"온라인 정보 선별 능력",
        "empathybadge": u"디지털 공감 능력"
    },
    "es": {
        "screentimebadge": u"Manejar el Tiempo en la Pantalla",
        "privacybadge": u"Manejar la Privacidad",
        "cyberbullyingbadge": u"Lidiar con el Ciberacoso Cyber-bullying",
        "digitalcitizensbadge": u"Identidad del Ciudadano Digital",
        "digitalfootprintbadge": u"Manejar la Huella Digital",
        "securitybadge": u"Manejar la Ciber-Seguridad",
        "criticalthinkingbadge": u"Pensamiento Crítico",
        "empathybadge": u"Empatía Digital"
    }
}


class Certificate(object):
    ufolder = "uploads"
    ufolder_certificate = "uploads/certificate"
    __certificate_foldername__ = "certificate"

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.ufolder = app.upload_app.ufolder
        self.ufolder_certificate = os.path.join(app.upload_app.ufolder, self.__certificate_foldername__)

        if not os.path.isdir(self.ufolder_certificate):
            os.mkdir(self.ufolder_certificate)

        app.certificate_app = self
        app.jinja_loader.searchpath.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"))
        app.upload_app.add_upload("certificate", upload_certificate)


def upload_certificate():
    data = request.json or (request.form and request.form.to_dict())
    if not data:
        return {"success": False}
    certname = data.get("certificate")
    lang = data.get("lang", "en")

    if certname not in ("screentimebadge", "privacybadge", "cyberbullyingbadge",
                        "digitalcitizensbadge", "digitalfootprintbadge", "securitybadge",
                        "criticalthinkingbadge", "empathybadge", "final"):
        return {"success": False}

    prog = current_user.get("dq_progress") or {}
    pname = certname
    notifname = "cert_notified"
    if certname == "final":
        pname = "empathybadge"
        notifname = "cert_final_notified"

    if pname not in prog or not isinstance(prog[pname], dict) or prog[pname].get(notifname):
        return {"success": False}

    meta = {"type": "certificate",
            "name": certname}

    user = current_user._get_current_object()
    username = user.get_username()
    part_username = username[0:2] if len(username) >= 2 else username
    part_username = invalid_dir_chars.sub("z", part_username)
    user_folder = os.path.join(current_app.certificate_app.__certificate_foldername__,
                               part_username)
    fullpath = os.path.join(current_app.certificate_app.ufolder, user_folder)

    if not os.path.isdir(fullpath):
        os.mkdir(fullpath)
    saved = current_app.upload_app.save_file(data, folder=user_folder, meta=meta, is_datauri=True)

    if saved:
        user.collection.update({"_id": current_user["_id"]},
                               {"$set": {"dq_progress.%s.%s" % (pname, notifname): True}})
        prog[pname][notifname] = True

        if user.get("guardiansack") and isinstance(user.get("parent"), dict) and user["parent"].get("email"):
            if current_app.config.get("BUCKET"):
                filepath = "https://storage.googleapis.com/%s/%s/%s" % (current_app.config["BUCKET"],
                                                                        saved["folder"],
                                                                        saved["filename"])
            else:
                filepath = url_for("download", filename=saved["folder"] + "/" + saved["filename"], _external=True)

            cert_send_mail(lang, user["parent"]["email"], certname, filepath)

        return {"success": True, "_id": str(saved["_id"])}

    return {"success": False}


def cert_send_mail(lang, email, certname, certificate):
    tmpl = "/" + certname + ".html"
    lang = lang if lang in lang_list else "en"
    tmpl = (lang + tmpl) if lang in lang_list else "en" + tmpl

    if certname == "final":
        title = {
            "ko": u"[DQ 월드] 기쁜 소식! 귀 자녀의 DQ™ 가 향상되었습니다",
            "en": u"[DQ World] Great news! Your child has raised their DQ™",
            "es": u"[DQ World] ¡Buenas noticias! El DQ™ de su hijo(a) ha aumentado"
        }
        subject = (title.get(lang) or title["en"])
    else:
        title = {
            "ko": u"[DQ 월드] 기쁜 소식! 귀 자녀의 %s이 개발되었습니다.",
            "en": "[DQ World] Great news! Your child has developed %s Skills",
            "es": u"[DQ World] ¡Buenas noticias! Su hijo(a) ha desarrollado Habilidades de %s."
        }
        subject = (title.get(lang) or title["en"]) % badge_name[lang][certname]

    sendmail(email,
             subject,
             render_template(tmpl,
                             dq_score=get_dq_score() if certname == "final" else 0,
                             certificate=certificate,
                             url_root=os.path.dirname(request.url_root[:-1]) + '/'))


def get_dq_score():
    usr = current_user._get_current_object()
    if not usr or not hasattr(usr, "collection"):
        return 0

    db = usr.collection.database
    score = 0

    res = db["ScreentimeDQResult"].get_dqresult(usr, True)
    if res:
        try:
            score += int(res.get("sc_mgmt_score", 0))
        except (ValueError, TypeError):
            pass

    res = db["PrivacyDQResult"].get_dqresult(usr, True)
    if res:
        try:
            score += int(res.get("pri_pi_mgmt_score", 0))
        except (ValueError, TypeError):
            pass

    res = db["CyberbullyingDQResult"].get_dqresult(usr, True)
    if res:
        try:
            score += int(res.get("cb_score", 0))
        except (ValueError, TypeError):
            pass

    res = db["DigitalcitizensDQResult"].get_dqresult(usr, True)
    if res:
        try:
            score += int(res.get("dc_identity_score", 0))
        except (ValueError, TypeError):
            pass

    res = db["DigitalfootprintDQResult"].get_dqresult(usr, True)
    if res:
        try:
            score += int(res.get("df_mgmt_score", 0))
        except (ValueError, TypeError):
            pass

    res = db["SecurityDQResult"].get_dqresult(usr, True)
    if res:
        try:
            score += int(res.get("sec_score", 0))
        except (ValueError, TypeError):
            pass

    res = db["CriticalthinkingDQResult"].get_dqresult(usr, True)
    if res:
        try:
            score += int(res.get("ct_score", 0))
        except (ValueError, TypeError):
            pass

    res = db["EmpathyDQResult"].get_dqresult(usr, True)
    if res:
        try:
            score += int(res.get("emp_de_score", 0))
        except (ValueError, TypeError):
            pass

    return score / 8.0
