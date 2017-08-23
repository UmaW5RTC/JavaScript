# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify, request, abort
from flask.ext.restful import Resource, reqparse
from bson.objectid import ObjectId
from bson.binary import Binary
from flask.ext.mongokit import Document
from werkzeug.datastructures import MultiDict
from werkzeug.local import LocalProxy
from dateutil import tz, parser
from .crud import _readonly_err, strip_nonitems, CrudBlueprint, _readonly_err_dict
from pymongo.errors import DuplicateKeyError
import math
import datetime
import re
import pymongo


def _getitem(self, itemid):
    filt = {}
    if self.filter_by and isinstance(self.filter_by, dict):
        filt = self.filter_by.copy()

    filt["_id"] = ObjectId(itemid)
    return self.model.find_one(filt)


class RootDocument(Document):
    skip_validation = True

    def _update_unique_field(self, key, value, errmsg="Value is already in use."):
        if not self.get("_id") and value and value != self.get(key) and \
                self.collection.find_one({key: value}, {"_id": 1}):
            return errmsg
        self[key] = value
        return None

    def _update_isin_field(self, collection, key, value, errmsg="Invalid value selected."):
        if isinstance(collection, (tuple, list)):
            collection, ckey = collection
        else:
            ckey = key

        if not self.collection.database[collection].find_one({ckey: value}, {"_id": 1}):
            return errmsg
        self[key] = value
        return None

    def _update_datetime(self, key, value, errmsg="Invalid date/time format"):
        if value:
            if isinstance(value, datetime.datetime):
                if not value.tzinfo:
                    self[key] = value.replace(tzinfo=tz.tzutc())
            elif isinstance(value, datetime.date):
                self[key] = datetime.datetime(year=value.year, month=value.month, day=value.day, tzinfo=tz.tzutc())
            elif isinstance(value, basestring):
                try:
                    self[key] = parser.parse(value)
                except Exception:
                    return errmsg
            else:
                return errmsg
        else:
            self[key] = None

        return None


