from . import client
from datetime import datetime
from flask import url_for, render_template, Response, redirect, request, current_app, abort
from mod_auth import current_user, current_userid, acl, current_session
from jinja2.exceptions import TemplateNotFound
import hashlib


MAXAGE = 61344000  #710 d


@client.route("/config.js")
@acl.requires_login
def app_config():

    if current_user.get_role() == 'Counselor':
        secret_key = current_app.config.get("SECRET_KEY", "testkeyOy3RPCgImH2ThNvjt3kGkpkoxt5yx5")
        s256 = hashlib.sha256()

        secret = secret_key + datetime.now().strftime("%y%m%d") + str(current_session.__cookie_sessid__).encode()
        s256.update(secret)
        token = "%s:%s" % (current_session.__cookie_sessid__, s256.hexdigest())
    else:
        token = None

    return Response(response=render_template('config.js',
                                             xsrf_name='XSRF-TOKEN-ADM',
                                             token=token,
                                             current_user_url=url_for('auth.user'),
                                             login_url=url_for('client.login'),
                                             logout_url=url_for('auth.logout'),
                                             base_url=request.script_root),
                    mimetype='text/javascript')


@client.route("/routes.js")
@acl.requires_login
def routesjs():

    return Response(response=render_template('routes.js'),
                    mimetype='text/javascript')


@client.route("/login")
def login():

    return render_template('login.html',
                           base_url=url_for('.index'))


@client.route("/register")
def register():
    return render_template('register.html',
                           base_url=url_for('.index'))


@client.route("/activate")
def activate():
    return render_template('activate.html',
                           base_url=url_for('.index'))


@client.route("/")
def index():

    if not current_userid:
        return redirect(url_for('.login'))
    else:
        return render_template('index.html',
                               logout_url=url_for('auth.logout'))


@client.route("/<int:_v>/views/<path:filename>")
@client.route("/views/<path:filename>")
def views(filename, _v=False):
    if not filename.startswith("/") and ".." not in filename:

        try:
            res = Response(response=render_template("views/%s" % filename,
                                                    datetime=datetime))

            if _v:
                res.cache_control.max_age = MAXAGE
                res.cache_control.public = True
                res.headers['Expires'] = "Thu, 31 Dec 2037 23:55:55 GMT"

            if filename.endswith('.json'):
                res.mimetype = 'application/json'
            elif filename.endswith('.txt'):
                res.mimetype = 'plain/text'

            return res

        except TemplateNotFound:
            abort(404)
    else:
        abort(404)

