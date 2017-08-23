__author__ = 'n2m'

from flask import jsonify
from flask.ext.restful import Api, Resource, reqparse
from rest import crudmgo, exportmgo
from mod_auth import acl
import datetime
from dateutil import tz, relativedelta


admin_stats = crudmgo.CrudMgoBlueprint("admin_stats", __name__, model="IZHero")
admin_stats_school = crudmgo.CrudMgoBlueprint("admin_stats_school", __name__, model="Country")
izhero_initdate = datetime.datetime(2015, 2, 1, 0, 0, 0, 0, tz.tzlocal())
onemonth = relativedelta.relativedelta(months=1)
oneday = relativedelta.relativedelta(days=1)
onehour = relativedelta.relativedelta(hours=1)


@admin_stats.resource
class UserStats(Resource):
    method_decorators = [acl.requires_role("administrator")]
    db = None
    model = None

    def get(self):
        pr = reqparse.RequestParser()
        pr.add_argument("year", type=int, store_missing=False)
        pr.add_argument("month", type=int, store_missing=False)
        pr.add_argument("day", type=int, store_missing=False)
        pr.add_argument("loggedin", type=int, store_missing=False)
        args = pr.parse_args()
        today = datetime.datetime.now(tz.tzlocal())

        year, month, day = args.get("year", today.year), args.get("month", 1), args.get("day", 1)
        start = datetime.datetime(year, month, day, 0, 0, 0, 0, tz.tzlocal())

        if start < izhero_initdate:
            start = izhero_initdate
            year = 2015
            month = 2
            day = 1
        elif start > today:
            start = datetime.datetime(today.year, today.month, 1, 0, 0, 0, 0, tz.tzlocal())
            year = today.year
            month = today.month
            day = 1

        end = izhero_initdate + onemonth
        stats = {"months": [], "days": [], "hours": []}
        filter_by = {"lastlogin": {"$ne": None}} if args.get("loggedin") and args["loggedin"] == 1 else {}

        if "month" not in args and "day" not in args:
            while start < today:
                filter_by["created"] = {"$gte": start, "$lt": end}
                stats["months"].append({
                    "year": start.year,
                    "month": start.month,
                    "count": self.model.find(filter_by).count()
                })
                start = end
                end = end + onemonth

        if "day" in args:
            start = datetime.datetime(year, month, day, 0, 0, 0, 0, tz.tzlocal())
            end = start + onehour
            till = start + oneday
            if till > today:
                till = today

            while start < till:
                filter_by["created"] = {"$gte": start, "$lt": end}
                stats["hours"].append({
                    "year": year,
                    "month": month,
                    "day": day,
                    "hour": start.hour,
                    "count": self.model.find(filter_by).count()
                })
                start = end
                end = end + onehour

        else:
            start = datetime.datetime(year, month if "month" in args else 12, 1, 0, 0, 0, 0, tz.tzlocal())
            if start > today:
                start = datetime.datetime(year, today.month, 1, 0, 0, 0, 0, tz.tzlocal())
            end = start + oneday
            till = start + onemonth
            if till > today:
                till = today

            while start < till:
                filter_by["created"] = {"$gte": start, "$lt": end}
                stats["days"].append({
                    "year": year,
                    "month": start.month,
                    "day": start.day,
                    "count": self.model.find(filter_by).count()
                })
                start = end
                end = end + oneday

        return jsonify(stats)


