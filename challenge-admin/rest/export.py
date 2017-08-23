# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import send_file, jsonify, abort, request
from flask.ext.restful import Resource
from xlsxwriter.workbook import Workbook
from datetime import datetime, timedelta
from dateutil import tz
import random
import string
import threading
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

elock = threading.Lock()
eworking = {}


class StringIONoClose(object):
    strio = None

    def __init__(self, strio):
        self.strio = strio

    def __iter__(self):
        return self

    def next(self):
        return self.strio.next()

    def isatty(self):
        return self.strio.isatty()

    def tell(self):
        return self.strio.tell()

    def seek(self, pos, mode=0):
        self.strio.seek(pos, mode)

    def read(self, n):
        return self.strio.read(n)

    def readline(self, length=None):
        return self.strio.readline(length)

    def readlines(self, sizehint=0):
        return self.strio.readlines(sizehint)

    def flush(self):
        self.strio.flush()

    def getvalue(self):
        return self.strio.getvalue()

    def close(self):
        pass

    def _close(self):
        self.strio.close()


def removework(fqn):
    with elock:
        wk = eworking.pop(fqn)

    if wk is not None and wk["status"] == 2:
        wk["output"].close()


def errorwork(fqn):
    with elock:
        wk = eworking.get(fqn)
        if wk is not None:
            wk["status"] = -1
            wk["output"].close()


class ExcelAPI(Resource):
    db = None
    model = None
    filter_by = None
    #: a list of tuple containing (column_name, excel_header/firstrow_value, excel_column_width)
    fields = [("id", "Id", 5)]
    sheet_name = "worksheet"
    sheet_id = None
    date_format = "d mmm yyyy, hh:mm:ss"
    header_format = {"bold": 1, "align": "center", "fg_color": "#FFFF00", "border": 1}
    modellist = None

    def _create_excel(self):
        output = StringIO.StringIO()
        xls = Workbook(output, {"default_date_format": self.date_format})
        sheet_name = self.sheet_name.strip()
        if len(sheet_name) > 31:
            sheet_name = sheet_name[0:31]
        sheet = xls.add_worksheet(sheet_name)
        return xls, sheet, output

    def _getfqn(self):
        return self.__class__.__module__ + '.' + self.__class__.__name__ + '.' + (self.sheet_id or self.sheet_name)

    def post(self):
        fqn = self._getfqn()

        with elock:
            isworking = eworking.get(fqn, {"status": 0})
            if isworking["status"] == 2:
                isworking["expire"].cancel()
                isworking["expire"] = threading.Timer(300.0, removework, (fqn,))
                isworking["expire"].start()
                return jsonify({"working": False,
                                "exid": isworking["exid"]})
            elif isworking["status"] == 1:
                return jsonify({"working": True})
            elif isworking["status"] == -1:
                del eworking[fqn]
                abort(500)

            xls, sheet, output = self._create_excel()
            rand_id = ''.join(random.sample(string.letters+string.digits, 24))
            eworking[fqn] = {
                "status": 1,
                "exid": rand_id,
                "expire": None,
                "output": output
            }

        self.modellist = self._get_models()
        threading.Thread(target=self._workexcel, args=(xls, sheet)).start()
        return jsonify({"working": True})

    def _workexcel(self, xls, sheet):
        try:
            sheet.freeze_panes(1, 0)
            self._write_header(sheet, 0, self.fields, xls.add_format(self.header_format))
            self._write_data(sheet, 1, self.fields, self.modellist, xls)
            xls.close()
            self._workcomplete()
        except Exception:
            self._workerror()
            try:
                xls.close()
            except Exception:
                pass

    def _workcomplete(self):
        with elock:
            fqn = self._getfqn()
            isworking = eworking.get(fqn)
            if isworking is not None and not isworking["output"].closed:
                isworking["status"] = 2
                isworking["expire"] = threading.Timer(300.0, removework, (fqn,))
                isworking["expire"].start()

    def _workerror(self):
        errorwork(self._getfqn())

    def get(self):
        if not request.args or request.args.get("exid") is None:
            abort(404)

        exid = request.args.get("exid")
        output = None
        fqn = self._getfqn()

        with elock:
            isworking = eworking.get(fqn, {"status": 0})
            if isworking["status"] == 2 and isworking["exid"] == exid:
                isworking["expire"].cancel()
                isworking["expire"] = threading.Timer(300.0, removework, (fqn,))
                isworking["expire"].start()
                output = isworking["output"]
            elif isworking["status"] == -1:
                del eworking[fqn]

        if output is None:
            abort(404)

        return self._send_excel(output, self.sheet_name)

    def _get_models(self):
        return self.model.query.filter_by(**self.filter_by).all() if self.filter_by else self.model.query.all()

    @staticmethod
    def _send_excel(output, sheet_name):
        output.seek(0)
        return send_file(StringIONoClose(output), attachment_filename=sheet_name + ".xlsx", as_attachment=True)

    @staticmethod
    def _write_header(sheet, row, fields, h_format):
        numfields = len(fields)
        for i in xrange(0, numfields):
            sheet.set_column(i, i, fields[i][2])
            sheet.write_string(row, i, fields[i][1], h_format)

    @classmethod
    def _write_data(cls, sheet, rownum, fields, models, xls=None):
        numfields = len(fields)
        sheet_name = sheet.get_name()
        if len(sheet_name) > 28:
            sheet_name = sheet_name[0:28]
        sheet_num = 1

        for m in models:
            for i in xrange(0, numfields):
                value = getattr(m, fields[i][0])
                cls._write_col(sheet, rownum, i, value)
            rownum += 1

            if rownum > 1048575:
                if xls is not None:
                    sheet_num += 1
                    nm = sheet_name + ' ' + str(sheet_num)
                    sheet = xls.add_worksheet(nm)
                    cls._write_header(sheet, 0, fields, xls.add_format(cls.header_format))
                    rownum = 1
                else:
                    break

    @staticmethod
    def _write_col(sheet, row, col, value):
        if isinstance(value, (str, unicode)):
            sheet.write_string(row, col, value)
        elif isinstance(value, (int, long, float)):
            sheet.write_number(row, col, value)
        elif isinstance(value, datetime):
            try:
                if value.tzinfo:
                    value = value.astimezone(tz.tzlocal())
                    value = value.replace(tzinfo=None)
                sheet.write_datetime(row, col, value)
            except Exception:
                return
        elif value is not None:
            sheet.write_string(row, col, str(value))