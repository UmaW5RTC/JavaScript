# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask.ext.restful import Api, reqparse
from rest import crudmgo, exportmgo
from mod_auth import acl


admin_izmission = crudmgo.CrudMgoBlueprint("admin_izmission", __name__, model="DqUserMission")


def get_zone(m):
    return __missions.get(m, (None, None))[1]


def get_mission(m):
    return __missions.get(m, (None, None))[0]


@admin_izmission.resource
class IZMissionStartExport(exportmgo.MgoExcelAPI):
    method_decorators = [acl.requires_role("administrator")]
    sheet_name = "Mission (Start)"
    fields = [("username", "Username", 30),
              ("started", "Start Date/Time", 20),
              ("zone", "Zone", 10),
              ("mission", "Mission", 50),
              ("started", "Created Date", 20),
              ("_id", "ID", 30)]

    def _get_models(self):
        models = list(self.model.find(self.filter_by).sort("userid", 1))
        curuser = None
        for m in models:
            m["username"] = None
            if not curuser or curuser["_id"] != m.get("userid"):
                curuser = self.db["IZHero"].collection.find_one({"_id": m["userid"]}, ["username"])
                if not curuser:
                    continue
            m["username"] = curuser["username"]
        return models

    @classmethod
    def _transform_model(cls, m):
        if not m["username"]:
            return None

        mission_name = get_mission(m.get("mission"))
        if not mission_name:
            return None

        zone_name = get_zone(m.get("mission"))

        d = {
            "username": m["username"],
            "started": m.get("started"),
            "zone": zone_name,
            "mission": mission_name,
            "_id": m["_id"]
        }
        return d


@admin_izmission.resource
class IZMissionSlideExport(exportmgo.MgoExcelAPI):
    method_decorators = [acl.requires_role("administrator")]
    sheet_name = "Mission Slide"
    fields = [("username", "Username", 30),
              ("time", "Start Date/Time", 20),
              ("zone", "Zone", 10),
              ("mission", "Mission", 50),
              ("name", "Slide", 20),
              ("started", "Created Date", 20),
              ("_id", "ID", 30)]

    def _get_models(self):
        models = []
        cursor = self.model.find(self.filter_by).sort("userid", 1)
        curuser = None
        for m in cursor:
            if not isinstance(m.get("checkpoint"), list) or len(m["checkpoint"]) == 0:
                continue

            m["username"] = None
            if not curuser or curuser["_id"] != m.get("userid"):
                curuser = self.db["IZHero"].collection.find_one({"_id": m["userid"]}, ["username"])
                if not curuser:
                    continue
            m["username"] = curuser["username"]
            for c in m["checkpoint"]:
                models.append({
                    "username": curuser["username"],
                    "time": c["time"],
                    "mission": m.get("mission"),
                    "name": c["name"],
                    "started": m.get("started"),
                    "_id": m["_id"],
                })
        return models

    @classmethod
    def _transform_model(cls, m):
        if not m["username"]:
            return None

        mission_name = get_mission(m.get("mission"))
        if not mission_name:
            return None

        m["zone"] = get_zone(m.get("mission"))
        m["mission"] = mission_name
        return m


@admin_izmission.resource
class IZMissionCompleteExport(exportmgo.MgoExcelAPI):
    method_decorators = [acl.requires_role("administrator")]
    sheet_name = "Mission (Complete)"
    fields = [("username", "Username", 30),
              ("completed", "Complete Date/Time", 20),
              ("zone", "Zone", 10),
              ("mission", "Mission", 50),
              ("started", "Created Date", 20),
              ("_id", "ID", 30)]
    filter_by = {"completed": {"$ne": None}}

    def _get_models(self):
        models = list(self.model.find(self.filter_by).sort("userid", 1))
        curuser = None
        for m in models:
            m["username"] = None
            if not curuser or curuser["_id"] != m.get("userid"):
                curuser = self.db["IZHero"].collection.find_one({"_id": m["userid"]}, ["username"])
                if not curuser:
                    continue
            m["username"] = curuser["username"]
        return models

    @classmethod
    def _transform_model(cls, m):
        if not m["username"]:
            return None

        mission_name = get_mission(m.get("mission"))
        if not mission_name:
            return None

        zone_name = get_zone(m.get("mission"))

        d = {
            "username": m["username"],
            "completed": m.get("completed"),
            "zone": zone_name,
            "mission": mission_name,
            "started": m.get("started"),
            "_id": m["_id"]
        }
        return d


@admin_izmission.resource
class IZMissionLikeExport(exportmgo.MgoExcelAPI):
    method_decorators = [acl.requires_role("administrator")]
    sheet_name = "Mission (Like)"
    fields = [("username", "Username", 30),
              ("completed", "Date/Time", 20),
              ("zone", "Zone", 10),
              ("mission", "Mission", 50),
              ("like", "Like/Dislike", 10),
              ("started", "Created Date", 20),
              ("_id", "ID", 30)]
    filter_by = {"completed": {"$ne": None}, "meta.like": {"$ne": None}}

    def _get_models(self):
        models = list(self.model.find(self.filter_by).sort("userid", 1))
        curuser = None
        for m in models:
            m["username"] = None
            if not curuser or curuser["_id"] != m.get("userid"):
                curuser = self.db["IZHero"].collection.find_one({"_id": m["userid"]}, ["username"])
                if not curuser:
                    continue
            m["username"] = curuser["username"]
        return models

    @classmethod
    def _transform_model(cls, m):
        if not m["username"]:
            return None

        mission_name = get_mission(m.get("mission"))
        if not mission_name:
            return None

        zone_name = get_zone(m.get("mission"))

        d = {
            "username": m["username"],
            "completed": m.get("completed"),
            "zone": zone_name,
            "mission": mission_name,
            "like": "Like" if isinstance(m.get("meta"), dict) and m["meta"].get("like") else "Dislike",
            "started": m.get("started"),
            "_id": m["_id"]
        }
        return d


