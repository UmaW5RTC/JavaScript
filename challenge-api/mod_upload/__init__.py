# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import send_from_directory, current_app, request, abort, jsonify, make_response
from flask.views import MethodView
from model.file import File, FileBin
from mod_auth import current_user, acl
import re
import hashlib
import os
import imghdr
import mimetypes


class Upload(object):
    _ufolder = "uploads"
    _upload_funcs = {}
    db = None
    vw_prefix = ""
    vw_name = "download"
    public_folders = []
    re_image = re.compile("^data:image/(\w+)?;base64,", re.IGNORECASE)

    @property
    def ufolder(self):
        return self._ufolder

    @property
    def uploaddb(self):
        return self.db["File"]

    def __init__(self, app=None, vw_prefix=None, vw_name=None, public_folders=[]):
        if app is not None:
            self.init_app(app, vw_prefix, vw_name, public_folders)
        else:
            self.vw_prefix = vw_prefix or self.vw_prefix
            self.vw_name = vw_name or self.vw_name
            self.public_folders = public_folders

    def init_app(self, app, vw_prefix=None, vw_name=None, public_folders=[]):
        self.db = app.config["mgodb"]
        self.db.register(File)
        self.db.register(FileBin)
        self._ufolder = app.config.get("UPLOAD_FOLDER", self._ufolder)
        self.vw_prefix = vw_prefix or self.vw_prefix
        self.vw_name = vw_name or self.vw_name
        self.public_folders = public_folders or self.public_folders
        app.upload_app = self
        app.add_url_rule(self.vw_prefix + "/" + self.vw_name + "/<path:filename>",
                         view_func=DownloadFile.as_view(self.vw_name))
        app.add_url_rule(self.vw_prefix + "/<int:_v>/" + self.vw_name + "/<path:filename>",
                         view_func=DownloadFile.as_view(self.vw_name + "_v"))
        app.add_url_rule("/upload/<name>", view_func=UploadFile.as_view("upload_file"))

    def add_upload(self, name, func):
        self._upload_funcs[name] = func

    def get_upload_func(self, name):
        return self._upload_funcs.get(name)

    def save_file(self, form, folder=None, meta=None, group=False, public=False, is_datauri=False):
        raw_folder = os.path.join(current_app.upload_app.ufolder, folder) \
            if folder else current_app.upload_app.ufolder

        if is_datauri:
            # this is only for saving images data
            if "file" in form:
                raw_data, ext = self.get_raw_image_data(form["file"])
                if not raw_data:
                    return False

                digest = hashlib.sha224(raw_data).hexdigest()
                filename = digest + "." + ext
                fullpath = os.path.join(raw_folder, filename)

                if not os.path.isfile(fullpath):
                    with open(fullpath, "wb") as f:
                        f.write(raw_data)

                f = self.uploaddb()
                f["meta"] = meta
                f["name"] = form["name"] + "." + ext if "name" in form else filename
                f["folder"] = folder.replace("\\", "/") if folder else ""
                f["filename"] = filename
                f["group"] = group
                f["public"] = public
                f.save()
                return f
        return False

    def get_raw_image_data(self, datauri):
        m = self.re_image.match(datauri)

        if m is None:
            return False, None

        ext = m.group(1)
        if ext.lower() not in ("png", "jpg", "jpeg", "gif"):
            return False, None

        data = self.re_image.sub("", datauri)
        raw_data = data.decode("base64")

        if not imghdr.what(None, raw_data):
            return False, None

        return raw_data, ext


class DownloadFile(MethodView):
    def get(self, filename, _v=False):
        is_public = False
        if "/" in filename:
            d = filename.split("/", 1)
            d = d[0]
            if d in current_app.upload_app.public_folders:
                is_public = True

        f = None
        if not is_public:
            basename = os.path.basename(filename)
            folder = os.path.dirname(filename)
            files = current_app.upload_app.uploaddb.find({"filename": basename, "folder": folder})
            can_view = False

            for f in files:
                created_by = f["created"] and f["created"].get("by")
                can_view = f["public"] or created_by == current_user["_id"] or current_user.get("is_parent") or\
                    (current_user.get("teacher") and (f["group"]) or (f.get("meta") and f["meta"].get("reject_share")))

                if not can_view and f["group"] and created_by and current_user["squad"] and current_user["squad"].get("code"):
                    user = current_app.upload_app.db["IZHero"].find_one({"_id": created_by})
                    if user and user["squad"] and user["squad"].get("code") == current_user["squad"].get("code"):
                        can_view = True
                        break
                elif can_view:
                    break

            if f is None:
                abort(404)
            #if not can_view:
            #    abort(403)

        def get_mimetype(fn):
            mimetype = mimetypes.guess_type(fn)[0]
            if mimetype is None:
                mimetype = 'application/octet-stream'

            return mimetype

        if current_app.config.get('USE_X_ACCEL_REDIRECT', False):
            response = make_response("")

            if '_v' in request.args:
                response.headers['Expires'] = 'Thu, 31 Dec 2037 23:55:55 GMT'
                response.headers['Cache-Control'] = 'private, max-age=315360000'
                response.headers['Pragma'] = 'cache'

            elif 'nocache' in request.args:
                response.headers['Cache-Control'] = 'no-cache, no-store, max-age=0'
                response.headers['Pragma'] = 'no-cache'

            response.headers['Content-Type'] = get_mimetype(filename)

            if 'att' in request.args:
                response.headers['Content-Disposition'] = 'attachment, filename=%s' % os.path.basename(filename)

            response.headers["X-Accel-Expires"] = 3600
            response.headers["X-Accel-Redirect"] = '%s/%s' % (current_app.config.get('X_ACCEL_REDIRECT_UPLOAD_URL', '/direct'), filename)
            return response
        else:
            return send_from_directory(current_app.upload_app.ufolder,
                                       filename,
                                       attachment_filename=f["name"] if f else filename,
                                       as_attachment='att' in request.args)


class UploadFile(MethodView):
    decorators = [acl.requires_login]

    def post(self, name=None):
        try:
            if not name:
                res = current_app.upload_app.save_file(request.json or
                                                       (request.form and request.form.to_dict()))
                return jsonify(success=bool(res), _id=(res and str(res["_id"]) or None))
            func = current_app.upload_app.get_upload_func(name)
            if func is not None:
                return jsonify(func())
        except Exception:
            pass
        return jsonify(success=False)