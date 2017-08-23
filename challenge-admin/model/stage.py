
# -*- coding: utf-8 -*-
__author__ = 'n2m'

from rest import crudmgo
from bson import ObjectId
from mod_auth import current_session, current_user
from flask import current_app
import datetime


class Stage(crudmgo.RootDocument):
    __collection__ = "izmissions"

    structure = {
        "stage": int,
        "name": basestring,
        "missions": [{
            "name": basestring,
            "parts": [],
            "group": bool,
            "prereq": [],
            "drawing": {
                "message": basestring,
                "sticker": basestring
            },
            "rewards": {
                "points": int,
                "coins": int
            },
            "stats": {
                "hits": int,
                "views": int
            },
            "modified": [{
                "by": ObjectId,
                "on": datetime.datetime
            }]
        }],
        "video": {
            "intro": basestring
        },
        "comic": basestring
    }

    indexes = [
        {"fields": ["stage", "name"]}
    ]
    required = ["name", "stage"]


class Stager(object):
    stage_num = 0
    progression = None
    untrack = ["star"]

    @classmethod
    def post(cls, mission, sub):
        mission = mission.lower()
        if mission not in cls.progression:
            return 0, 0

        user = current_user._get_current_object()

        if not user["progress"] or not user["progress"][0]:
            return 0, 0

        if len(user["progress"]) < (cls.stage_num + 1):
            for _ in xrange((cls.stage_num + 1) - len(user["progress"])):
                user["progress"].append({})

        track_sub = False
        sub_index = 0

        if cls.progression[mission]["sub"]:
            if isinstance(cls.progression[mission]["rewards"][0], (tuple, list)):
                if sub not in cls.progression[mission]["sub"]:
                    return 0, 0
                sub_index = cls.progression[mission]["sub"].index(sub)
                track_sub = True
            else:
                stage_mission = "stage" + str(cls.stage_num) + "-" + mission
                if not current_session.get("data"):
                    current_session["data"] = {}
                subs = current_session["data"].get(stage_mission)

                if not subs:
                    subs = []
                    current_session["data"][stage_mission] = subs
                if sub not in subs:
                    subs.append(sub)

                has_all = True

                for s in cls.progression[mission]["sub"]:
                    if s not in subs:
                        has_all = False
                        break

                if not has_all:
                    return 0, 0

                current_session["data"].pop(stage_mission, None)

        timenow = crudmgo.utctime()
        has_coins = False

        if not user["progress"][cls.stage_num].get(mission):
            stats = {"first": timenow,
                     "last": timenow,
                     "hits": 1}
            user["progress"][cls.stage_num][mission] = {sub: stats} if track_sub else stats
            has_coins = True
        else:
            if track_sub:
                if sub not in user["progress"][cls.stage_num][mission]:
                    mission_d = {"first": timenow,
                                 "last": None,
                                 "hits": 0}
                    user["progress"][cls.stage_num][mission][sub] = mission_d
                else:
                    mission_d = user["progress"][cls.stage_num][mission][sub]
            else:
                if "hits" not in user["progress"][cls.stage_num][mission]:
                    user["progress"][cls.stage_num][mission] = {"first": timenow,
                                                                "last": None,
                                                                "hits": 0}
                mission_d = user["progress"][cls.stage_num][mission]

            mission_d["last"] = timenow
            mission_d["hits"] += 1

            if mission_d["hits"] == 1:  # or (mission == "star" and mission_d["hits"] <= 3):
                has_coins = True

        rewards = cls.progression[mission]["rewards"][sub_index] if track_sub else cls.progression[mission]["rewards"]
        if not has_coins:
            rewards = (rewards[0], 0)

        cls.log_coins(mission, sub, track_sub, rewards[1], timenow)
        cls.update_progress(user)

        user.save()

        return rewards

    @classmethod
    def log_coins(cls, mission, sub, track_sub, rewards, timenow=False):
        if rewards:
            mission_log = {
                "stage": cls.stage_num,
                "mission": mission,
                "sub_mission": sub if track_sub else None,
                "coins": rewards,
                "on": timenow if timenow else crudmgo.utctime()
            }
            coinlog = current_app.config["mgodb"]["CoinLog"].find_one({"_id": current_user["_id"]})
            if not coinlog:
                coinlog = current_app.config["mgodb"]["CoinLog"]()
                coinlog["_id"] = current_user["_id"]
                coinlog["missions"] = []
            coinlog["missions"].append(mission_log)
            coinlog.save()

    @classmethod
    def update_progress(cls, user):
        if not user["progress"][cls.stage_num].get("_completed"):
            _completed = True
            user_progress = user["progress"][cls.stage_num]
            _missions_completed = 0
            _total_missions = len(cls.progression) - len(cls.untrack or ())

            for pname, prog in cls.progression.iteritems():
                if pname in (cls.untrack or ()):
                    continue

                _complete_mission = True

                if pname not in user_progress or not user_progress.get(pname):
                    _completed = False
                    _complete_mission = False
                elif prog["sub"] and isinstance(prog["rewards"][0], (tuple, list)):
                    for prog_sub in prog["sub"]:
                        if prog_sub not in user_progress[pname] or not user_progress[pname][prog_sub]\
                                or not user_progress[pname][prog_sub].get("hits"):
                            _completed = False
                            _complete_mission = False
                            break
                elif not user_progress[pname].get("hits"):
                    _completed = False
                    _complete_mission = False

                if _complete_mission:
                    _missions_completed += 1

            if _completed:
                user["progress"][cls.stage_num]["_completed"] = crudmgo.utctime()
                user["progress"][cls.stage_num]["_missions_completed"] = str(_total_missions) + "/" + str(_total_missions)
            else:
                user["progress"][cls.stage_num]["_missions_completed"] = str(_missions_completed) + "/" + str(_total_missions)


