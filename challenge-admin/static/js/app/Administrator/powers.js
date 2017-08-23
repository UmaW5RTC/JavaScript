/*
@copyright 2015. iZ Hero
Created by FxHarvest LLP
*/

'use strict';


(function(ng){

    /** @ngInject */
    function PowerRootCtrl($scope, $state, $http, BASE_URL){
        function loadCategories(name) {
            $http.get(BASE_URL + 'powers/' + name)
                .success(function (res) {
                    $scope[name] = res.items;
                });
        }

        loadCategories('competencies');
        loadCategories('values');
        loadCategories('topics');

        $scope.to_power = function (p) {
            $state.go('powers.power', {pid: p._id, power: p});
        };

        $scope.edit = function (p) {
            $state.go('powers.power_edit', {pid: p._id, power: p});
        };

        $scope.to_mission = function (mission) {
            $state.go('powers.mission', {m: mission, mid: mission._id});
        };

        $scope.edit_mission = function (mission) {
            $state.go('powers.mission_edit', {m: mission, mid: mission._id});
        };

        $scope.create_mission = function (p) {
            $state.go('powers.mission_create', {pid: p._id});
        };

        $scope.cancel = function (mission) {
            if (mission && mission.power_id) {
                $state.go('powers.power', {pid: mission.power_id});
            } else {
                $state.go('powers.list');
            }
        };
    }

    /** @ngInject */
    function PowerListCtrl($scope, $http, BASE_URL, $state){
        $scope.respect = [];

        $http.get(BASE_URL + 'powers')
            .success(function (res) {
                if (res.items) {
                    $scope.respect = res.items;
                }
            });
    }

    /** @ngInject */
    function PowerCtrl($scope, $http, $state, $stateParams, BASE_URL) {
        $scope.ui = {
            success: null,
            busy: false
        };

        function loadMissions(pid) {
            if (!$scope.ui.busy) {
                $scope.ui.busy = true;
                $http.get(BASE_URL + 'powers/missions', {params: {power: pid}})
                    .success(function (res) {
                        $scope.ui.busy = false;
                        $scope.missions = res.items;
                    }).error(function () {
                        $scope.ui.busy = false;
                    });
            }
        }

        function loadPower(pid) {
            if (!$scope.ui.busy) {
                $scope.ui.busy = true;
                $http.get(BASE_URL + 'powers/item/' + pid)
                    .success(function (res) {
                        $scope.ui.busy = false;
                        loadMissions(res._id);
                        $scope.p = res;
                    }).error(function () {
                        $scope.ui.busy = false;
                    });
            }
        }

        $scope.save = function (power) {
            if (!$scope.ui.busy) {
                $scope.ui.busy = true;
                $http.put(BASE_URL + 'powers/item/' + power._id, power)
                    .success(function (res) {
                        $scope.ui.success = res.success;
                        $scope.ui.busy = false;
                        $scope.cancel();
                    }).error(function () {
                        $scope.ui.success = false;
                        $scope.ui.busy = false;
                    });
            }
        };

        if (!$stateParams.p || !$stateParams.p._id) {
            if (!$stateParams.pid) {
                $scope.cancel();
                return;
            }

            loadPower($stateParams.pid);
        } else {
            $scope.p = $stateParams.p;
            loadMissions($stateParams.p._id);
        }
    }

    /** @ngInject */
    function MissionCtrl($scope, $http, $state, $stateParams, BASE_URL) {
        $scope.ui = {
            success: null,
            busy: false
        }

        function loadMission(mid) {
            if (!$scope.ui.busy) {
                $scope.ui.busy = true;
                $http.get(BASE_URL + 'powers/missions/item/' + mid)
                    .success(function (res) {
                        $scope.ui.busy = false;
                        $scope.m = res;
                    }).error(function () {
                        $scope.ui.busy = false;
                    });
            }
        }

        $scope.save = function (mission) {
            if (!$scope.ui.busy) {
                $scope.ui.busy = true;
                var url = BASE_URL + 'powers/missions/';
                var func = $http.post;

                if (mission._id) {
                    url += 'item/' + mission._id;
                    func = $http.put;
                }

                func(url, mission)
                    .success(function (res) {
                        $scope.ui.success = res.success;
                        $scope.ui.busy = false;
                        $scope.cancel(mission);
                    }).error(function () {
                        $scope.ui.success = false;
                        $scope.ui.busy = false;
                    });
            }
        };

        if (!$stateParams.m || !$stateParams.m._id) {
            if ($stateParams.mid) {
                loadMission($stateParams.mid);
            } else if ($stateParams.pid) {
                $scope.m = {
                    id: '',
                    code: '',
                    name: '',
                    power_id: $stateParams.pid,
                    selcompetency: null,
                    cwtopic: null,
                    cwvalue: null,
                    level: '1',
                    time: '5',
                    objective: ''
                };
            }
        } else {
            $scope.m = $stateParams.m;
        }
    }

    ng.controller('PowerRootCtrl', PowerRootCtrl);
    ng.controller('PowerListCtrl', PowerListCtrl);
    ng.controller('PowerCtrl', PowerCtrl);
    ng.controller('MissionCtrl', MissionCtrl);

})(angular.module(APP_MODULE_NAME));