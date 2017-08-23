$urlRouterProvider.otherwise("/users/admins");

$stateProvider

.state('users', {
    abstract: true,
    templateUrl: "static/views/Administrator/users/common.html",
})

.state('users.admins', {
    url: "/users/admins",
    templateUrl: "static/views/Administrator/users/admins.html",
    controller: 'AdminListCtrl as admin_list',
    data: {
        nice_name: 'Administrators'
    }
})

.state('users.admins_new', {
    url: "/users/admin_new",
    templateUrl: "static/views/Administrator/users/admin_edit.html",
    controller: 'AdminCtrl as admin',
    data: {
        nice_name: 'New Administrator'
    }
})

.state('users.admins_edit', {
    url: "/users/admin_edit",
    params: {'admin': {}},
    templateUrl: "static/views/Administrator/users/admin_edit.html",
    controller: 'AdminCtrl as admin',
    data: {
        nice_name: 'Edit Administrator'
    }
})

.state('users.students', {
    url: "/users/students",
    templateUrl: "static/views/Administrator/users/students.html",
    controller: 'UserListCtrl as user_list',
    data: {
        nice_name: 'Students'
    }
})

.state('users.izheroes', {
    url: '/users/izheroes',
    templateUrl: 'static/views/Administrator/users/izheroes.html',
    controller: 'IZHEROListCtrl as izhero_list',
    data: {
        nice_name: 'iZ HEROES'
    }
})

.state('users.izhero_edit', {
    url: '/users/izhero?id',
    params: {'izhero': {}},
    templateUrl: 'static/views/Administrator/users/izhero_edit.html',
    controller: 'IZHEROCtrl as izhero',
    data: {
        nice_name: 'Edit iZ HERO'
    }
})

.state('users.teachers', {
    url: '/users/teachers',
    templateUrl: 'static/views/Administrator/users/teachers.html',
    controller: 'TeacherListCtrl as teach_list',
    data: {
        nice_name: 'Teachers'
    }
})

.state('users.teacher_edit', {
    url: '/users/teacher?id',
    params: {'teacher': {}},
    templateUrl: 'static/views/Administrator/users/teacher_edit.html',
    controller: 'TeacherCtrl as teach',
    data: {
        nice_name: 'Edit Teacher'
    }
})

.state('users.members', {
    url: "/users/members",
    templateUrl: "static/views/Administrator/users/members.html",
    controller: 'MemberListCtrl as member_list',
    data: {
        nice_name: 'Memberships'
    }
})

.state('users.members_new', {
    url: "/users/member_new",
    templateUrl: "static/views/Administrator/users/member_edit.html",
    controller: 'MemberCtrl as member',
    data: {
        nice_name: 'New Membership'
    }
})

.state('users.schoolmembers', {
    url: "/users/teach_members",
    templateUrl: "static/views/Administrator/users/teach_members.html",
    controller: 'SchoolMemberListCtrl as member_list',
    data: {
        nice_name: 'Memberships'
    }
})

.state('users.schoolmembers_new', {
    url: "/users/teach_member_new",
    templateUrl: "static/views/Administrator/users/teach_member_edit.html",
    controller: 'SchoolMemberCtrl as member',
    data: {
        nice_name: 'New Membership'
    }
})

.state('missions', {
    abstract: true,
    templateUrl: "static/views/Administrator/missions/common.html",
    controller: 'MissionRootCtrl'
})

.state('missions.list', {
    url: "/missions",
    templateUrl: "static/views/Administrator/missions/list.html",
    controller: 'MissionListCtrl as mission_list'
})

.state('missions.detail', {
    url: "/missions/:id",
    templateUrl: "static/views/Administrator/missions/detail.html",
    controller: 'MissionCtrl as mission'
})
/*
.state('powers', {
    url: "/powers",
    templateUrl: "static/views/Administrator/list.html",
    controller: 'PowerListCtrl as mission_list',
    data: {
        nice_name: "What's Your Power"
    }
})
*/
.state('surveys', {
    url: "/surveys",
    templateUrl: "static/views/Administrator/list.html",
    controller: 'SurveyListCtrl as mission_list',
    data: {
        nice_name: 'Surveys'
    }
})