class StageOne(Stager):
    stage_num = 1
    progression = {"izeyes": {"sub": None,
                              "rewards": (100, 1)},
                   "mirror": {"sub": ["peopleilove", "thingsilove", "thingsiamgoodat"],
                              "rewards": [(0, 0), (0, 0), (300, 3)]},
                   "childlight": {"sub": None,
                                  "rewards": (100, 1)},
                   "keeper": {"sub": None,
                              "rewards": (100, 1)},
                   "pandora": {"sub": None,
                               "rewards": (100, 1)},
                   "dreamhut": {"sub": None,
                                "rewards": (100, 1)},
                   "tree": {"sub": ["hello", "thankyou", "imsorry"],
                            "rewards": [(100, 1), (100, 1), (100, 1)]},
                   "lightworld": {"sub": None,
                                  "rewards": (100, 5)},
                   "izsquad": {"sub": None,
                               "rewards": (200, 2)},
                   "star": {"sub": ["opentheeyes", "greaterplan", "rejoicealways", "givethanks", "youareblessed",
                                    "thereisnone", "youarespecial", "youareamasterpiece", "nothingsimpossible",
                                    "askandit", "knockandthedoor"],
                            "rewards": [(0, 3), (0, 3), (0, 3), (0, 3), (0, 3),
                                        (0, 3), (0, 3), (0, 3), (0, 3), (0, 3), (0, 3)]}}


class StageTwo(Stager):
    stage_num = 2
    progression = {"izradar": {"sub": None,
                               "rewards": (100, 1)},
                   "three": {"sub": None,
                             "rewards": (0, 0)},
                   "knowyourenemy": {"sub": None,
                                     "rewards": (100, 1)},
                   "flameofanger": {"sub": None,
                                    "rewards": (100, 1)},
                   "izkeeper": {"sub": None,
                                "rewards": (100, 1)},
                   "slowtoanger": {"sub": None,
                                   "rewards": (100, 1)},
                   "enails": {"sub": ["hurtful", "secret", "impersonate", "pretend", "exclude"],
                              "rewards": [(100, 1), (100, 1), (100, 1), (100, 1), (100, 1)]},
                   "izsquad": {"sub": None,
                               "rewards": (200, 2)},
                   "sense": {"sub": None,
                             "rewards": (100, 1)},
                   "star": {"sub": ["dontjustfollow", "dojustice", "getyourizradar", "anythingnicetosay",
                                    "givemeadiscerningheart", "infollmonsarelooking", "ioutsmartinfollmons",
                                    "ifyoucannotsay", "notjustonemessage", "isyourmessageok"],
                            "rewards": [(0, 3), (0, 3), (0, 3), (0, 3), (0, 3),
                                        (0, 3), (0, 3), (0, 3), (0, 3), (0, 3)]}}


class StageThree(Stager):
    stage_num = 3
    progression = {"izcontrol": {"sub": None,
                                 "rewards": (100, 1)},
                   "knowyourenemy": {"sub": None,
                                     "rewards": (100, 1)},
                   "childlight": {"sub": None,
                                  "rewards": (100, 1)},
                   "izkeeper": {"sub": None,
                                "rewards": (100, 1)},
                   "discipline": {"sub": None,
                                  "rewards": (100, 1)},
                   "time": {"sub": None,
                            "rewards": (100, 1)},
                   "izsquad": {"sub": None,
                               "rewards": (200, 2)},
                   "brutus": {"sub": None,
                              "rewards": (100, 1)},
                   "dungeon": {"sub": None,
                               "rewards": (100, 1)},
                   "contentcritique": {"sub": None,
                                       "rewards": (100, 1)},
                   "contentcritique2": {"sub": None,
                                        "rewards": (100, 1)},
                   "star": {"sub": ["iwilldiscipline", "stopcomplaining", "thereisaway", "mywordshavepower",
                                    "prepareyourminds", "iamincontrol", "bepositive", "greatpower",
                                    "allthingspossible", "saytherightthings", "youbecome"],
                            "rewards": [(0, 3), (0, 3), (0, 3), (0, 3), (0, 3), (0, 3),
                                        (0, 3), (0, 3), (0, 3), (0, 3), (0, 3)]}}


