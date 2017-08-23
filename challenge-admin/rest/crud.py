# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import jsonify, Blueprint, request
from flask.ext.restful import Resource, reqparse
from sqlalchemy import inspect, or_, and_
from sqlalchemy.orm import attributes, contains_eager
from werkzeug.datastructures import MultiDict
from wtforms.validators import StopValidation
from werkzeug.local import LocalProxy
from dateutil import tz
from wtforms import SelectField
import math
import datetime
import re


class ListAPI(Resource):
    """Base Class to list or insert item(s) of a db model.
    It is used to create a straightforward restful API of listing and insert item into model.
    Use in conjunction with :py:class:`ItemAPI` to create a complete restful API (list/get/create/update/delete)
    for db model.
    """

    #: The flask SQLAlchemy db object
    db = None
    #: The db model object
    model = None
    #: The default limit of items per page
    limit = 25
    #: The dict to pass into filter_by of model query
    filter_by = None
    #: Whether it is readonly. If true, only get method works, while post method will return success=False
    readonly = False

    def get(self):
        """Retrieve a list of items from a database model.
        It accepts url query str to search, sort, paginate through the list.
        url query param:
            s: The search terms separated by spaces. See :py:meth:`ListAPI._searchquery` for search support.
            o: The field to sort the results by. It can only be a field that is also returned as a result
            p: The page of list. It defaults to page 1.
            l: The limit of items per page. It defaults to 25
        The json result will contains 2 keys (items, pages), where items will contain the list of model,
        and pages will contain the total number of pages available.
        See :py:func:`model_to_json` on how the model object is converted to a dict and its functionalities.

        :return: The json response to be sent back to the browser
        """
        args = self._argsparser().parse_args()
        start, stop, limit = self._paginate(args)
        q = self._filter(self.model.query)
        q = self._searchquery(q, args)
        q = self._orderquery(q, args)
        data = q.slice(start, stop).all()
        pages = int(math.ceil(q.count() / float(limit)))
        return jsonify(items=[model_to_json(m, is_list=True) for m in data], pages=pages)

    def post(self):
        """Create a new item in the database model. This method is only available if it is not readonly
        If the item is successfully inserted into the database, the ID of the item will be returned.
        If not, a dictionary of key:fieldname, value:error will be returned.
        Validation of input values is supported. See :py:meth:`ListAPI._formitem` for more information.

        :return: The json response with success:bool, and id:itemid if success, or errors:dict(fieldname=error)
        """
        if self.readonly:
            return _readonly_err()
        item, err = self._formitem()
        if item is None:
            return jsonify({"success": False, "errors": err})
        item = self._setfilter(item)
        self.db.session.add(item)
        self.db.session.commit()
        return jsonify({"success": True, "id": item.id})

    def _formitem(self):
        """Creates a new model object with inputs parameters from the request data.
        This method will validate input values. To support validation,
        add a __form__ attribute in the model pointing to the WTForm class.
        Or simply, include sqlalchemy.orm.validates decorated methods in the model class
        that raises AssertionError, AttributeError, or ValueError.
        Override this method to perform own validation and creation of model object.

        :return: (model object, error message) tuple. If validation for model fails, return None for model object
        and attach a error message. Else error message should be False
        """
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
            item = self.model(**data)
        except (AssertionError, AttributeError, ValueError) as e:
            return None, e.message

        return item, False

    def _paginate(self, args):
        """Provides paging of items. Method will take values from 'p' and 'l' request query to calculate
        the current start, stop, and limit of the page.
        Override this method to perform own calculation of start, stop, limit of the list.

        :return: (int start, int stop, int limit). start is the offset of the slice, stop is the end of the slice.
        limit is start - stop.
        """
        limit = args.get("l", self.limit)
        if limit < 1:
            limit = self.limit

        page = args.get("p", 1)
        if page < 1:
            page = 1
        start = (page - 1) * limit
        stop = page * limit

        return start, stop, limit

    @staticmethod
    def _argsparser():
        """The request parser for all the request variables needed for the list.
        Extend on this method to add on arguments to the parser to get custom variables for custom functionalities.

        :return: The parser
        """
        parser = reqparse.RequestParser()
        parser.add_argument("p", type=int, store_missing=False)
        parser.add_argument("l", type=int, store_missing=False)
        parser.add_argument("s", type=str, store_missing=False)
        parser.add_argument("o", type=str, store_missing=False)
        return parser

    def _filter(self, q):
        """Apply filter from self.filter_by attribute.

        :param q: The db model's query object
        :return: The updated db model's query object
        """
        if self.filter_by and isinstance(self.filter_by, dict):
            q = q.filter_by(**self.filter_by)
        return q

    def _setfilter(self, item):
        """Apply filter value to model that is going to be inserted into database
        :param item: The model to be commited to db
        :return: The model that has the filter value applied
        """
        if self.filter_by and isinstance(self.filter_by, dict):
            for k, v in self.filter_by.iteritems():
                setattr(item, k, v)
        return item

    def _searchquery(self, q, args):
        """Filter the database results based on the search terms provided.
        To support searching, the db model should include a
        __crud_searchfield__ attribute of a tuple of field names to search in.
        Searching a foreign field is allowed. Just use `attrname.fieldname`
        where attrname is the name of the attribute that contains the db.relationship in the current model
        and fieldname is the name of the field of the foreign model to search in. (e.g. user.name)
        The search is performed using the database LIKE, with left/right '%' wildcard.
        For each field name, the search will perform a OR. For each space separated term, a AND will be performed.
        e.g. for a "s=term1+term2" request query and a __crud_searchfield__ = ("field1", "field2")
        (field1 LIKE '%term1%' AND field1 LIKE '%term2%') OR (field2 LIKE '%term2%' AND field2 LIKE '%term2%')
        Override this method to perform own search functionality.

        :param q: The db model's query object
        :param args: The request args (argparser) dict that with 's' key containing the search terms.
        :return: The updated db model's query object
        """
        search = args.get("s", "").strip()
        if len(search) >= 3 and self.model.__crud_searchfield__:
            q, fcols = get_search_filters(self.model, q, search)
            if fcols:
                q = q.filter(or_(*fcols))
        return q

    def _orderquery(self, q, args):
        """Sort the list result based on field name in the 'o' param of the request query.
        Currently can only sort a single field but foreign fields are supported.
        To sort by a foreign field, the model name must be in the __json_foreign__ or __json_list_foreign__ attribute.
        It must also not be a field omitted, or if using whitelisting, a field that is whitelisted.
        See :py:func:`model_to_json` for the type of on how json_foreign attribute are used and field omit/whitelist.

        :param q: The db model's query object
        :param args: The request args (argparser) dict that with 'o' key containing the name of order field.
        :return: The updated db model's query object
        """
        order = args.get("o", "").strip()
        if order == "":
            return q

        # if '-' char prefix the fieldname, it means a descending order.
        isdesc = order[0] == '-'
        if isdesc:
            order = order[1:].strip()

        if order != "":
            # sorting using a field of a foreign model.
            if "." in order:
                rel, order = order.split(".", 1)
                relcls = get_relationship_model(self.model, rel)
                col = get_model_col(relcls, order)

                # can only search foreign fields if foreign model is included in the final result.
                if col is not None and relcls is not None and\
                        json_has_foreign(self.model, rel, is_list=True) and not json_is_omitted(relcls, order):
                    relation = getattr(self.model, rel)
                    q = q.outerjoin(relation).options(contains_eager(relation))
                    q = q.order_by(col.desc() if isdesc else col)
            else:
                col = get_model_col(self.model, order)
                # does not allow sorting on columns that are omitted from results
                if col is not None and not json_is_omitted(self.model, order):
                    q = q.order_by(col.desc() if isdesc else col)
        return q