@admin_stats_school.resource
class SchoolUserStats(crudmgo.ListArrayAPI):
    method_decorators = [acl.requires_role("administrator")]
    unwind = "schools"
    order = "schools"
    db = None
    model = None

    def get(self):
        pr = reqparse.RequestParser()
        pr.add_argument("country", type=unicode, store_missing=False)
        pr.add_argument("school", type=unicode, store_missing=False)
        pr.add_argument("year", type=int, store_missing=False)
        pr.add_argument("month", type=int, store_missing=False)
        pr.add_argument("day", type=int, store_missing=False)
        pr.add_argument("loggedin", type=int, store_missing=False)
        args = pr.parse_args()
        cname = args.get("country", "Singapore")
        self.filter_by = {"name": cname}
        d = {}

        if args.get("school"):
            today = datetime.datetime.now(tz.tzlocal())
            year, month, day = args.get("year", today.year), args.get("month", 1), args.get("day", 1)

            filter_by = {"country": cname, "school": args["school"]}
            if args.get("loggedin"):
                filter_by["lastlogin"] = {"$ne": None}

            if "day" in args:
                d["hours"] = []
                start = datetime.datetime(year, month, day, 0, 0, 0, 0, tz.tzlocal())
                end = start + onehour
                till = start + oneday
                if till > today:
                    till = today

                while start < till:
                    filter_by["created"] = {"$gte": start, "$lt": end}
                    d["hours"].append({
                        "year": year,
                        "month": month,
                        "day": day,
                        "hour": start.hour,
                        "count": self.db["IZHero"].find(filter_by).count()
                    })
                    start = end
                    end = end + onehour
            elif "month" in args:
                d["days"] = []
                start = datetime.datetime(year, month, 1, 0, 0, 0, 0, tz.tzlocal())
                if start > today:
                    start = datetime.datetime(year, today.month, 1, 0, 0, 0, 0, tz.tzlocal())
                end = start + oneday
                till = start + onemonth
                if till > today:
                    till = today

                while start < till:
                    filter_by["created"] = {"$gte": start, "$lt": end}
                    d["days"].append({
                        "year": year,
                        "month": start.month,
                        "day": start.day,
                        "count": self.db["IZHero"].find(filter_by).count()
                    })
                    start = end
                    end = end + oneday
            else:
                d["months"] = []
                start = datetime.datetime(year, month, day, 0, 0, 0, 0, tz.tzlocal())
                if start < izhero_initdate:
                    start = izhero_initdate
                elif start > today:
                    start = datetime.datetime(today.year, today.month, 1, 0, 0, 0, 0, tz.tzlocal())
                end = izhero_initdate + onemonth

                while start < today:
                    filter_by["created"] = {"$gte": start, "$lt": end}
                    d["months"].append({
                        "year": start.year,
                        "month": start.month,
                        "count": self.db["IZHero"].find(filter_by).count()
                    })
                    start = end
                    end = end + onemonth
        else:
            schools, pages, count = self._getcursorwithcount()
            d["items"] = []
            d["pages"] = pages
            d["count"] = count
            for s in schools:
                o = {"schools": s["schools"],
                     "count": self.db["IZHero"].find({"country": cname, "school": s["schools"]}).count(),
                     "count_loggedin": self.db["IZHero"].find({"country": cname, "school": s["schools"],
                                                               "lastlogin": {"$ne": None}}).count(),
                     "points": 0, "donated": 0}

                agg = self.db["IZHero"].collection.aggregate([{"$match": {"country": cname, "school": s["schools"]}},
                                                              {"$group": {"_id": None,
                                                                          "points": {"$sum": "$points"},
                                                                          "donated": {"$sum": "$donated"}}}])
                if agg.get("result") and len(agg["result"]) > 0:
                    o["points"] = int(agg["result"][0].get("points", 0))
                    o["donated"] = int(agg["result"][0].get("donated", 0))

                d["items"].append(o)

        return jsonify(d)


@admin_stats_school.resource
class SchoolUserStatsExport(exportmgo.MgoExcelArrayAPI):
    method_decorators = [acl.requires_role("administrator")]
    sheet_name = "School Users"
    unwind = "schools"
    cname = ""
    fields = [("schools", "School", 40),
              ("count", "No. Users", 15),
              ("count_loggedin", "No. Users (Logged In)", 30),
              ("points", "Total iZPs", 20),
              ("donated", "Total Donations", 20)]
    schools = []

    def __init__(self, *args, **kargs):
        super(SchoolUserStatsExport, self).__init__(*args, **kargs)
        pr = reqparse.RequestParser()
        pr.add_argument("country", type=unicode, store_missing=False)
        args = pr.parse_args()
        self.cname = args.get("country", "Singapore")

        self.sheet_name = self.__class__.sheet_name + " - " + self.cname
        self.filter_by = {"name": self.cname}
        self._models()

    def _models(self):
        cursor = super(SchoolUserStatsExport, self)._get_models()
        schools = []

        for s in cursor:
            o = {"schools": s["schools"],
                 "count": self.db["IZHero"].find({"country": self.cname, "school": s["schools"]}).count(),
                 "count_loggedin": self.db["IZHero"].find({"country": self.cname, "school": s["schools"],
                                                           "lastlogin": {"$ne": None}}).count(),
                 "points": 0, "donated": 0}

            agg = self.db["IZHero"].collection.aggregate([{"$match": {"country": self.cname, "school": s["schools"]}},
                                                          {"$group": {"_id": None,
                                                                      "points": {"$sum": "$points"},
                                                                      "donated": {"$sum": "$donated"}}}])
            if agg.get("result") and len(agg["result"]) > 0:
                o["points"] = int(agg["result"][0].get("points", 0))
                o["donated"] = int(agg["result"][0].get("donated", 0))

            schools.append(o)
        self.schools = schools

    def _get_models(self):
        return self.schools


apistats = Api(admin_stats)
apistats.add_resource(UserStats, "", endpoint="stats_users")
apistats.add_resource(UserStats, "/", endpoint="stats_users_slash")
apistats = Api(admin_stats_school)
apistats.add_resource(SchoolUserStats, "", endpoint="stats_schools")
apistats.add_resource(SchoolUserStats, "/", endpoint="stats_schools_slash")
apistats.add_resource(SchoolUserStatsExport, "/export", endpoint="stats_schools_export")
