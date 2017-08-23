# -*- coding: utf-8 -*-
__author__ = 'n2m'

from export import ExcelAPI


class MgoExcelAPI(ExcelAPI):
    model_is_dict = True

    def _get_models(self):
        return self.model.find(self.filter_by)

    # NOTE: once _get_models is retrieved, processing will be done off context.
    # So self.db, self.model will not work anymore.
    @classmethod
    def _transform_model(cls, m):
        return m

    @classmethod
    def _write_data(cls, sheet, rownum, fields, models, xls=None):
        numfields = len(fields)
        sheet_name = sheet.get_name()
        if len(sheet_name) > 28:
            sheet_name = sheet_name[0:28]
        sheet_num = 1

        for m in models:
            m = cls._transform_model(m)
            if m is None:
                continue

            for i in xrange(0, numfields):
                if "." in fields[i][0]:
                    sub = fields[i][0].split(".")
                    value = m
                    for s in sub:
                        if value:
                            if s.isdigit() and isinstance(value, (tuple, list)):
                                value = value[int(s)]
                            else:
                                value = value.get(s)
                        else:
                            value = ""
                            break
                else:
                    value = m.get(fields[i][0])
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


class MgoExcelArrayAPI(MgoExcelAPI):
    unwind = None

    def _get_models(self):
        unwind = "$" + self.unwind if isinstance(self.unwind, basestring) and self.unwind[0] != '$' else self.unwind
        filter_by = self.filter_by or {}
        aggset = [
            {"$unwind": unwind},
            {"$match": filter_by}
        ]
        cursor = self.model.collection.aggregate(aggset, allowDiskUse=True, cursor={})
        return cursor
