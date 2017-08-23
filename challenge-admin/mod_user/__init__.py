# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask.ext import restful
from flask import request
from rest import crud, export
from mod_auth import acl

admin_user = crud.CrudBlueprint('admin_user', __name__, model="user")


@admin_user.resource
class UserList(crud.ListAPI):
    method_decorators = [acl.requires_role("administrator")]


@admin_user.resource
class UserItem(crud.ItemAPI):
    method_decorators = [acl.requires_role("administrator")]


@admin_user.resource
class UserStatus(crud.ToggleAPI):
    method_decorators = [acl.requires_role("administrator")]
    toggle = "status"
    is_val = ("inactive", "active")


@admin_user.resource
class UserGuardAck(crud.ToggleAPI):
    method_decorators = [acl.requires_role("administrator")]
    toggle = "guardiansack"
    is_int = True


@admin_user.resource
class UserExport(export.ExcelAPI):
    method_decorators = [acl.requires_role("administrator")]
    sheet_name = "users"
    fields = [("id", "Id", 5),
              ("name", "Name", 25),
              ("firstname", "First Name", 20),
              ("lastname", "Last Name", 20),
              ("guardiansemail", "Guardian's Email", 40),
              ("points", "Points", 10),
              ("type", "Type", 11),
              ("schoolname", "School Code", 25),
              ("classname", "Class Name", 20),
              ("country", "Country", 20),
              ("createdate", "Created Date", 20),
              ("lastlogindate", "Last Login", 20),
              ("guardiansack", "Guardian's Acknowledge", 22)]