class ListAPI(Resource):
    db = None
    model = None
    limit = 25
    filter_by = None
    readonly = False
    no_ulimit = False
    order = ""
    sendcount = False

    def get(self):
        return jsonify(self._get())

    def post(self):
        return jsonify(self._post())

    def _get(self):
        cursor, pages, count = self._getcursorwithcount()
        d = dict(items=[model_to_json(m, is_list=True) for m in cursor], pages=pages)
        if self.sendcount:
            d["count"] = count
        return d

    def _getcursorwithcount(self):
        args = self._argsparser().parse_args()
        start, stop, limit = self._paginate(args)
        d = self.filter_by.copy() if self.filter_by and isinstance(self.filter_by, dict) else {}
        d = self._searchquery(d, args)
        cursor = self.model.find(d) if d else self.model.find()
        cursor = self._orderquery(cursor, args)
        pages = 0
        count = cursor.count()
        if limit:
            cursor = cursor.skip(start).limit(limit)
            # cursor's count doesn't count with skip and limit by default
            pages = int(math.ceil(count / float(limit)))
        elif count:
            pages = 1
        return cursor, pages, count

    def _getcursor(self):
        cursor, pages, count = self._getcursorwithcount()
        return cursor, pages

    def _post(self):
        if self.readonly:
            return _readonly_err_dict()
        item, err = self._formitem()
        if item is None or err:
            return {"success": False, "errors": err}
        item = self._setfilter(item)
        try:
            item.save()
        except DuplicateKeyError:
            return {"success": False, "error": "Duplicate value"}
        except Exception as e:
            print(e)
            abort(500)

        return {"success": True, "id": get_flat_value(item.get("_id"))}

    @staticmethod
    def _argsparser():
        pr = reqparse.RequestParser()
        pr.add_argument("p", type=int, store_missing=False)
        pr.add_argument("l", type=int, store_missing=False)
        pr.add_argument("s", type=str, store_missing=False)
        pr.add_argument("o", type=str, store_missing=False)
        return pr

    def _paginate(self, args):
        limit = args.get("l", self.limit)
        if self.no_ulimit and limit < 1:
            limit = self.limit
        elif limit < 1:
            return 0, 0, 0

        page = args.get("p", 1)
        if page < 1:
            page = 1
        start = (page - 1) * limit
        stop = page * limit

        return start, stop, limit

    def _searchquery(self, d, args):
        search = args.get("s", "").strip()
        if len(search) >= 3 and hasattr(self.model, "__crud_searchfield__") and self.model.__crud_searchfield__:
            search = "(^|\s)" + re.escape(search)
            searchor = [{fname: {"$regex": search, "$options": "i"}} for fname in self.model.__crud_searchfield__]
            if "$and" in d:
                d["$and"].append({"$or": searchor})
            elif "$or" in d:
                d["$and"] = [{"$or": searchor}, {"$or": d["$or"]}]
                del d["$or"]
            else:
                d["$or"] = searchor
        return d

    def _orderquery(self, c, args):
        order = args.get("o", self.order).strip()
        if order == "":
            return c.sort("_id", pymongo.ASCENDING)

        # if '-' char prefix the fieldname, it means a descending order.
        isdesc = order[0] == '-'
        if isdesc:
            order = order[1:].strip()

        # does not allow sorting on columns that are omitted from results
        c = c.sort((order if not json_is_omitted(self.model, order) else "_id"), (pymongo.DESCENDING if isdesc else pymongo.ASCENDING))
        return c

    def _formitem(self):
        # This is the WTForm to validate input data.
        mform = getattr(self.model, "__form__", None)

        # Flask-WTForms requires the data to be a MultiDict instance.
        # request.form is already MultiDict but request.json is not.
        data = MultiDict(request.json) if request.json is not None else request.form

        if mform is not None:
            form = mform(data, csrf_enabled=False)
            if not form.validate():
                return None, form.errors
            data = strip_nonitems(form.data, data)

        try:
            item = self.model()
            if hasattr(item, "update_raw"):
                err = item.update_raw(data)
            else:
                err = {}
                for k, v in data.iteritems():
                    func = getattr(item, "update_" + k, None)
                    if func and callable(func):
                        e = func(v)
                        if e:
                            err[k] = e
                    else:
                        item[k] = v
                if not err:
                    err = None
        except (AssertionError, AttributeError, ValueError) as e:
            return None, e.message

        return item, err

    def _setfilter(self, item):
        if self.filter_by and isinstance(self.filter_by, dict):
            for k, v in self.filter_by.iteritems():
                if k[0:1] == "$":
                    continue
                if "." in k:
                    splitnames = k.split(".")
                    lastname = splitnames[-1]
                    splitnames = splitnames[:-1]
                    curlvl = item
                    for k2 in splitnames:
                        if not isinstance(curlvl[k2], dict):
                            curlvl[k2] = {}
                        curlvl = curlvl[k2]
                    curlvl[lastname] = v
                else:
                    item[k] = v
        return item


class ListArrayAPI(ListAPI):
    unwind = None

    def _get(self):
        cursor, pages, count = self._getcursorwithcount()
        d = dict(items=[dict_to_json(m, self.model) for m in cursor], pages=pages)
        if self.sendcount:
            d["count"] = count
        return d

    def _getcursorwithcount(self):
        args = self._argsparser().parse_args()
        start, stop, limit = self._paginate(args)
        d = self.filter_by.copy() if self.filter_by and isinstance(self.filter_by, dict) else {}
        d = self._searchquery(d, args)
        unwind = "$" + self.unwind if isinstance(self.unwind, basestring) and self.unwind[0] != '$' else self.unwind

        aggset = [
            {"$unwind": unwind},
            {"$match": d},
            {"$group": {"_id": None, "count": {"$sum": 1}}}
        ]
        cursor = self.model.collection.aggregate(aggset, allowDiskUse=True)
        count = cursor["result"][0]["count"] if cursor["result"] else 0
        pages = 0

        aggset = self._orderquery(aggset, args)

        if limit:
            aggset.append({"$skip": start})
            aggset.append({"$limit": limit})
            pages = int(math.ceil(count / float(limit)))
        elif count:
            pages = 1

        cursor = self.model.collection.aggregate(aggset, allowDiskUse=True)
        return cursor["result"], pages, count

    def _orderquery(self, c, args):
        order = args.get("o", self.order).strip()
        if order == "":
            c[2] = {"$sort": {"_id": pymongo.ASCENDING}}
            return c

        # if '-' char prefix the fieldname, it means a descending order.
        isdesc = order[0] == '-'
        if isdesc:
            order = order[1:].strip()

        # does not allow sorting on columns that are omitted from results
        c[2] = {"$sort": {(order if order != "" and not json_is_omitted(self.model, order) else "_id"): (pymongo.DESCENDING if isdesc else pymongo.ASCENDING)}}
        return c