class ItemAPI(Resource):
    """Serves as similar purpose as :py:class:`ListAPI` except that this class mainly deals with a single item.
    It supports get/update/delete of a single item given its <itemid>.
    All get/put/delete methods requires a itemid param.
    The class attributes serves an identical purpose as :py:class:`ListAPI`.
    """

    db = None
    model = None
    filter_by = None
    readonly = False

    def get(self, itemid):
        """Gets the json serialization of the model item.

        :param itemid: The ID of the item
        :return: The json response to be sent back to the browser
        """
        data = self._getitem(itemid)
        if data is None:
            return jsonify({})
        return jsonify(model_to_json(data, is_single=True))

    def put(self, itemid):
        """Update the item in the database. Like :py:meth:`ListAPI.post`,
        this method supports input validation. See :py:meth:`ItemAPI._formdata` for more info on input validation.

        :param itemid: The ID of the item
        :return: The json response to be sent back to the browser
        """
        if self.readonly:
            return _readonly_err()

        res, data = self._formdata()
        if not res:
            return jsonify({"success": False, "errors": data})

        res, err = self._updateitem(itemid, data)
        if not res:
            return jsonify({"success": False, "errors": err})

        self.db.session.commit()
        return jsonify({"success": True})

    def delete(self, itemid):
        """Delete the item from the database.

        :param itemid: The ID of the item
        :return: The json response to be sent back to the browser
        """
        if self.readonly:
            return _readonly_err()

        item = self._getitem(itemid)
        if item is not None:
            self.db.session.delete(item)
            self.db.session.commit()
            return jsonify(success=True, id=item.id)
        return jsonify(success=False, error="Item not found.")

    def _getitem(self, itemid):
        """Get a loaded model from the database. If filter_by attribute is set, the filter will apply.
        Note: when using the filter_by, the method will query the database with the id name `id`.
        It will fail if the primary key is not named `id`. This does not have any effect if filter_by is empty.

        :param itemid: The ID of the item
        :return: The loaded model object or None if not found.
        """
        if self.filter_by and isinstance(self.filter_by, dict):
            filt = self.filter_by.copy()
            filt["id"] = itemid
            data = self.model.query.filter_by(**filt).first()
        else:
            data = self.model.query.get(itemid)
        return data

    def _formdata(self):
        # TODO: this provides a similar function as the `ListAPI._formdata` method.
        # Refactor this into a function of its own that is called by both classes.
        # This _formdata method should remain though (with a call to the refactored func)?
        # So child class can still override its functionality.
        data = MultiDict(request.json) if request.json is not None else request.form

        mform = getattr(self.model, "__form__", None)
        if mform is not None:
            form = mform(data, csrf_enabled=False)
            form.__is_update__ = True
            if not form.validate():
                return False, form.errors
            data = strip_nonitems(form.data, data)

        return True, data

    def _updateitem(self, itemid, data):
        """Performs the actual update of the value into the database after data is validated.
        This method does not perform any input validation. Validation is done in _formdata method.

        :param itemid: The ID of the item
        :param data: The dict containing the updated values of the model object
        :return: (success, error) where success is a boolean of whether data is updated successfully
        and error containing any error message if not successful.
        """
        item = self._getitem(itemid)
        cols = get_model_pubcolnames(self.model)
        try:
            for field, value in data.iteritems():
                # setting a field that is listed in filter_by is not allowed
                if field in cols and getattr(item, field, None) != value and (not self.filter_by or
                                                                              field not in self.filter_by):
                    setattr(item, field, value)
            return True, None
        except (AssertionError, AttributeError, ValueError) as e:
            return False, e.message