@admin_user.resource
class UserExportFull(export.ExcelAPI):
    sheet_name = "users"
    fields_u = [("id", "Id", 5),
                ("name", "Name", 25),
                ("firstname", "First Name", 20),
                ("lastname", "Last Name", 20),
                ("guardiansemail", "Guardian's Email", 40),
                ("points", "Points", 10),
                ("type", "Type", 11),
                ("schoolname", "School Code", 25),
                ("classname", "Class Name", 20),
                ("country", "Country", 20),
                ("createdate", "Created Date", 20),
                ("lastlogindate", "Last Login", 20),
                ("guardiansack", "Guardian's Acknowledge", 22),
                ("compldate", "Pre-Survey Date", 20),
                ("firstdate", "First Date", 20),
                ("lastdate", "Last Date", 20),
                ("hits", "Hits", 10),
                ("firstdate", "First Date", 20),
                ("lastdate", "Last Date", 20),
                ("hits", "Hits", 10),
                ("firstdate", "First Date", 20),
                ("lastdate", "Last Date", 20),
                ("hits", "Hits", 10),
                ("firstdate", "First Date", 20),
                ("lastdate", "Last Date", 20),
                ("hits", "Hits", 10),
                ("firstdate", "First Date", 20),
                ("lastdate", "Last Date", 20),
                ("hits", "Hits", 10),
                ("firstdate", "First Date", 20),
                ("lastdate", "Last Date", 20),
                ("hits", "Hits", 10),
                ("firstdate", "First Date", 20),
                ("lastdate", "Last Date", 20),
                ("hits", "Hits", 10),
                ("compldate", "Post-Survey Date", 20)]
    fields_pre = [("id", "Id", 5),
                  ("user.name", "Username", 25),
                  (None, "Q1", 5),
                  (None, "Q2", 10),
                  (None, "Q3", 5),
                  (None, "Q4", 5),
                  (None, "Q5", 8),
                  (None, "Q6", 5),
                  (None, "Part1-1", 8),
                  (None, "Part1-2", 8),
                  (None, "Part1-3", 8),
                  (None, "Part1-4", 8),
                  (None, "Part1-5", 8),
                  (None, "Part1-6", 8),
                  (None, "Part1-7", 8),
                  (None, "Part1-8", 8),
                  (None, "Part1-9", 8),
                  (None, "Part2-1", 8),
                  (None, "Part2-2", 8),
                  (None, "Part2-3", 8),
                  (None, "Part2-4", 8),
                  (None, "Part2-5", 8),
                  (None, "Part2-6", 8),
                  (None, "Part2-7", 8),
                  (None, "Part2-8", 8),
                  (None, "Part2-9", 8),
                  (None, "Part2-10", 8),
                  (None, "Part2-11", 8),
                  (None, "Part2-12", 8),
                  (None, "Part3-1", 8),
                  (None, "Part3-2", 8),
                  (None, "Part3-3", 8),
                  (None, "Part3-4", 8),
                  (None, "Part3-5", 8),
                  (None, "Part3-6", 8),
                  (None, "Part3-7", 8),
                  (None, "Part3-8", 8),
                  (None, "Part3-9", 8),
                  (None, "Part3-10", 8),
                  (None, "Part4-1", 8),
                  (None, "Part4-2", 8),
                  (None, "Part4-3", 8),
                  (None, "Part4-4", 8),
                  (None, "Part4-5", 8),
                  (None, "Part4-6", 8),
                  (None, "Part4-7", 8),
                  (None, "Part4-8", 8),
                  (None, "Part4-9", 8),
                  (None, "Part4-10", 8),
                  (None, "Part4-11", 8),
                  (None, "Part4-12", 8)]
    fields_post = [("id", "Id", 5),
                   ("user.name", "Username", 25),
                   (None, "Q1", 5),
                   (None, "Q2", 10),
                   (None, "Q3", 15),
                   (None, "Part1-1", 8),
                   (None, "Part1-2", 8),
                   (None, "Part1-3", 8),
                   (None, "Part1-4", 8),
                   (None, "Part1-5", 8),
                   (None, "Part1-6", 8),
                   (None, "Part1-7", 8),
                   (None, "Part1-8", 8),
                   (None, "Part1-9", 8),
                   (None, "Part2-1", 8),
                   (None, "Part2-2", 8),
                   (None, "Part2-3", 8),
                   (None, "Part2-4", 8),
                   (None, "Part2-5", 8),
                   (None, "Part2-6", 8),
                   (None, "Part2-7", 8),
                   (None, "Part2-8", 8),
                   (None, "Part2-9", 8),
                   (None, "Part2-10", 8),
                   (None, "Part2-11", 8),
                   (None, "Part2-12", 8),
                   (None, "Part3-1", 8),
                   (None, "Part3-2", 8),
                   (None, "Part3-3", 8),
                   (None, "Part3-4", 8),
                   (None, "Part3-5", 8),
                   (None, "Part3-6", 8),
                   (None, "Part3-7", 8),
                   (None, "Part3-8", 8),
                   (None, "Part3-9", 8),
                   (None, "Part3-10", 8),
                   (None, "Part4-1", 8),
                   (None, "Part4-2", 8),
                   (None, "Part4-3", 8),
                   (None, "Part4-4", 8),
                   (None, "Part4-5", 8),
                   (None, "Part4-6", 8),
                   (None, "Part4-7", 8),
                   (None, "Part4-8", 8),
                   (None, "Part4-9", 8),
                   (None, "Part4-10", 8),
                   (None, "Part4-11", 8),
                   (None, "Part4-12", 8),
                   (None, "Part5-1", 8),
                   (None, "Part5-2", 8),
                   (None, "Part5-3", 8),
                   (None, "Part5-4", 8)]
    u_sql = """SELECT u.id, u.name, u.firstname, u.lastname, u.guardiansemail, u.points, u.type,
    u.schoolname, u.classname, u.country, u.createdate, u.lastlogindate, u.guardiansack,
    pr.compldate as predate,
    r.firstdate as rfdate, r.lastdate as rldate, r.hits as rhits,
    e.firstdate as efdate, e.lastdate as eldate, e.hits as ehits,
    s.firstdate as sfdate, s.lastdate as sldate, s.hits as shits,
    p.firstdate as pfdate, p.lastdate as pldate, p.hits as phits,
    a.firstdate as afdate, a.lastdate as aldate, a.hits as ahits,
    c.firstdate as cfdate, c.lastdate as cldate, c.hits as chits,
    t.firstdate as tfdate, t.lastdate as tldate, t.hits as thits,
    po.compldate as postdate,
    pr.status as prstat, pr.id as preid, po.status as postat, po.id as postid
FROM users u
    LEFT JOIN users_mission r ON r.userid=u.id AND r.missionid=1
    LEFT JOIN users_mission e ON e.userid=u.id AND e.missionid=2
    LEFT JOIN users_mission s ON s.userid=u.id AND s.missionid=3
    LEFT JOIN users_mission p ON p.userid=u.id AND p.missionid=4
    LEFT JOIN users_mission a ON a.userid=u.id AND a.missionid=5
    LEFT JOIN users_mission c ON c.userid=u.id AND c.missionid=6
    LEFT JOIN users_mission t ON t.userid=u.id AND t.missionid=7
    LEFT JOIN users_survey pr ON pr.userid=u.id AND pr.status=-1 AND pr.surveyid=1
    LEFT JOIN users_survey po ON po.userid=u.id AND po.status=-1 AND po.surveyid=2;"""

    def __init__(self, *args, **kargs):
        super(UserExportFull, self).__init__(*args, **kargs)
        if "single" in request.args and request.args["single"]:
            self.sheet_id = "users-single"

    def _workexcel(self, xls, sheet_u):
        try:
            if self.sheet_id and self.sheet_id == "users-single":
                self._singlesheet(xls, sheet_u)
                return

            h_format = xls.add_format(self.header_format)
            write_col = self._write_col
            execute = self.db.engine.execute

            sheet_u.freeze_panes(2, 0)
            sheet_u.merge_range("O1:Q1", "iZ Radar", h_format)
            sheet_u.merge_range("R1:T1", "iZ Eyes", h_format)
            sheet_u.merge_range("U1:W1", "iZ Shout", h_format)
            sheet_u.merge_range("X1:Z1", "iZ Protect", h_format)
            sheet_u.merge_range("AA1:AC1", "iZ Ears", h_format)
            sheet_u.merge_range("AD1:AF1", "iZ Control", h_format)
            sheet_u.merge_range("AG1:AI1", "iZ Teleport", h_format)
            self._write_header(sheet_u, 1, self.fields_u, h_format)

            rownum = 2
            results = execute(self.u_sql)
            range_res = xrange(len(self.fields_u))
            for res in results:
                for i in range_res:
                    write_col(sheet_u, rownum, i, res[i])
                rownum += 1
            del results

            sheet_pre = xls.add_worksheet("pre-survey")
            sheet_pre.freeze_panes(1, 0)
            self._write_header(sheet_pre, 0, self.fields_pre, h_format)

            rownum = 1
            results = execute("SELECT u.id, u.name, s.id as sid FROM users u JOIN users_survey s ON s.userid=u.id AND s.status=-1 AND s.surveyid=1 ORDER BY s.userid;")
            for res in results:
                write_col(sheet_pre, rownum, 0, res[0])
                write_col(sheet_pre, rownum, 1, res[1])
                questions = execute("SELECT qns, ansnum, anstext FROM users_survey_answer WHERE usurveyid=%d ORDER BY qns;" % res[2])
                i = 2
                for q in questions:
                    value = str(q[1]) + ", " + q[2] if q[2] else q[1]
                    if q[0] == 4:
                        write_col(sheet_pre, rownum, i, 2 if q[1] & 1 else 1)
                        value = ""
                        if q[1] & 2:
                            value += "1,"
                        if q[1] & 4:
                            value += "2,"
                        if q[1] & 8:
                            value += "3,"
                        if q[1] & 16:
                            value += "4,"
                        if value:
                            value = value[:-1]
                        i += 1
                    write_col(sheet_pre, rownum, i, value)
                    i += 1
                rownum += 1

            del results

            sheet_post = xls.add_worksheet("post-survey")
            sheet_post.freeze_panes(1, 0)
            self._write_header(sheet_post, 0, self.fields_post, h_format)

            rownum = 1
            results = execute("SELECT u.id, u.name, s.id as sid FROM users u JOIN users_survey s ON s.userid=u.id AND s.status=-1 AND s.surveyid=2 ORDER BY s.userid;")
            for res in results:
                write_col(sheet_post, rownum, 0, res[0])
                write_col(sheet_post, rownum, 1, res[1])
                questions = execute("SELECT qns, ansnum, anstext FROM users_survey_answer WHERE usurveyid=%d ORDER BY qns;" % res[2])
                i = 2
                for q in questions:
                    value = str(q[1]) + ", " + q[2] if q[2] else q[1]
                    if q[0] == 1:
                        write_col(sheet_post, rownum, i, 2 if q[1] & 1 else 1)
                        value = ""
                        if q[1] & 2:
                            value += "1,"
                        if q[1] & 4:
                            value += "2,"
                        if q[1] & 8:
                            value += "3,"
                        if q[1] & 16:
                            value += "4,"
                        if value:
                            value = value[:-1]
                        i += 1
                    elif q[0] == 2:
                        value = ""
                        if q[1] & 1:
                            value += "1,"
                        if q[1] & 2:
                            value += "2,"
                        if q[1] & 4:
                            value += "3,"
                        if q[1] & 8:
                            value += "4,"
                        if q[1] & 16:
                            value += "5,"
                        if q[1] & 32:
                            value += "6,"
                        if value:
                            value = value[:-1]
                        if q[2]:
                            value = value + ", " + q[2]
                    write_col(sheet_post, rownum, i, value)
                    i += 1
                rownum += 1

            del results
            xls.close()
            self._workcomplete()
        except Exception:
            self._workerror()

    def _singlesheet(self, xls, sheet_u):
        h_format = xls.add_format(self.header_format)
        write_col = self._write_col
        execute = self.db.engine.execute

        sheet_u.freeze_panes(2, 0)
        sheet_u.merge_range("O1:Q1", "iZ Radar", h_format)
        sheet_u.merge_range("R1:T1", "iZ Eyes", h_format)
        sheet_u.merge_range("U1:W1", "iZ Shout", h_format)
        sheet_u.merge_range("X1:Z1", "iZ Protect", h_format)
        sheet_u.merge_range("AA1:AC1", "iZ Ears", h_format)
        sheet_u.merge_range("AD1:AF1", "iZ Control", h_format)
        sheet_u.merge_range("AG1:AI1", "iZ Teleport", h_format)
        sheet_u.merge_range("AK1:CG1", "Pre Survey", h_format)
        sheet_u.merge_range("CH1:EE1", "Post Survey", h_format)
        self._write_header(sheet_u, 1, self.fields_u + self.fields_pre[2:] + self.fields_post[2:], h_format)

        rownum = 2
        results = execute(self.u_sql)
        fields_pre_start = len(self.fields_u)
        fields_post_start = fields_pre_start + len(self.fields_pre) - 2
        range_res = xrange(fields_pre_start)
        for res in results:
            for i in range_res:
                write_col(sheet_u, rownum, i, res[i])
            if res[36] == -1:
                self._write_pre(sheet_u, res[37], rownum, fields_pre_start)
            if res[38] == -1:
                self._write_post(sheet_u, res[39], rownum, fields_post_start)
            rownum += 1
        del results

        xls.close()
        self._workcomplete()

    def _write_pre(self, sheet_pre, preid, rownum, i):
        execute = self.db.engine.execute
        write_col = self._write_col
        questions = execute("SELECT qns, ansnum, anstext FROM users_survey_answer WHERE usurveyid=%d ORDER BY qns;" % preid)

        for q in questions:
            value = str(q[1]) + ", " + q[2] if q[2] else q[1]
            if q[0] == 4:
                write_col(sheet_pre, rownum, i, 2 if q[1] & 1 else 1)
                value = ""
                if q[1] & 2:
                    value += "1,"
                if q[1] & 4:
                    value += "2,"
                if q[1] & 8:
                    value += "3,"
                if q[1] & 16:
                    value += "4,"
                if value:
                    value = value[:-1]
                i += 1
            write_col(sheet_pre, rownum, i, value)
            i += 1

    def _write_post(self, sheet_post, postid, rownum, i):
        execute = self.db.engine.execute
        write_col = self._write_col
        questions = execute("SELECT qns, ansnum, anstext FROM users_survey_answer WHERE usurveyid=%d ORDER BY qns;" % postid)

        for q in questions:
            value = str(q[1]) + ", " + q[2] if q[2] else q[1]
            if q[0] == 1:
                write_col(sheet_post, rownum, i, 2 if q[1] & 1 else 1)
                value = ""
                if q[1] & 2:
                    value += "1,"
                if q[1] & 4:
                    value += "2,"
                if q[1] & 8:
                    value += "3,"
                if q[1] & 16:
                    value += "4,"
                if value:
                    value = value[:-1]
                i += 1
            elif q[0] == 2:
                value = ""
                if q[1] & 1:
                    value += "1,"
                if q[1] & 2:
                    value += "2,"
                if q[1] & 4:
                    value += "3,"
                if q[1] & 8:
                    value += "4,"
                if q[1] & 16:
                    value += "5,"
                if q[1] & 32:
                    value += "6,"
                if value:
                    value = value[:-1]
                if q[2]:
                    value = value + ", " + q[2]
            write_col(sheet_post, rownum, i, value)
            i += 1


api = restful.Api(admin_user)
api.add_resource(UserList, '/', endpoint='users')
api.add_resource(UserItem, '/item/<int:itemid>', endpoint='user')
api.add_resource(UserStatus, '/status/<int:itemid>', endpoint='status')
api.add_resource(UserGuardAck, '/guardack/<int:itemid>', endpoint='guardack')
api.add_resource(UserExport, '/export', endpoint='export')
api.add_resource(UserExportFull, '/exportfull', endpoint='exportfull')