class ItemAPI(Resource):
    db = None
    model = None
    filter_by = None
    readonly = False

    def get(self, itemid):
        data = self._getitem(itemid)
        if data is None:
            return jsonify({})
        return jsonify(model_to_json(data, is_single=True))

    def put(self, itemid):
        return jsonify(self._put(itemid))

    def _put(self, itemid):
        if self.readonly:
            return _readonly_err_dict()

        res, data = self._formdata()

        # if password is student , res is return to false
        
        if not res:
            return {"success": False, "errors": data}

        item, err = self._updateitem(itemid, data)
        if item is None or err:
            return {"success": False, "errors": err}

        try:
            item.save()
        except DuplicateKeyError:
            return {"success": False, "error": "Duplicate value"}
        except Exception:
            abort(500)

        return {"success": True}

    def delete(self, itemid):
        if self.readonly:
            return _readonly_err()

        item = self._getitem(itemid)
        if item is not None:
            item.delete()
            return jsonify(success=True, id=itemid)
        return jsonify(success=False, error="Item not found.")

    _getitem = _getitem

    def _formdata(self):
        data = MultiDict(request.json) if request.json is not None else request.form

        mform = getattr(self.model, "__form__", None)
        if mform is not None:
            form = mform(data, csrf_enabled=False)
            form.__is_update__ = True
            if not form.validate():
                return False, form.errors
            data = strip_nonitems(form.data, data)

        return True, data

    def _updateitem(self, itemid, data, item=None):
        if item is None:
            item = self._getitem(itemid)
        if hasattr(item, "update_raw"):
            err = item.update_raw(data)
        elif item is not None:
            err = {}
            for k, v in data.iteritems():
                func = getattr(item, "update_" + k, None)
                if func is not None and callable(func):
                    e = func(v)
                    if e:
                        err[k] = e
                else:
                    item[k] = v
            if not err:
                err = None
        else:
            err = "Item not found."
        return item, err


class AppendAPI(Resource):
    db = None
    model = None
    field = None
    filter_by = None

    _getitem = _getitem

    def post(self, itemid):
        item = self._getitem(itemid)
        data = MultiDict(request.json) if request.json is not None else request.form

        if hasattr(item, "append_raw"):
            item.append_raw(data)
        elif data:
            data = data.to_dict()
            filt = self.filter_by.copy() if self.filter_by else {}
            filt["_id"] = itemid
            self.model.update(filt, {self.field: {"$push": data}})
            """
            data = self.normalise_data(data)
            for k, v in data.iteritems():
                if "." in k:
                    namesplit = k.split(".")
                    pkg = namesplit[:-1]
                    name = namesplit[-1]
                    struct = self.model.structure
                    curlevel = item

                    for k2 in pkg:
                        if k2 in curlevel:
                            curlevel = curlevel[k2]
                        else:
                            curlevel[k2] = {}
                            curlevel = curlevel[k2]
                        if k2 in struct:
                            struct = struct[k2]

                    if name not in curlevel:
                        curlevel[name] = []
                    curr = curlevel
                else:
                    curr = item
                    name = k
                    struct = self.model.structure[k]

                if isinstance(curr[name], list):
                    curr[name].append(v)
                elif isinstance(struct[name], list):
                    curr[name] = [v]
            item.save()
            """

    def delete(self, itemid):
        data = MultiDict(request.json) if request.json is not None else request.form
        if data:
            data = data.to_dict()
            filt = self.filter_by.copy() if self.filter_by else {}
            filt["_id"] = itemid
            self.model.update(filt, {"$pull": {self.field: data}})
        return jsonify(success=True)

    @staticmethod
    def _normalise_data(data):
        names = {}
        for k in data.iterkeys():
            if "." in k:
                nest = k.split(".")
                pkg = nest[:-1]
                name = nest[-1]

                if pkg not in names:
                    if len(data.getlist(k, ())) > 1:
                        names[pkg] = []
                        for v in data.getlist(k):
                            names[pkg].append({name: v})
                    else:
                        names[pkg] = [{name: v}]
                else:
                    if len(data.getlist(k, ())) > 1:
                        i = 0
                        try:
                            for v in data.getlist(k):
                                names[pkg][i][name] = v
                                i += 1
                        except IndexError:
                            pass
                    else:
                        names[pkg][0][name] = v
        return names