class ToggleAPI(Resource):
    """Base class to provide an restful API for toggling a model field value between True/False.
    Class provides, full get/post/put/delete methods to retrieve current value, set value to True,
    toggle True/False, and set value to False.
    """

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
        """Get the toggle value. The json dict will just contain {toggle_name: toggle_value},
        or an empty dict if item of itemid does not exists.

        :param itemid: The ID of the item
        """
        item = self._getitem(itemid)
        if item is not None:
            return jsonify({self.toggle: getattr(item, self.toggle, None)})
        return jsonify({})

    def post(self, itemid):
        """Set the toggle value to True or 1 or a value equivalent to True depending on how :py:attr:`ToggleAPI.is_int`
        or :py:attr:`ToggleAPI.is_val` is being set. Is_val takes precedence over is_int.
        The json dict returned to the browser will contain {success:boolean, toggle: value}
        Note that the key toggle is "toggle" as is, instead of the toggle name.

        :param itemid: The ID of the item
        """
        item = self._getitem(itemid)
        res = {"success": False}
        if item is not None and hasattr(item, self.toggle):
            val = self.is_val[1] if isinstance(self.is_val, (tuple, list)) else 1 if self.is_int else True
            setattr(item, self.toggle, val)
            self.db.session.commit()
            res["success"] = True
            res["toggle"] = val
        else:
            res["error"] = "Item not found"
        return jsonify(res)

    def put(self, itemid):
        """Toggle the value between true/false or its equivalent value depending on its current value.
        If the current value is true, it will be set to false now. Likewise if the current value is false.

        :param itemid: The ID of the item
        """
        item = self._getitem(itemid)
        res = {"success": False}
        if item is not None and hasattr(item, self.toggle):
            if isinstance(self.is_val, (tuple, list)):
                try:
                    state = self.is_val[self.is_val.index(getattr(item, self.toggle)) ^ 1]
                except ValueError:
                    state = self.is_val[0]
            else:
                state = getattr(item, self.toggle) ^ 1 if self.is_int else not getattr(item, self.toggle)
            setattr(item, self.toggle, state)
            self.db.session.commit()
            res["success"] = True
            res["toggle"] = state
        else:
            res["error"] = "Item not found"
        return jsonify(res)

    def delete(self, itemid):
        """Set the toggle value to False or its equivalent.

        :param itemid: The ID of the item
        """
        item = self._getitem(itemid)
        res = {"success": False}
        if item is not None and hasattr(item, self.toggle):
            val = self.is_val[0] if isinstance(self.is_val, (tuple, list)) else 0 if self.is_int else False
            setattr(item, self.toggle, val)
            self.db.session.commit()
            res["success"] = True
            res["toggle"] = val
        else:
            res["error"] = "Item not found"
        return jsonify(res)

    def _getitem(self, itemid):
        # TODO: this provides a similar function as the `ItemAPI._getitem` method.
        if self.filter_by and isinstance(self.filter_by, dict):
            filt = self.filter_by.copy()
            filt["id"] = itemid
            data = self.model.query.filter_by(**filt).first()
        else:
            data = self.model.query.get(itemid)
        return data


