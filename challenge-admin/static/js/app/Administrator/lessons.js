/*
@copyright 2015. iZ Hero
Created by FxHarvest LLP
*/

'use strict';


(function(ng){

    /** @ngInject */
    function LessonListCtrl($scope, $http, BASE_URL, $state, $stateParams){
        $scope.lessons = [];
        $scope.lang = $stateParams.lang || 'en';

        $scope.refresh = function() {
            $http.get(BASE_URL + 'dqlessons?lang=' + $scope.lang)
                .success(function (res) {
                    if (res.items) {
                        $scope.lessons = res.items;
                    }
                });
        }

        $scope.refresh();

        $scope.delete = function(lid) {
            if (lid && confirm('Are you sure you want to delete this lesson?')) {
                $http.delete(BASE_URL + 'dqlessons/item/' + lid)
                    .success(function() {
                        refresh();
                    });
            }
        };

        $scope.to_lesson = function (l) {
            $state.go('lessons.lesson', {lid: l._id, lesson: l, lang: l.lang});
        };

        $scope.create = function() {
            $state.go('lessons.lesson', {lang: $scope.lang});
        };

        /*
        $scope.$watch('lang', function(newval, oldval) {
            newval !== oldval && refresh();
        });*/
    }

    /** @ngInject */
    function LessonCtrl($scope, $http, $state, $stateParams, BASE_URL) {
        $scope.ui = {
            success: null,
            busy: false
        };
        $scope.lesson = {
            lang: $stateParams.lang,
            no: '',
            name: '',
            objective: '',
            keypoints: '',
            time: ''
        };

        function loadLesson(lid) {
            if (!$scope.ui.busy) {
                $scope.ui.busy = true;
                $http.get(BASE_URL + 'dqlessons/item/' + lid)
                    .success(function (res) {
                        $scope.ui.busy = false;
                        $scope.lesson = res;
                    }).error(function () {
                        $scope.ui.busy = false;
                    });
            }
        }

        $scope.save = function (lesson) {
            if (!$scope.ui.busy) {
                $scope.ui.busy = true;
                var method = lesson._id ? 'PUT' : 'POST',
                    url = BASE_URL + 'dqlessons' + (lesson._id ? '/item/' + lesson._id : '');
                $http({
                    method: method,
                    url: url,
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    },
                    data: lesson,
                    transformRequest: function (data, headersGetter) {
                        var formData = new FormData();
                        _.forEach(data, function (value, key) {
                            formData.append(key, value);
                        });

                        var headers = headersGetter();
                        delete headers['Content-Type'];
                        return formData;
                    }
                }).success(function (res) {
                    $scope.ui.success = res.success;
                    $scope.ui.busy = false;
                    res.success && $scope.cancel();
                }).error(function () {
                    $scope.ui.success = false;
                    $scope.ui.busy = false;
                });
            }
        };

        $scope.cancel = function() {
            $state.go('lessons.list', {lang: $scope.lesson.lang});
        }

        if (!$stateParams.lesson || !$stateParams.lesson._id) {
            if ($stateParams.lid) {
                loadLesson($stateParams.lid);
            }
        } else {
            $scope.lesson = $stateParams.lesson;
        }
    }

    ng.controller('LessonListCtrl', LessonListCtrl);
    ng.controller('LessonCtrl', LessonCtrl);
    ng.directive('fileModel', ['$parse', function ($parse) {
        return {
            link: function (scope, el, attrs) {
                el.bind('change', function (e) {
                    var file = e.target.files[0];
                    var model = $parse(attrs.fileModel);
                    model.assign(scope, file ? file : undefined);
                });
            }
        };
    }]);
})(angular.module(APP_MODULE_NAME));