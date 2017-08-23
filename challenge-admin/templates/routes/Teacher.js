$urlRouterProvider.otherwise("/squads");

$stateProvider

.state('squads', {
    abstract: true,
    templateUrl: "VIEW_PATH/Teacher/squads/common.html",
    controller: 'SquadRootCtrl'
})

.state('squads.list', {
    url: "/squads?guide",
    templateUrl: "VIEW_PATH/Teacher/squads/list.html",
    controller: 'SquadListCtrl as squad_list',
    data: {
        nice_name: 'Squads'
    }
})

.state('squads.create', {
    url: "/squads/create",
    templateUrl: "VIEW_PATH/Teacher/squads/create.html",
    controller: 'SquadCtrl as squad',
    data: {
        nice_name: 'Squad'
    },
    params: {
        is_tutorial: {}
    }
})

.state('squads.edit', {
    url: "/squads/edit?code",
    templateUrl: "VIEW_PATH/Teacher/squads/create.html",
    controller: 'SquadCtrl as squad',
    data: {
        nice_name: 'Squad'
    }
})

.state('squads.allmembers', {
    url: "/squads/members",
    templateUrl: "VIEW_PATH/Teacher/squads/members.html",
    controller: 'MemberListCtrl as member_list',
    data: {
        nice_name: 'Members'
    }
})

.state('squads.members', {
    url: "/squads/members/:code/:name",
    templateUrl: "VIEW_PATH/Teacher/squads/members.html",
    controller: 'MemberListCtrl as member_list',
    data: {
        nice_name: 'Members'
    },
    params: {
        is_tutorial: {}
    }
})

.state('squads.member', {
    url: "/squads/member/:id",
    templateUrl: "VIEW_PATH/Teacher/squads/member.html",
    controller: 'MemberCtrl as member',
    data: {
        nice_name: 'Member'
    }
})

.state('squads.add_member', {
    url: "/squads/member/:code/:name",
    templateUrl: "VIEW_PATH/Teacher/squads/member.html",
    controller: 'MemberCtrl as member',
    data: {
        nice_name: 'Add Student'
    }
})

.state('squads.stickers', {
    url: "/squads/stickers?code",
    templateUrl: "VIEW_PATH/Teacher/squads/stickers.html",
    controller: 'SquadStickerListCtrl as sticker_list',
    data: {
        nice_name: 'Stickers'
    }
})

.state('squads.rstickers', {
    url: "/squads/rstickers?code",
    templateUrl: "VIEW_PATH/Teacher/squads/stickers.html",
    controller: 'SquadRStickerListCtrl as sticker_list',
    data: {
        nice_name: 'Stickers',
        removed: true
    }
})

.state('squads.stories', {
    url: "/squads/stories?code",
    templateUrl: "VIEW_PATH/Teacher/squads/stories.html",
    controller: 'SquadStoryListCtrl as sticker_list',
    data: {
        nice_name: 'Stories',
        is_story: true
    }
})

.state('squads.rstories', {
    url: "/squads/rstories?code",
    templateUrl: "VIEW_PATH/Teacher/squads/stories.html",
    controller: 'SquadRStoryListCtrl as sticker_list',
    data: {
        nice_name: 'Stories',
        is_story: true,
        removed: true
    }
})

.state('profile', {
    abstract: true,
    templateUrl: "VIEW_PATH/Teacher/profile/common.html"
})

.state('profile.me', {
    url: "/profile",
    templateUrl: "VIEW_PATH/Teacher/profile/detail.html",
    controller: 'ProfileCtrl as profile',
    data: {
        nice_name: 'Profile'
    }
})

.state('profile.accesscode', {
    url: "/accesscode",
    templateUrl: "VIEW_PATH/Teacher/profile/accesscode.html",
    controller: 'AccessCodeCtrl as accesscode',
    data: {
        nice_name: 'Access Code'
    }
})

.state('squads.news', {
    url: "/squads/news?code",
    templateUrl: "VIEW_PATH/Teacher/squads/news.html",
    controller: 'NewsListCtrl as news_list',
    data: {
        nice_name: 'News'
    }
})

.state('squads.create_news', {
    url: "/squads/news/create?code",
    templateUrl: "VIEW_PATH/Teacher/squads/news_edit.html",
    controller: 'NewsCtrl as news',
    data: {
        nice_name: 'News'
    }
})

.state('squads.edit_news', {
    url: "/squads/news/edit",
    templateUrl: "VIEW_PATH/Teacher/squads/news_edit.html",
    controller: 'NewsCtrl as news',
    data: {
        nice_name: 'News'
    },
    params: {
        news: {}
    }
})

.state('lessons', {
    abstract: true,
    templateUrl: "VIEW_PATH/Teacher/lessons/common.html"
})

.state('lessons.list', {
    url: "/lessons",
    templateUrl: "VIEW_PATH/Teacher/lessons/list.html",
    controller: 'LessonListCtrl as lessons',
    data: {
        nice_name: "Missions"
    }
})

.state('lessons.competencies', {
    url: "/lessons/selcompetencies",
    templateUrl: "VIEW_PATH/Teacher/lessons/competencies.html",
    controller: 'SELCompetencyListCtrl as competencies',
    data: {
        nice_name: "Social and Emotional Learning Competencies"
    }
})

.state('lessons.values', {
    url: "/lessons/cwvalues",
    templateUrl: "VIEW_PATH/Teacher/lessons/values.html",
    controller: 'CWValueListCtrl as values',
    data: {
        nice_name: "Cyber Wellness Values"
    }
})

.state('lessons.topics', {
    url: "/lessons/cwtopics",
    templateUrl: "VIEW_PATH/Teacher/lessons/topics.html",
    controller: 'CWTopicListCtrl as topics',
    data: {
        nice_name: "Cyber Wellness Topics"
    }
})

.state('lessons.powers', {
    url: "/lessons/powers",
    templateUrl: "VIEW_PATH/Teacher/lessons/powers.html",
    controller: 'PowerListCtrl as powers',
    data: {
        nice_name: "7 Powers of RESPECT"
    }
})

.state('anns', {
    abstract: true,
    templateUrl: "VIEW_PATH/Teacher/anns/common.html"
})

.state('anns.list', {
    url: "/announcements",
    templateUrl: "VIEW_PATH/Teacher/anns/list.html",
    controller: 'AnnListCtrl as ann_list',
    data: {
        nice_name: "News"
    }
})

.state('anns.view', {
    url: "/announcements/view/:id",
    templateUrl: "VIEW_PATH/Teacher/anns/view.html",
    controller: 'AnnCtrl as ann_list',
    data: {
        nice_name: "News"
    },
    params: {
        entity: {}
    }
})

.state('anns.feedbacks', {
    url: "/feedbacks",
    templateUrl: "VIEW_PATH/Teacher/anns/feedbacks.html",
    controller: 'FeedbackListCtrl as feedback_list',
    data: {
        nice_name: "Feedbacks"
    }
})

.state('anns.feedback_view', {
    url: "/feedbacks/view/:id",
    templateUrl: "VIEW_PATH/Teacher/anns/feedback_view.html",
    controller: 'FeedbackCtrl as feedback',
    data: {
        nice_name: "Feedback"
    },
    params: {
        entity: {}
    }
})

.state('anns.feedback_create', {
    url: "/feedbacks/create",
    templateUrl: "VIEW_PATH/Teacher/anns/feedback_create.html",
    controller: 'FeedbackCtrl as feedback',
    data: {
        nice_name: "Make a Feedback"
    },
    params: {
        entity: {}
    }
})