class StageFour(Stager):
    stage_num = 4
    progression = {"izprotect": {"sub": None,
                                 "rewards": (100, 1)},
                   "knowyourenemy": {"sub": None,
                                     "rewards": (100, 1)},
                   "childlight": {"sub": None,
                                  "rewards": (100, 1)},
                   "izkeeper": {"sub": None,
                                "rewards": (100, 1)},
                   "permission": {"sub": None,
                                  "rewards": (100, 1)},
                   "personal": {"sub": None,
                                "rewards": (100, 1)},
                   "izsquad": {"sub": None,
                               "rewards": (200, 2)},
                   "safety": {"sub": None,
                              "rewards": (100, 1)},
                   "star": {"sub": ["backoff", "dontgiveinfollmons", "iknowrightwrong", "iwillfindadult",
                                    "iwilltalksomeone", "justtryagain", "maketheworld",
                                    "nevergiveup", "thinkbeforeyourclick"],
                            "rewards": [(0, 3), (0, 3), (0, 3), (0, 3), (0, 3),
                                        (0, 3), (0, 3), (0, 3), (0, 3)]}}


class StageFive(Stager):
    stage_num = 5
    progression = {"izshout": {"sub": None,
                               "rewards": (100, 1)},
                   "knowyourenemy": {"sub": None,
                                     "rewards": (100, 1)},
                   "childlight": {"sub": None,
                                  "rewards": (100, 1)},
                   "izkeeper": {"sub": None,
                                "rewards": (100, 1)},
                   "powerpose": {"sub": None,
                                 "rewards": (100, 1)},
                   "team": {"sub": None,
                            "rewards": (100, 1)},
                   "izsquad": {"sub": None,
                               "rewards": (200, 2)},
                   "speakup": {"sub": None,
                               "rewards": (100, 1)},
                   "star": {"sub": ["backoff", "helpneedy", "iamcompassionate", "iwillfindadult",
                                    "iwilltalksomeone", "thisisnotcool", "notyourfault",
                                    "iambrave", "countonme", "takecareoffriends", "friendsforever",
                                    "letusbe", "weareizheroes"],
                            "rewards": [(0, 3), (0, 3), (0, 3), (0, 3), (0, 3),
                                        (0, 3), (0, 3), (0, 3), (0, 3), (0, 3),
                                        (0, 3), (0, 3), (0, 3)]}}


class StageSix(Stager):
    stage_num = 6
    progression = {"izears": {"sub": None,
                              "rewards": (100, 1)},
                   "knowyourenemy": {"sub": None,
                                     "rewards": (100, 1)},
                   "childlight": {"sub": None,
                                  "rewards": (100, 1)},
                   "izkeeper": {"sub": None,
                                "rewards": (100, 1)},
                   "express": {"sub": None,
                               "rewards": (100, 1)},
                   "hear": {"sub": ["typed", "feel", "relate"],
                            "rewards": [(0, 0), (0, 0), (300, 3)]},
                   "izsquad": {"sub": None,
                               "rewards": (200, 2)},
                   "lightworld": {"sub": None,
                                  "rewards": (100, 1)},
                   "star": {"sub": ["letmehelp", "areyouok", "howcanihelp", "youareawesome",
                                    "whenyougive", "iamproud", "youmakemesmile",
                                    "iamlistening", "hastheright", "notjudge"],
                            "rewards": [(0, 3), (0, 3), (0, 3), (0, 3), (0, 3),
                                        (0, 3), (0, 3), (0, 3), (0, 3), (0, 3)]}}


class StageSeven(Stager):
    stage_num = 7
    progression = {"izteleport": {"sub": None,
                                  "rewards": (100, 1)},
                   "knowyourenemy": {"sub": None,
                                     "rewards": (100, 1)},
                   "childlight": {"sub": None,
                                  "rewards": (100, 1)},
                   "mediarules": {"sub": None,
                                  "rewards": (100, 1)},
                   "mediapledge": {"sub": None,
                                   "rewards": (100, 1)},
                   "teach": {"sub": None,
                             "rewards": (100, 1)},
                   "izsquad": {"sub": None,
                               "rewards": (200, 2)},
                   "lightworld": {"sub": None,
                                  "rewards": (100, 1)},
                   "when": {"sub": None,
                            "rewards": (100, 1)},
                   "star": {"sub": ["dearmom", "thanksteacher", "rolemodel", "myhero",
                                    "momison", "teacherknows", "icancountonyou",
                                    "whatdoyouhave", "respectauthority", "honoryourfather"],
                            "rewards": [(0, 3), (0, 3), (0, 3), (0, 3), (0, 3),
                                        (0, 3), (0, 3), (0, 3), (0, 3), (0, 3)]}}
