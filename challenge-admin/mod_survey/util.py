# -*- coding: utf-8 -*-
__author__ = 'n2m'

from flask import escape


def get_pre_question(qns):
    return pre_qns.get(int(qns), "")


def get_pre_answer(qns, ans, anstxt):
    anstxt = str(escape(anstxt))
    return pre_qnstype.get(qns, scale)(ans, anstxt)


def get_pre_choice(qns, ans):
    if int(qns) == 4:
        return izherochoice(ans)
    return ans


def get_post_question(qns):
    return post_qns.get(int(qns), "")


def get_post_answer(qns, ans, anstxt):
    anstxt = str(escape(anstxt))
    return post_qnstype.get(qns, scale)(ans, anstxt)


def get_post_choice(qns, ans):
    qns = int(qns)
    if qns == 1:
        return izherochoice(ans)
    if qns == 2:
        return izherochalhowchoice(ans)
    return ans


def gender(ans, _=None):
    return "Boy" if ans == 1 else "Girl"


def race(ans, anstxt=None):
    return {1: "Chinese",
            2: "Malay",
            3: "Indian",
            4: "Eurasian"}.get(int(ans), anstxt)


def age(ans, _=None):
    if ans == 1:
        return "Below 6 years"
    if ans >= 14:
        return "Above 18 years"
    return str(int(ans) + 5) + " years"


def izhero(ans, _=None):
    return ("No" if ans & 1 else "Yes"), izherocontent(ans)


def izherocontent(ans):
    c = "<ul>"
    if ans & 2:
        c += "<li>I have played the iZ HERO Story Quest Game</li>"
    if ans & 4:
        c += "<li>I have visited the iZ HERO Exhibition @ Singapore Science Centre</li>"
    if ans & 8:
        c += "<li>I have read the iZ HERO Comic Story</li>"
    if ans & 16:
        c += "<li>I have visited the iZ HERO Challenge Website</li>"
    c += "</ul>"
    return c


def izherochoice(ans):
    return (1 if ans & 1 else 2), izherocontentchoice(ans)


def izherocontentchoice(ans):
    c = ""

    if ans & 2:
        c += "1, "
    if ans & 4:
        c += "2, "
    if ans & 8:
        c += "3, "
    if ans & 16:
        c += "4, "

    if c:
        c = c[:-2]
    return c


def izherochal(ans, anstxt=None):
    return {1: "I have not visited the site",
            2: "I visited the site but I didn’t play its activities",
            3: "I have played some of its activities",
            4: "I have completed a cycle of all its activities at least once"}.get(int(ans), anstxt)


def izherochalhow(ans, anstxt=None):
    c = "<ul>"
    if ans & 1:
        c += "<li>I played the Website by myself at home</li>"
    if ans & 2:
        c += "<li>My friends played the Website together</li>"
    if ans & 4:
        c += "<li>My teacher taught us some lessons of iZ HERO Challenge in class</li>"
    if ans & 8:
        c += "<li>My teacher taught us all of the 10 lessons of iZ HERO Challenge in class</li>"
    if ans & 16:
        c += "<li>My parent helped me play the Website at home</li>"
    if ans & 32:
        c += "<li>Others: " + anstxt + "</li>"
    c += "</ul>"
    return c


def izherochalhowchoice(ans):
    c = ""

    if ans & 1:
        c += "1, "
    if ans & 2:
        c += "2, "
    if ans & 4:
        c += "3, "
    if ans & 8:
        c += "4, "
    if ans & 16:
        c += "5, "
    if ans & 32:
        c += "6, "

    if c:
        c = c[:-2]
    return c


def scale7(neg, pos):
    def s7(ans, _=None):
        ans = int(ans)
        return "%s : %s%s%s : %s" % (neg,
                                     ("_ " * (ans - 1)),
                                     '<strong style="text-decoration:underline;">x</strong>',
                                     (" _" * (7 - ans)),
                                     pos)
    return s7


def scale(ans, anstxt=None):
    return {1: "Strongly Disagree",
            2: "Disagree",
            3: "Neutral",
            4: "Agree",
            5: "Strongly Agree"}.get(int(ans), anstxt)


