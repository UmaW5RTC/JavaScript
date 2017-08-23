/*
@copyright 2015. iZ Hero
Created by FxHarvest LLP
*/

'use strict';

(function(ng){

    /** @ngInject */
    function LessonListCtrl($scope, $http, BASE_URL, $state, $sce){
        $scope.sort = 'code';
        $scope.filters = {
            power: '',
            competency: '',
            topic: '',
            value: ''
        };
        $scope.ui = {
            powers: [],
            competencies: [],
            topics: [],
            values: []
        };
        $scope.title = {
            powers: {},
            competencies: {},
            values: {},
            topics: {}
        }

        function loadFilters(name) {
            $http.get(BASE_URL + 'lessons/' + name)
                .success(function (res) {
                    if (res.items) {
                        $scope.ui[name] = res.items;
                        if ($scope.title[name]) {
                            for (var i in res.items) {
                                $scope.title[name][res.items[i]._id] = {definition: res.items[i].definition || '',
                                                                        name: res.items[i].name || ''};
                            }
                        }
                    }
                });
        }

        $scope.sortBy = function(name) {
            $scope.sort = ($scope.sort === name) ? '-' + name : name;
            $scope.loadLessons();
        };

        $scope.loadLessons = function() {
            var params = {};

            if ($scope.filters.power) {
                params['power'] = $scope.filters.power;
            }
            if ($scope.filters.competency) {
                params['competency'] = $scope.filters.competency;
            }
            if ($scope.filters.topic) {
                params['topic'] = $scope.filters.topic;
            }
            if ($scope.filters.value) {
                params['value'] = $scope.filters.value;
            }

            if ($scope.sort) {
                params['o'] = $scope.sort;
            }

            $http.get(BASE_URL + 'lessons', {params: params})
                .success(function (res) {
                    if (res.items) {
                        for(var i = 0; i < res.items.length; i++) {
                            switch(res.items[i].level) {
                            case 1:
                            case '1':
                                res.items[i].level_name = 'Easy';
                                break;
                            case 2:
                            case '2':
                                res.items[i].level_name = 'Intermediate';
                                break;
                            case 3:
                            case '3':
                                res.items[i].level_name = 'Advanced';
                                break;
                            }
                            res.items[i].link = '/zone/e' + getStage(res.items[i].power_id) + '#!/' + res.items[i].power.replace(' ', '') + '?launch=' + res.items[i].id;
                            res.items[i].power_title = $sce.trustAsHtml('<a title="' + $scope.title.powers[res.items[i].power_id].definition.replace('"', '&quot;') + '">' + res.items[i].power + '</a>');
                        }
                        $scope.missions = res.items;
                    }
                });
        }

        function getStage(powerid) {
            for (var i in $scope.ui.powers) {
                if ($scope.ui.powers[i]._id == powerid) {
                    return $scope.ui.powers[i].adventure | 0;
                }
            }
            return '';
        }

        $scope.getSEL = function(selcompetency) {
            var value = '';

            for (var i in selcompetency) {
                if (selcompetency[i] in $scope.title.competencies) {
                    if (value !== '') {
                        value += ',<br>';
                    }
                    value += '<a title="' + $scope.title.competencies[selcompetency[i]].definition.replace('"', '&quot;') + '">' + $scope.title.competencies[selcompetency[i]].name + '</a>';
                }
            }

            return $sce.trustAsHtml(value);
        };

        $scope.getCWValue = function(cwvalue) {
            var value = '';

            for (var i in cwvalue) {
                if (cwvalue[i] in $scope.title.values) {
                    if (value !== '') {
                        value += ',<br>';
                    }
                    value += '<a title="' + $scope.title.values[cwvalue[i]].definition.replace('"', '&quot;') + '">' + $scope.title.values[cwvalue[i]].name + '</a>';
                }
            }

            return $sce.trustAsHtml(value);
        };

        $scope.getCWTopic = function(cwtopic) {
            var value = '';

            for (var i in cwtopic) {
                if (cwtopic[i] in $scope.title.topics) {
                    if (value !== '') {
                        value += ',<br>';
                    }
                    value += '<a title="' + $scope.title.topics[cwtopic[i]].definition.replace('"', '&quot;') + '">' + $scope.title.topics[cwtopic[i]].name + '</a>';
                }
            }

            return $sce.trustAsHtml(value);
        };

        loadFilters('powers');
        loadFilters('competencies');
        loadFilters('topics');
        loadFilters('values');
        $scope.loadLessons();
    }

    /** @ngInject */
    function SELCompetencyListCtrl($scope, $http, BASE_URL, $state, $sce){
        $scope.ui = {
            competencies: []
        };

        function loadFilters(name) {
            $http.get(BASE_URL + 'lessons/' + name)
                .success(function (res) {
                    if (res.items) {
                        $scope.ui[name] = res.items;
                    }
                });
        }

        loadFilters('competencies');
    }

    /** @ngInject */
    function CWValueListCtrl($scope, $http, BASE_URL, $state, $sce){
        $scope.ui = {
            values: []
        };

        function loadFilters(name) {
            $http.get(BASE_URL + 'lessons/' + name)
                .success(function (res) {
                    if (res.items) {
                        $scope.ui[name] = res.items;
                    }
                });
        }

        loadFilters('values');
    }

    /** @ngInject */
    function CWTopicListCtrl($scope, $http, BASE_URL, $state, $sce){
        $scope.ui = {
            topics: []
        };

        function loadFilters(name) {
            $http.get(BASE_URL + 'lessons/' + name)
                .success(function (res) {
                    if (res.items) {
                        $scope.ui[name] = res.items;
                    }
                });
        }

        loadFilters('topics');
    }

    /** @ngInject */
    function PowerListCtrl($scope, $http, BASE_URL, $state, $sce){
        $scope.ui = {
            powers: []
        };

        function loadFilters(name) {
            $http.get(BASE_URL + 'lessons/' + name)
                .success(function (res) {
                    if (res.items) {
                        $scope.ui[name] = res.items;
                    }
                });
        }

        loadFilters('powers');
    }

    ng.controller('LessonListCtrl', LessonListCtrl);
    ng.controller('SELCompetencyListCtrl', SELCompetencyListCtrl);
    ng.controller('CWValueListCtrl', CWValueListCtrl);
    ng.controller('CWTopicListCtrl', CWTopicListCtrl);
    ng.controller('PowerListCtrl', PowerListCtrl);

})(angular.module(APP_MODULE_NAME));