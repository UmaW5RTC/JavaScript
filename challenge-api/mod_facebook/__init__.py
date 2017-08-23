# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import render_template, url_for, abort
from bson import ObjectId
from rest import crudmgo

mods = ['sticker', 'mediapledge']
facebook = crudmgo.CrudMgoBlueprint('facebook', __name__, model='File', template_folder='templates')


@facebook.route('/<mod>/<itemid>', endpoint='share')
def facebookshare(mod, itemid):
    if mod not in mods:
        abort(404)

    db = facebook.db
    model = facebook.db[facebook.model]
    item = None
    message = ''
    title = ''

    if mod == 'sticker':
        msg = db["JustLoveEmailLog"].find_one({"_id": ObjectId(itemid)})
        if msg is not None and isinstance(msg.get("file"), ObjectId):
            item = model.find_one({"_id": msg["file"]})
            message = msg.get('message', '')
            title = 'iZ HERO Sticker'
    else:
        item = model.find_one({"_id": ObjectId(itemid)})
        title = 'iZ HERO Media Pledge'

    if item is not None:
        link = url_for("drawing_sticker.email_download",
                       itemid=item["_id"], key=item["meta"]["key"], _external=True)
        return render_template('share_%s.html' % mod,
                               title=title,
                               url=url_for('facebook.share', mod=mod, itemid=itemid, _external=True),
                               descr=message,
                               message=message,
                               created_by=item['created']['username'],
                               created_on=str(item['created']['on']),
                               image=link,
                               link=link)
    abort(404)