pre_qns = {1: "Are you a boy or a girl?",
           2: "What is your race?",
           3: "How old are you?",
           4: ("Have you ever played, read, or been to anything related to iZ HERO?",
               "If Yes, which of the following have you done?"),
           5: "Have you ever played the activities in the iZ HERO Challenge Website?",
           6: {"h": "Part One: iZ Master would like to know how you feel about yourself.",
               "q": "1. I feel that I have a number of good qualities."},
           7: "2. At times, I think I am no good at all.",
           8: "3. I often wish I were someone else.",
           9: "4. I am doing the best work that I can.",
           10: "5. I am a lot of fun to be with.",
           11: "6. Someone always has to tell me what to do.",
           12: "7. I am happy to try new things.",
           13: "8. I do not get upset easily.",
           14: "9. I know how to deal with my anger.",
           15: {"h": "Part Two: iZ Master would like to know how you feel about others.",
                "q": "1. It's alright to send mean messages to someone using a mobile phone or the internet " +
                     "if they have poked fun at your friends."},
           16: "2. Posting a mean message about a cyber bully is just teaching them a lesson.",
           17: "3. Sending a mean message about someone on Facebook is just teasing.",
           18: "4. Children cannot be blamed for texting mean comments if it is commonly done by everyone.",
           19: "5. Posting mean comments about other kids on Facebook does not really hurt them.",
           20: "6. Kids who get cyber bullied usually do things to deserve it.",
           21: "7. Someone who is a cyber bully does not deserve to be treated like a human being.",
           22: "8. I should not give my home address/photos etc to someone I don’t know well on the internet.",
           23: "9. It is not wise to respond to any messages that are mean or nasty or make you feel uncomfortable.",
           24: "10. I can tell what other people are feeling.",
           25: "11. I am able to tell when other people are upset.",
           26: "12. I can understand another person’s way of thinking.",
           27: {"h": "Part Three: iZ Master would like to know if or how often do your parents do the following.",
                "q": "1. Demands to know whom I chat with online."},
           28: "2. Limits the amount of time that I can use the Internet.",
           29: "3. Talks to me about what I should do if  I  receive messages from strangers.",
           30: "4. Parents have taught me to use the Internet safely.",
           31: "5. My parent stays nearby me when I am online.",
           32: "6. Determines the time of the day I can use Internet.",
           33: "7. Talks to me about what kinds of things should or should not be shared online.",
           34: "8. Talks to me about what I should do if someone tries to threaten me.",
           35: "9. Talks to me why some websites are good or bad.",
           36: "10. My parent has set rules about time spent online.",
           37: {"h": ("Part Four: Finally, iZ Master like to know your opinion about some actions.",
                      "Giving out  Personal Information Online  to someone I don’t know well is..."),
                "q": "Bad/Good"},
           38: "Foolish/Wise",
           39: "Unenjoyable/Enjoyable",
           40: "Harmful/Beneficial",
           41: "Unimportant/Important",
           42: {"h": "Saying or doing nasty or hurting remarks to other online/ on the Internet is...",
                "q": "Bad/Good"},
           43: "Foolish/Wise",
           44: "Unenjoyable/Enjoyable",
           45: "Harmful/Beneficial",
           46: "Unfavourable/Favourable",
           47: {"h": "",
                "q": "I have said nasty or hurtful things to others in the past year while on the Internet"},
           48: "I do not intend to say nasty or hurting remarks to others online/ on the Internet in the near future"}

pre_qnstype = {1: gender,
               2: race,
               3: age,
               4: izhero,
               5: izherochal,
               37: scale7("Bad", "Good"),
               42: scale7("Bad", "Good"),
               38: scale7("Foolish", "Wise"),
               43: scale7("Foolish", "Wise"),
               39: scale7("Unenjoyable", "Enjoyable"),
               44: scale7("Unenjoyable", "Enjoyable"),
               40: scale7("Harmful", "Beneficial"),
               45: scale7("Harmful", "Beneficial"),
               41: scale7("Unimportant", "Important"),
               46: scale7("Unfavourable", "Favourable")}