class CrudBlueprint(Blueprint):
    """Extends the base Blueprint to provide the functionality of injecting the db and model object into resource.
    Restful API resource class like ListAPI, ItemAPI, and ToggleAPI makes use of this to get db and model var.
    For CrudBlueprint to work as db/model injector, an app config of "db" that contains the db object is required.
    CrudBlueprint will also attempt to get the model object from the app config using a naming convention of
    "model.<model_name>" where <model_name> is the name of the model passed through a keyword argument of model
    when creating the blueprint.
    To inject the db/model object into the resource, decorate the resource class with the `resource` method.
    The db/model attribute will be populated when the resource object is constructed/initialized.
    """
    db = None
    model = None

    def __init__(self, *args, **kargs):
        m = kargs.get("model", None)
        if m is not None:
            del kargs["model"]

        super(CrudBlueprint, self).__init__(*args, **kargs)

        if m is not None:
            def setdbmodel(state):
                self.model = state.app.config.get("model." + m)
                self.db = state.app.config.get("db")
            self.record_once(setdbmodel)

    def resource(self, cls):
        cls.__oldinit__ = cls.__init__

        def init(s, *args, **kargs):
            s.db = self.db
            s.model = self.model
            s.__oldinit__(*args, **kargs)

        cls.__init__ = init
        return cls


def model_to_json(model, is_single=False, is_list=False, allows=None):
    """Convert a model object into a dict suitable for jsonify.
    The function will first check if a `json` method exists on the model.
    If it does, the json method will be used to create the dict (use this feature to create a custom json dict).
    Otherwise the function will look through the db columns to generate the dict.

    Attributes can be set on the model class to configure what data the returned dict will include:
    __json_omit__: A tuple containing the names of fields that should be omitted from the dict.
    __json_foreign__: A tuple containing the names of foreign relationship object that should be embedded.
                      The end result is a nested dict containing the foreign relationship accessable through its name.
                      e.g. {field:value, field:value, foreign_name:{foreign_field:foreign_value,foreign_field:...}...}
                      Use a colon ':' char to list a comma separate whitelist fields that is allowed on the nested dict.
                      e.g. "user:name,firstname,lastname"
                      In the above case, only the fields name, firstname, and lastname will be included in the user.
    __json_single_foreign__: similar to __json_foreign__ except it is only used when the param is_single
                             of this function is set to True. is_single is set to True
                             when called by :py:meth:`ItemAPI.get`
    __json_list_foreign__: similar to __json_single_foreign__ except when is_list is True. is_list is set to True
                           when called by :py:meth:`ListAPI.get`

    :param model: The model object to be converted to a dict.
    :param is_single: Whether it is a single model; is insignificant unless you want to invoke __json_single_foreign__
    :param is_list: Whether it is part of a list of models; is insignificant unless to invoke __json_list_foreign__
    :param allows: A list of whitelisted fields. Only fields listed here will be included if param is not empty.
    :return: The dict of the model
    """
    if model is None:
        return {}

    # used for variables like current_user which is encap using LocalProxy
    if isinstance(model, LocalProxy):
        model = model._get_current_object()

    # if model provides a json method, we will just use that.
    meth = getattr(model, "json", None)
    if meth is not None and callable(meth):
        return meth()

    modclass = inspect(model.__class__)
    omit = getattr(model, "__json_omit__", ())

    jsondict = {}
    for name in modclass.column_attrs.keys():
        # if field is a private property, tries to see if there is a public one and use it.
        if name[0] == "_" and hasattr(model, name[1:]):
            name = name[1:]
        # not in omit or if whitelist is provided, must be in whitelist
        if name not in omit and (not allows or name in allows):
            jsondict[name] = get_json_value(model, name)

    def jsonforeign(foreign):
        for aname in foreign:
            fields = None
            if ":" in aname:
                # getting the whitelisted fields
                aname, fields = model_to_json.name_split(aname, 1)
                fields = model_to_json.whitelist_split(fields.strip())

            if not allows or aname in allows:
                fmodel = getattr(model, aname)
                if isinstance(fmodel, (list, tuple)):
                    jsondict[aname] = [model_to_json(m, allows=fields) for m in fmodel]
                else:
                    jsondict[aname] = model_to_json(fmodel, allows=fields)

    jsonforeign(getattr(model, "__json_foreign__", ()))
    if is_single:
        jsonforeign(getattr(model, "__json_single_foreign__", ()))
    if is_list:
        jsonforeign(getattr(model, "__json_list_foreign__", ()))

    return jsondict
