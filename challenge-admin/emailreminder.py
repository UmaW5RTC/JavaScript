# -*- coding: utf-8 -*-
__author__ = 'n2m'

from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta
from pymongo import MongoReplicaSetClient, MongoClient
import cfg
import sendgrid
import os
import sys

PACKAGE_DIR = os.path.join(
    os.path.dirname(__file__),
    "site-packages"
)
sys.path.insert(0, PACKAGE_DIR)

from dateutil import tz


__langs__ = ('en', 'ko', 'es')
__from__ = {
    'en': 'DQ World',
    'ko': u'DQ 월드',
    'es': 'DQ World'
}
__subjects__ = {
    'en/activation_1_day_left.html': u'[DQ World] Your child’s DQ™ World account will expire tomorrow',
    'en/activation_3_days_left.html': u'[DQ World] 3 days left to activate your child’s DQ™ World account and raise your child’s DQ (digital intelligence quotient)',
    'en/inactive_1_week.html': u'[DQ World] Raise your child’s DQ™ (digital intelligence quotient)',
    'ko/activation_1_day_left.html': u'[DQ 월드] 귀 자녀의 DQ™ World 계정은 내일 삭제 됩니다',
    'ko/activation_3_days_left.html': u'[DQ 월드] 귀 자녀의 DQ™ World 계정 인증이 3일 남았습니다. 계정 인증을 완료하고 귀 자녀의 DQ(디지털 지능 지수)를 높이세요',
    'ko/inactive_1_week.html': u'[DQ 월드] 귀 자녀의 DQ™ (디지털 지능 지수)를 높이세요',
    'es/activation_1_day_left.html': u'[DQ World] La cuenta DQ™ World de su hijo(a) expirará mañana',
    'es/activation_3_days_left.html': u'[DQ World] Quedan 3 días para activar la cuenta DQ™ World de su hijo(a) y aumentar su DQ (coeficiente de inteligencia digital)',
    'es/inactive_1_week.html': u'[DQ World] Aumente el DQ™ (coeficiente de inteligencia digital) de su hijo(a)'
}


def main():
    if not getattr(cfg, "CRON_REMINDER", False):
        sys.exit("CRON_REMINDER not enabled")

    if getattr(cfg, 'MONGODB_REPLSET_URL', False):
        client = MongoReplicaSetClient(
                    hosts_or_uri=getattr(cfg, 'MONGODB_REPLSET_URL'),
                    tz_aware=getattr(cfg, 'MONGODB_TZ_AWARE', False)
                )
    else:
        client = MongoClient(
                    host=getattr(cfg, 'MONGODB_HOST', None),
                    port=getattr(cfg, 'MONGODB_PORT', None),
                    slave_okay=getattr(cfg, 'MONGODB_SLAVE_OKAY', False),
                    tz_aware=getattr(cfg, 'MONGODB_TZ_AWARE', False)
                 )

    db = client[getattr(cfg, 'MONGODB_DATABASE')]

    if getattr(cfg, 'MONGODB_USERNAME', None) is not None:
        db.authenticate(
            getattr(cfg, 'MONGODB_USERNAME'),
            getattr(cfg, 'MONGODB_PASSWORD')
        )

    jj = Environment(
        loader=FileSystemLoader(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'reminder_templates')),
        autoescape=True
    )

    dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=tz.tzlocal())
    three_days = dt - timedelta(days=3)
    four_days = dt - timedelta(days=4)
    five_days = dt - timedelta(days=5)
    six_days = dt - timedelta(days=6)
    seven_days = dt - timedelta(days=7)
    eight_days = dt - timedelta(days=8)

    url_root = "https://www.dqworld.net/"

    if isinstance(getattr(cfg, "SITE_DOMAIN_NAME", None), basestring):
        url_root = getattr(cfg, "SITE_DOMAIN_NAME").lower()
        if not url_root.startswith("http://") and not url_root.startswith("https://"):
            url_root = "https://" + url_root
        if url_root[len(url_root)-1] != "/":
            url_root += "/"

    sent = 0
    heroes = db['izheroes'].find({'created': {'$lt': three_days, '$gte': four_days},
                                  'parent.email': {'$ne': None},
                                  'activationcode': {'$ne': ''},
                                  'teacher': False,
                                  'guardiansack': False},
                                 {'parent.email': 1,
                                  'username': 1,
                                  'lang': 1,
                                  'activationcode': 1})
    for hero in heroes:
        if not hero['activationcode'] or not hero['parent']['email']:
            continue

        if 'lang' not in hero or hero['lang'] not in __langs__:
            hero['lang'] = 'en'
        tname = '%s/activation_3_days_left.html' % hero['lang']
        tmpl = jj.get_template(tname)
        html = tmpl.render(
            url_root=url_root,
            activationcode=hero['activationcode'],
            username=hero['username']
        )
        sendmail(hero['parent']['email'], __subjects__[tname], html, hero['lang'])
        sent += 1

    heroes = db['izheroes'].find({'created': {'$lt': five_days, '$gte': six_days},
                                  'parent.email': {'$ne': None},
                                  'activationcode': {'$ne': ''},
                                  'teacher': False,
                                  'guardiansack': False},
                                 {'parent.email': 1,
                                  'username': 1,
                                  'lang': 1,
                                  'activationcode': 1})
    for hero in heroes:
        if not hero['activationcode'] or not hero['parent']['email']:
            continue

        if 'lang' not in hero or hero['lang'] not in __langs__:
            hero['lang'] = 'en'
        tname = '%s/activation_1_day_left.html' % hero['lang']
        tmpl = jj.get_template(tname)
        html = tmpl.render(
            url_root=url_root,
            activationcode=hero['activationcode'],
            username=hero['username']
        )
        sendmail(hero['parent']['email'], __subjects__[tname], html, hero['lang'])
        sent += 1

    for lang in __langs__:
        tname = '%s/inactive_1_week.html' % lang
        heroes = db['izheroes'].find({'lastlogin': {'$lt': seven_days, '$gte': eight_days},
                                      'parent.email': {'$ne': None},
                                      'dq_progress.empathybadge': {'$exists': False},
                                      'teacher': False,
                                      'lang': lang,
                                      'guardiansack': True}).distinct('parent.email')
        for email in heroes:
            tmpl = jj.get_template(tname)
            html = tmpl.render(url_root=url_root)
            sendmail(email, __subjects__[tname], html, lang)
            sent += 1

    print("completed: %d reminders sent" % sent)


def sendmail(to, subject, html, lang):
    sg = sendgrid.SendGridClient(cfg.SENDGRID_USERNAME,
                                 cfg.SENDGRID_PASSWORD,
                                 raise_errors=False)

    message = sendgrid.Mail()
    message.add_to(to)
    message.set_subject(subject)
    message.set_html(html)
    message.set_from(u'%s <%s>' % (__from__[lang], getattr(cfg, 'MANDRILL_DEFAULT_FROM', 'admin@dqworld.net')))
    sg.send(message)


if __name__ == "__main__":
    main()