post_qns = {1: ("Have you ever played, read, or been to anything related to iZ HERO?",
                "If Yes, which of the following have you done?"),
            2: "How did you played the iZ HERO Challenge?",
            3: {"h": "Part One: iZ Master would like to know how you feel about yourself.",
                "q": "1. I feel that I have a number of good qualities."},
            4: "2. At times, I think I am no good at all.",
            5: "3. I often wish I were someone else.",
            6: "4. I am doing the best work that I can.",
            7: "5. I am a lot of fun to be with.",
            8: "6. Someone always has to tell me what to do.",
            9: "7. I am happy to try new things.",
            10: "8. I do not get upset easily.",
            11: "9. I know how to deal with my anger.",
            12: {"h": "Part Two: iZ Master would like to know how you feel about others.",
                 "q": "1. It's alright to send mean messages to someone using a mobile phone or the internet " +
                      "if they have poked fun at your friends."},
            13: "2. Posting a mean message about a cyber bully is just teaching them a lesson.",
            14: "3. Sending a mean message about someone on Facebook is just teasing.",
            15: "4. Children cannot be blamed for texting mean comments if it is commonly done by everyone.",
            16: "5. Posting mean comments about other kids on Facebook does not really hurt them.",
            17: "6. Kids who get cyber bullied usually do things to deserve it.",
            18: "7. Someone who is a cyber bully does not deserve to be treated like a human being.",
            19: "8. I should not give my home address/photos etc to someone I don’t know well on the internet.",
            20: "9. It is not wise to respond to any messages that are mean or nasty or make you feel uncomfortable.",
            21: "10. I can tell what other people are feeling.",
            22: "11. I am able to tell when other people are upset.",
            23: "12. I can understand another person’s way of thinking.",
            24: {"h": "Part Three: iZ Master would like to know if or how often do your parents do the following.",
                 "q": "1. Demands to know whom I chat with online."},
            25: "2. Limits the amount of time that I can use the Internet.",
            26: "3. Talks to me about what I should do if  I  receive messages from strangers.",
            27: "4. Parents have taught me to use the Internet safely.",
            28: "5. My parent stays nearby me when I am online.",
            29: "6. Determines the time of the day I can use Internet.",
            30: "7. Talks to me about what kinds of things should or should not be shared online.",
            31: "8. Talks to me about what I should do if someone tries to threaten me.",
            32: "9. Talks to me why some websites are good or bad.",
            33: "10. My parent has set rules about time spent online.",
            34: {"h": ("Part Four: Finally, iZ Master like to know your opinion about some actions.",
                       "Giving out  Personal Information Online  to someone I don’t know well is..."),
                "q": "Bad/Good"},
            35: "Foolish/Wise",
            36: "Unenjoyable/Enjoyable",
            37: "Harmful/Beneficial",
            38: "Unimportant/Important",
            39: {"h": "Saying or doing nasty or hurting remarks to other online/ on the Internet is...",
                "q": "Bad/Good"},
            40: "Foolish/Wise",
            41: "Unenjoyable/Enjoyable",
            42: "Harmful/Beneficial",
            43: "Unfavourable/Favourable",
            44: {"h": "",
                 "q": "I have said nasty or hurtful things to others in the past year while on the Internet"},
            45: "I do not intend to say nasty or hurting remarks to others online/ on the Internet in the near future",
            46: {"h": "Part Five: iZ Master would like to know how you feel about the playing iZ HERO Challenge website activities.",
                 "q": "1. The iZ HERO Challenge website activities made learning more interesting."},
            47: "2. Doing the iZ HERO Challenge website activities is worthwhile.",
            48: "3. The iZ HERO Challenge website activities are helpful.",
            49: "4. I like the comic stories of the iZ HERO Challenge."}

post_qnstype = {1: izhero,
                2: izherochalhow,
                34: scale7("Bad", "Good"),
                39: scale7("Bad", "Good"),
                35: scale7("Foolish", "Wise"),
                40: scale7("Foolish", "Wise"),
                36: scale7("Unenjoyable", "Enjoyable"),
                41: scale7("Unenjoyable", "Enjoyable"),
                37: scale7("Harmful", "Beneficial"),
                42: scale7("Harmful", "Beneficial"),
                38: scale7("Unimportant", "Important"),
                43: scale7("Unfavourable", "Favourable")}