model_to_json.name_split = re.compile("\\s*:\\s*").split
model_to_json.whitelist_split = re.compile("\\s*,\\s*").split


def get_json_value(model, name):
    """Get the value suitable for json serialization from the provided model and its field name.
    If the value is a datetime object, it will set a local timezone if not found and returns a iso-format string.

    :param model: The model to extract the value
    :param name: The name of the attribute/property to get the value from
    :return: A json serializable value that is supposedly equivalent to the original value
    """
    val = getattr(model, name, None)
    if isinstance(val, datetime.datetime):
        if not val.tzinfo:
            val = val.replace(tzinfo=tz.tzlocal())
        val = val.isoformat()
    return val


def json_has_foreign(model, fname, is_single=False, is_list=False):
    """Check whether the model has the __json_*_foreign__ attribute used by :py:func:`model_to_json`
    AND that the field name is in the __json_*_foreign__ list/tuple.

    :param model: The model to check for __json_*_foreign__
    :param fname: The name of the foreign field
    :param is_single: Whether to also check in __json_single_foreign__
    :param is_list: Whether to also check in __json_list_foreign__
    :return: The boolean result of the check.
    """

    def foreign_check(attrname):
        for name in getattr(model, attrname, ()):
            if ":" in name:
                name, _ = model_to_json.name_split(name, 1)
            if fname == name:
                return True
        return False

    return foreign_check("__json_foreign__") or (is_single and foreign_check("__json_single_foreign__")) or\
        (is_list and foreign_check("__json_list_foreign__"))


def json_is_omitted(model, name):
    """Check whether field is set to be omitted in the model.

    :param model: The model to check for omission
    :param name: The name of the field
    :return: Whether field should be omitted.
    """
    return name in getattr(model, "__json_omit__", ())


def get_model_col(mcls, name):
    """Gets the SQLAlchemy db field in a model class with a given field name.

    :param mcls: The model class
    :param name: The field name
    :return: The SQLAlchemy field
    """
    if mcls is not None:
        col = getattr(mcls, name, None)
        if isinstance(col, attributes.InstrumentedAttribute):
            return col
    return None


def get_model_cols(mcls):
    """Gets the dict of field name and SQLAlchemy field from the model class

    :param mcls: The model class
    :return: A dict of {field_name:SQLAlchemy_field}
    """
    d = None
    if mcls is not None:
        mcls = inspect(mcls)
        d = {name: getattr(mcls, name, None) for name in mcls.columns_attrs.keys()}
    return d


def get_model_colnames(mcls):
    """Gets the list of column names from the model class

    :param mcls: The model class
    :return: The list of column names
    """
    d = None
    if mcls is not None:
        inspector = inspect(mcls)
        d = [name for name in inspector.column_attrs.keys()]
    return d


def get_model_pubcolnames(mcls):
    """Gets the list of public column names (doesn't start with '_') from the model class

    :param mcls: The model class
    :return: The list of public column names
    """
    d = None
    if mcls is not None:
        inspector = inspect(mcls)
        d = [name[1:] if name[0] == "_" and hasattr(mcls, name[1:]) else name for name in inspector.column_attrs.keys()]
    return d