class ToggleAPI(Resource):
    db = None
    model = None
    filter_by = None
    #: The name of the toggle field.
    toggle = ""
    #: Whether the value for the toggle field is int (meaning 0/1) instead of boolean
    is_int = False
    #: Whether the value for the toggle field is custom
    #: Set it to a tuple/list of value that is in index 0 = False and index 1 = True. e.g. ("Inactive", "Active")
    is_val = None

    def get(self, itemid):
        item = self._getitem(itemid)
        if item is not None:
            return jsonify({self.toggle: item.get(self.toggle)})
        return jsonify({})

    def post(self, itemid):
        item = self._getitem(itemid)
        res = {"success": False}
        if item is not None and self.toggle in item:
            val = self.is_val[1] if isinstance(self.is_val, (tuple, list)) else 1 if self.is_int else True
            item[self.toggle] = val
            item.save()
            res["success"] = True
            res["toggle"] = val
        else:
            res["error"] = "Item not found"
        return jsonify(res)

    def put(self, itemid):
        item = self._getitem(itemid)
        res = {"success": False}
        if item is not None and self.toggle in item:
            if isinstance(self.is_val, (tuple, list)):
                try:
                    state = self.is_val[self.is_val.index(item[self.toggle]) ^ 1]
                except ValueError:
                    state = self.is_val[0]
            else:
                state = item[self.toggle] ^ 1 if self.is_int else not item[self.toggle]
            item[self.toggle] = state
            item.save()
            res["success"] = True
            res["toggle"] = state
        else:
            res["error"] = "Item not found"
        return jsonify(res)

    def delete(self, itemid):
        item = self._getitem(itemid)
        res = {"success": False}
        if item is not None and self.toggle in item:
            val = self.is_val[0] if isinstance(self.is_val, (tuple, list)) else 0 if self.is_int else False
            item[self.toggle] = val
            item.save()
            res["success"] = True
            res["toggle"] = val
        else:
            res["error"] = "Item not found"
        return jsonify(res)

    _getitem = _getitem


class CrudMgoBlueprint(CrudBlueprint):
    db = None
    model = None

    def __init__(self, *args, **kargs):
        m = kargs.get("model", None)
        if m is not None:
            del kargs["model"]

        super(CrudMgoBlueprint, self).__init__(*args, **kargs)

        if m is not None:
            def setdbmodel(state):
                self.model = m
                self.db = state.app.config.get("mgodb")
            self.record_once(setdbmodel)

    def resource(self, cls):
        cls.__oldinit__ = cls.__init__

        def init(s, *args, **kargs):
            s.db = self.db
            s.model = self.db[self.model]
            s.__oldinit__(*args, **kargs)

        cls.__init__ = init
        return cls