.state('quizzes', {
    url: "/quizzes",
    templateUrl: "static/views/Administrator/list.html",
    controller: 'QuizListCtrl as quiz_list',
    data: {
        nice_name: 'iZ Quiz'
    }
})

.state('stickers', {
    abstract: true,
    templateUrl: "static/views/Administrator/stickers/common.html",
    controller: 'StickerRootCtrl'
})

.state('stickers.list', {
    url: '/stickers',
    templateUrl: 'static/views/Administrator/stickers/list.html',
    controller: 'StickerListCtrl as sticker_list',
    data: {
        nice_name: 'Stickers'
    }
})

.state('stickers.gallery', {
    url: '/gallery',
    templateUrl: 'static/views/Administrator/stickers/gallery.html',
    controller: 'GalleryListCtrl as gallery_list',
    data: {
        nice_name: 'Gallery'
    }
})

.state('stats', {
    abstract: true,
    templateUrl: "static/views/Administrator/stats/common.html",
})

.state('stats.users', {
    url: "/stats",
    templateUrl: "static/views/Administrator/stats/users.html",
    controller: 'StatsCtrl as stats',
    data: {
        nice_name: "Registered Users"
    }
})

.state('stats.schools', {
    url: "/stats/schools",
    templateUrl: "static/views/Administrator/stats/schools.html",
    controller: 'StatsSchoolCtrl as stats',
    data: {
        nice_name: "Registered Users per School"
    }
})

.state('powers', {
    abstract: true,
    controller: 'PowerRootCtrl as power_root',
    templateUrl: "static/views/Administrator/powers/common.html"
})

.state('powers.list', {
    url: "/powers",
    templateUrl: "static/views/Administrator/powers/list.html",
    controller: 'PowerListCtrl as power_list',
    data: {
        nice_name: "7 Powers of Respect"
    }
})

.state('powers.power_edit', {
    url: "/powers/edit/:pid",
    templateUrl: "static/views/Administrator/powers/power_edit.html",
    controller: 'PowerCtrl as power',
    data: {
        nice_name: "Edit Power of Respect"
    },
    params: {
        p: {}
    }
})

.state('powers.power', {
    url: "/powers/:pid",
    templateUrl: "static/views/Administrator/powers/power.html",
    controller: 'PowerCtrl as power',
    data: {
        nice_name: "Power of Respect"
    },
    params: {
        p: {}
    }
})

.state('powers.mission', {
    url: "/mission/:mid",
    templateUrl: "static/views/Administrator/powers/mission.html",
    controller: 'MissionCtrl as mission',
    data: {
        nice_name: "Mission"
    },
    params: {
        m: {}
    }
})

.state('powers.mission_edit', {
    url: "/mission/edit/:mid",
    templateUrl: "static/views/Administrator/powers/mission_create.html",
    controller: 'MissionCtrl as mission',
    data: {
        nice_name: "Edit Mission"
    }
})

.state('powers.mission_create', {
    url: "/mission/create/:pid",
    templateUrl: "static/views/Administrator/powers/mission_create.html",
    controller: 'MissionCtrl as mission',
    data: {
        nice_name: "Create Mission"
    }
})

.state('izsquads', {
    abstract: true,
    templateUrl: "static/views/Administrator/izsquads/common.html"
})

.state('izsquads.list', {
    url: "/izsquads",
    templateUrl: "static/views/Administrator/izsquads/list.html",
    controller: 'IZSquadListCtrl as izsquad_list',
    data: {
        nice_name: "Classes"
    }
})

.state('anns', {
    abstract: true,
    templateUrl: "static/views/Administrator/anns/common.html"
})

.state('anns.list', {
    url: "/announcements",
    templateUrl: "static/views/Administrator/anns/list.html",
    controller: 'AnnListCtrl as ann_list',
    data: {
        nice_name: "Announcements"
    }
})

.state('anns.create', {
    url: "/announcements/create",
    templateUrl: "static/views/Administrator/anns/create.html",
    controller: 'AnnCtrl as ann_list',
    data: {
        nice_name: "Make an Announcement"
    }
})

.state('anns.edit', {
    url: "/announcements/edit/:id",
    templateUrl: "static/views/Administrator/anns/create.html",
    controller: 'AnnCtrl as ann_list',
    data: {
        nice_name: "Edit an Announcement"
    },
    params: {
        entity: {}
    }
})