api = Api(admin_izmission)
api.add_resource(IZMissionStartExport, '/export_start', endpoint='export_start')
api.add_resource(IZMissionSlideExport, '/export_slide', endpoint='export_slide')
api.add_resource(IZMissionCompleteExport, '/export_complete', endpoint='export_complete')
api.add_resource(IZMissionLikeExport, '/export_like', endpoint='export_like')

__missions = {
    'izpillars': ('DQ HEROES are Digital Leaders!', 1),
    'e0': ('The Beginning', 1),
    'pretest': ('What Type of Digital Leader are You?', 1),
    'digileader': ('Be a Digital Leader', 1),
    'digiworld': ('Digital Leaders in the Digital World', 1),
    'e1_1': ('The DQ HERO Chip', 1),
    'multask': ('Controlling Multi-tasking', 1),
    'e1_3': ('The Bump', 1),
    'gameaddict': ('Preventing Game Addiction', 1),
    'e1_4': ('One Bad Message', 1),
    'e1_5': ('Too Much Game Time', 1),
    'checkscreen': ('Harmful Effects of Excessive Screen Time', 1),
    'selfcontrol': ('Self-Control in Digital Use', 1),
    'balancescreen': ('Balancing Screen Time', 1),
    'e1_7': ('Gone', 1),
    'mediarules': ('Family Media Rule', 1),
    'priorities': ('Managing Time and Priorities', 1),
    'screentimebadge': ('Screen Time Quiz', 1),
    'e2_1': ('Left Behind', 2),
    'pinfo': ('Personal Information', 2),
    'snsprivacy': ('Keeping Privacy on Social Media', 2),
    'protectinfo': (u'Protecting Others’ Privacy', 2),
    'spinfo': ('Internet Privacy Rights', 2),
    'privacybadge': ('Privacy Quiz', 2),
    'e2_3': ('Lu Under Pressure', 3),
    'detectbully': ('Detecting Cyberbullying', 3),
    'cyberbully': ('Defining Cyberbullying', 3),
    'bullytypes': ('Identifying Types of Cyberbullying', 3),
    'involvebully': ('Being Involved in Cyberbullying Unknowingly', 3),
    'noretaliate': ('Diffusing a Cyberbullying Situation', 3),
    'e2_4': ('Viral Virus', 3),
    'dealbully': ('Dealing with Cyberbullying', 3),
    'trustedadults': ('Who are My Trusted Adults', 3),
    'seekhelp': ('When to Seek Help', 3),
    'cyberbullyingbadge': ('Cyberbullying Quiz', 3),
    'e2_5': ('Here with You', 4),
    'insidenet': ('How Does the Internet Work?', 4),
    'e3_1': ('Wake Up!', 4),
    'goldenrule': ('Digital Leader Creed', 4),
    'globalcitizens': ('Being a Global Citizen', 4),
    'e3_2': ('The Calling', 4),
    'strength': (u'What’s My Dream?', 4),
    'e3_3': ('RAZ. The TITAN', 4),
    'onoffline': ('Congruent Online and Offline Identities', 4),
    'persona': ('Integrity of Online Persona', 4),
    'digitalcitizensbadge': ('Digital Citizen Quiz', 4),
    'e3_4': (u'Guardian’s Gates', 5),
    'digifootprint': ('What is Digital Footprint?', 5),
    'footprintpinfo': ('Digital Footprints Reveal Personal Info', 5),
    'persistfootprint': ('Persistent Digital Footprints', 5),
    'digirep': ('Digital Footprint Impacts Digital Reputation', 5),
    'confootprint': ('Real Life Consequences of Digital Footprints', 5),
    'stopthinkconnect': ('Stop. Think. Connect.', 5),
    'digitalfootprintbadge': ('Digital Footprint Quiz', 5),
    'e4_1': ('Cloak of Silence and Eyes of Detection', 6),
    'createpwd': ('Creating Strong Passwords', 6),
    'pwdsafe': ('Keeping Passwords Safe', 6),
    'spamscam': ('Managing SPAM and SCAM', 6),
    'detectphish': ('Managing Phishing', 6),
    'mobilesafety': ('Observing Mobile Security', 6),
    'securitybadge': ('Digital Security Quiz', 6),
    'e4_2': ('Blocker Shield and Iron Will', 7),
    'friendbehavior': ('Who Do You Meet Online', 7),
    'onlinefriends': ('Who are Online Friends?', 7),
    'stranger': ('The 12 Stranger Alerts ', 7),
    'violentcontent': ('How to Avoid Violent Content', 7),
    'inapprocontent': ('What is Inappropriate Content?', 7),
    'contentcritique': ('How to Content Critique', 7),
    'truefalse': ('True vs. False Info', 7),
    'criticalthinkingbadge': ('Critical Thinking Quiz', 7),
    'e4_3': ('Failed', 8),
    'speakup': ('Courage to Speak Up', 8),
    'stander': ('By-standers vs. Up-standers', 8),
    'e4_4': (u'A Titan’s Sacrifice', 8),
    'e5_1': (u'New Heart’s Training', 8),
    'e5_2': ('Something in Common', 8),
    'digiempathy': ('Listening with Empathy Online', 8),
    'speakempathy': ('Speak Up with Empathy', 8),
    'e5_3': ('Getting It Right', 8),
    'empathyfriends': ('Empathy for Cyber Victims', 8),
    'avoidjudging': (u'Don’t be Judgemental Online', 8),
    'e5_4': ('The DQ HERO', 8),
    'empathybadge': ('Digital Empathy Quiz', 8)
}