def model_to_json(model, is_list=False, is_single=False):
    if model is None:
        return {}

    if isinstance(model, LocalProxy):
        model = model._get_current_object()

    meth = getattr(model, "json", None)
    if meth is not None and callable(meth):
        return meth()

    def diglist(l, m, prefix=None):
        _l = []
        if isinstance(m, list):
            if len(l) > 0:
                _struct = l[0]
                _is_dict = isinstance(_struct, dict)
                _is_list = not _is_dict and isinstance(_struct, list)
                for _v in m:
                    if _is_dict and _v:
                        _l.append(digdict(_struct.iteritems(), _v, prefix))
                    elif _is_list and _v:
                        _l.append(diglist(_struct, _v, prefix))
                    else:
                        _l.append(to_flat_value(_v))
            else:
                _l = [to_flat_value(_v) for _v in m]
        return _l

    def digdict(d, m, prefix=None):
        _d = {}
        for _k, _v in d:
            _prefix = prefix + "." + _k if prefix else _k
            if not json_is_omitted(model, _prefix, is_list, is_single):
                if isinstance(_v, dict) and _v:
                    _d[_k] = digdict(_v.iteritems(), m[_k], _prefix) if _k in m else {}
                elif isinstance(_v, list) and _v:
                    _d[_k] = diglist(_v, m[_k], _prefix) if _k in m else []
                else:
                    _d[_k] = to_flat_value(m.get(_k))
        return _d

    jsondict = digdict(model.structure.iteritems(), model)

    if "_id" not in model.structure and not json_is_omitted(model, "_id", is_list, is_single):
        jsondict["_id"] = get_flat_value(model.get("_id"))

    return jsondict


def dict_to_json(md, model, is_list=False, is_single=False):
    if model is None:
        return {}

    if isinstance(model, LocalProxy):
        model = model._get_current_object()

    def diglist(m, prefix=None):
        _l = []
        if isinstance(m, list):
            if len(m) > 0:
                _is_dict = isinstance(m[0], dict)
                _is_list = not _is_dict and isinstance(m[0], list)
                for _v in m:
                    if _is_dict and _v:
                        _l.append(digdict(_v, prefix))
                    elif _is_list and _v:
                        _l.append(diglist(_v, prefix))
                    else:
                        _l.append(to_flat_value(_v))
            else:
                _l = [to_flat_value(_v) for _v in m]
        return _l

    def digdict(m, prefix=None):
        _d = {}
        for _k, _v in m.iteritems():
            _prefix = prefix + "." + _k if prefix else _k
            if not json_is_omitted(model, _prefix, is_list, is_single):
                if isinstance(_v, dict) and _v:
                    _d[_k] = digdict(m[_k], _prefix) if _k in m else {}
                elif isinstance(_v, list) and _v:
                    _d[_k] = diglist(m[_k], _prefix) if _k in m else []
                else:
                    _d[_k] = to_flat_value(m.get(_k))
        return _d

    return digdict(md)


def get_flat_value(val):
    if isinstance(val, datetime.datetime):
        if not val.tzinfo:
            # mongo defaults to utc
            val = val.replace(tzinfo=tz.tzutc())
        val = val.isoformat()
    elif isinstance(val, ObjectId) or isinstance(val, Binary):
        val = str(val)
    return val


def to_flat_value(d):
    _d = None
    if isinstance(d, (tuple, list)):
        _d = [(to_flat_value(d[i]) if isinstance(d[i], (tuple, list, dict)) else get_flat_value(d[i]))
              for i in xrange(len(d))]
    elif isinstance(d, dict):
        _d = {k: (to_flat_value(v) if isinstance(v, (tuple, list, dict)) else get_flat_value(v))
              for k, v in d.iteritems()}
    else:
        _d = get_flat_value(d)
    return _d


def json_is_omitted(model, name, is_list=False, is_single=False):
    omit = False

    if is_list:
        omit = name in getattr(model, "__json_list_omit__", ())
    if not omit and is_single:
        omit = name in getattr(model, "__json_single_omit__", ())
    if not omit:
        omit = name in getattr(model, "__json_omit__", ())

    return omit


def localtime():
    return datetime.datetime.now(tz.tzlocal())


def utctime():
    return datetime.datetime.now(tz.tzutc())