.state('anns.feedbacks', {
    url: "/feedbacks",
    templateUrl: "static/views/Administrator/anns/feedbacks.html",
    controller: 'FeedbackListCtrl as feedback_list',
    data: {
        nice_name: "Feedbacks"
    }
})

.state('anns.feedback_view', {
    url: "/feedbacks/view/:id",
    templateUrl: "static/views/Administrator/anns/feedback_view.html",
    controller: 'FeedbackCtrl as feedback',
    data: {
        nice_name: "Feedback"
    },
    params: {
        entity: {}
    }
})

.state('schools', {
    abstract: true,
    templateUrl: "static/views/Administrator/schools/common.html"
})

.state('schools.list', {
    url: "/schools",
    templateUrl: "static/views/Administrator/schools/list.html",
    controller: 'UnverifSchoolListCtrl as school_list',
    data: {
        nice_name: "Schools"
    }
})

.state('encyclopedia', {
    abstract: true,
    templateUrl: "static/views/Administrator/encyclopedia/common.html"
})

.state('encyclopedia.category', {
    url: "/encyclopedia",
    templateUrl: "static/views/Administrator/encyclopedia/categories.html",
    controller: 'EncyclopediaCtrl as encyclopedia',
    data: {
        nice_name: "Encyclopedia"
    },
    params: {
        lang: 'en'
    }
})

.state('encyclopedia.category_create', {
    url: "/encyclopedia/create?lang",
    templateUrl: "static/views/Administrator/encyclopedia/category_edit.html",
    controller: 'ECategoryCtrl as encyclopedia',
    data: {
        nice_name: "Encyclopedia"
    }
})

.state('encyclopedia.category_edit', {
    url: "/encyclopedia/edit/:cid?lang",
    templateUrl: "static/views/Administrator/encyclopedia/category_edit.html",
    controller: 'ECategoryCtrl as encyclopedia',
    data: {
        nice_name: "Encyclopedia"
    },
    params: {
        c: {}
    }
})

.state('encyclopedia.pages', {
    url: "/encyclopedia/pages/:cid?lang",
    templateUrl: "static/views/Administrator/encyclopedia/pages.html",
    controller: 'PagesCtrl as epages',
    data: {
        nice_name: "Encyclopedia Page"
    }
})

.state('encyclopedia.page_create', {
    url: "/encyclopedia/page/create/:cid?lang",
    templateUrl: "static/views/Administrator/encyclopedia/page_edit.html",
    controller: 'PageCtrl as epage',
    data: {
        nice_name: "Encyclopedia Page"
    }
})

.state('encyclopedia.page_edit', {
    url: "/encyclopedia/page/edit/:pid?lang",
    templateUrl: "static/views/Administrator/encyclopedia/page_edit.html",
    controller: 'PageCtrl as epage',
    data: {
        nice_name: "Encyclopedia Page"
    },
    params: {
        p: {}
    }
})

.state('encyclopedia.page_view', {
    url: "/encyclopedia/page/view/:pid?lang",
    templateUrl: "static/views/Administrator/encyclopedia/page_view.html",
    controller: 'PageCtrl as epage',
    data: {
        nice_name: "Encyclopedia Page"
    }
})

.state('dqresults', {
    abstract: true,
    templateUrl: "static/views/Administrator/dqresults/common.html",
})

.state('dqresults.pretests', {
    url: "/dqresults/pretests",
    templateUrl: "static/views/Administrator/dqresults/pretests.html",
    controller: 'PretestListCtrl as dqresult_list',
    data: {
        nice_name: 'Pretest DQ Results'
    }
})

.state('lessons', {
    abstract: true,
    templateUrl: "static/views/Administrator/lessons/common.html",
})

.state('lessons.list', {
    url: "/lessons",
    templateUrl: "static/views/Administrator/lessons/list.html",
    controller: 'LessonListCtrl as dqlesson_list',
    data: {
        nice_name: 'Lessons'
    },
    params: {
        lang: 'en'
    }
})

.state('lessons.lesson', {
    url: "/lessons/lesson?lid&lang",
    templateUrl: "static/views/Administrator/lessons/lesson.html",
    controller: 'LessonCtrl as dqlesson',
    data: {
        nice_name: 'Lesson'
    },
    params: {
        lesson: {}
    }
})