def get_relationship_model(mcls, fname):
    """Gets the foreign model class of a relationship attribute in a model class.

    :param mcls: The model class to find the relationship's model
    :param fname: The name of the relationship attribute
    :return: The foreign model class of the relationship.
    """
    inspector = inspect(mcls)
    relprop = inspector.relationships.get(fname, None)
    if relprop is not None:
        return relprop.mapper.class_
    return None


def escape_like_char(s):
    """Escape the '%' wildcard char used by SQL LIKE

    :param s: The string to have the '%' char escaped
    :return: The escaped string
    """
    return s.replace("\\", "\\\\").replace("%", "\\%")


def get_search_filter(mcls, q, cname, search):
    """Generate a filter that searches with search term(s) given a field to search in.

    :param mcls: The model class to search in.
    :param q: The query object of the model class.
    :param cname: The field to search in.
    :param search: The search term(s). Terms can be separated by a space.
    :return: The updated query object with the joins applied if searching using foreign fields.
             The filter that can be used to search the terms provided.
             Note: you have to manually apply the filter to the query.
             e.g. q, fil = get_search_filter(mcls, q, cname, search)
             q = q.filter(fil)
    """
    if "." in cname:
        rel, cname = cname.split(".", 1)
        relation = getattr(mcls, rel)
        mcls = get_relationship_model(mcls, rel)
        q = q.outerjoin(relation).options(contains_eager(relation))

    if " " in search:
        keywords = search.split(" ")
        col = get_model_col(mcls, cname)
        fil = and_(*(col.like("%"+escape_like_char(word)+"%") for word in keywords if word != "")).self_group()
    else:
        search = "%"+escape_like_char(search)+"%"
        fil = get_model_col(mcls, cname).like(search)

    return q, fil


def get_search_filters(mcls, q, search):
    """Generate a list of filters that searches with search term(s).
    The function will look into the __crud_searchfield__ attribute of the model class to
    get a list of attributes to search in.

    :param mcls: The model class to search in.
    :param q: The query object of the model class.
    :param search: The search term(s). Terms can be separated by a space.
    :return: The updated query object with the joins applied if searching using foreign fields.
             The list of filters that can be used to search the terms provided.
             Note: you have to manually apply the filter to the query.
             e.g. q, fil = get_search_filter(mcls, q, cname, search)
             q = q.filter(_or(*fil))
    """
    filters = []
    for cname in getattr(mcls, "__crud_searchfield__", ()):
        q, f = get_search_filter(mcls, q, cname, search)
        filters.append(f)
    return q, filters


def put_optional(form, field):
    """A function used as a validator for WTForm's field.
    This function will stop the validation chain of an update if the field is missing from the form data.
    This will automatically invoke as long as the request's method is PUT.
    To manually flag wtform as a validation for a db update instead of an insert,
    set an attribute `__is_update__` in the wtform class to True.
    """
    # The docs for wtforms seems to be a little incorrect regarding field.raw_data
    # field.raw_data will contain an empty list even if it's key does not exists in the form data
    # field.raw_data will only be None if the entire form's data is None?
    if (request.method == "PUT" or getattr(form, "__is_update__", False)) and\
            (field.raw_data is None or field.data is None or (isinstance(field.raw_data, (tuple, list)) and not field.raw_data)):
        raise StopValidation()


def strip_nonitems(fdata, data):
    """Remove any keys in fdata that is not in data.
    IMPT: This function is used because the data from form validator contains keys that are not in the request body
    and assigns empty/None value to them. Therefore we have to remove keys that are not passed in (data=request.data).

    :param fdata: The dict containing keys to be removed.
    :param data: The dict where the keys of fdata should mirror.
    :return: The fdata dict with keys not in data removed.
    """
    loopdata = fdata.copy()
    for k in loopdata.iterkeys():
        if k not in data:
            del(fdata[k])
    return fdata


def _readonly_err():
    return jsonify(_readonly_err_dict())


def _readonly_err_dict():
    return {"success": False, "error": "Making modifications are not allowed"}


class NullSelectField(SelectField):
    def pre_validate(self, form):
        if not isinstance(self.raw_data, (tuple, list)) or self.raw_data:
            super(NullSelectField, self).pre_validate(form)
