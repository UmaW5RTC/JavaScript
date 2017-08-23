$urlRouterProvider.otherwise("/surveys");

$stateProvider

.state('surveys', {
    abstract: true,
    templateUrl: "static/views/Counselor/surveys/common.html",
    controller: 'SurveyRootCtrl'
})

.state('surveys.list', {
    url: "/surveys",
    templateUrl: "static/views/Counselor/surveys/list.html",
    controller: 'SurveyListCtrl as survey_list',
    data: {
        nice_name: 'Surveys'
    }
})

.state('surveys.one', {
    url: "/survey/:id",
    templateUrl: "static/views/Counselor/surveys/one.html",
    controller: 'SurveyCtrl as survey',
    data: {
        nice_name: 'Survey'
    }
})



