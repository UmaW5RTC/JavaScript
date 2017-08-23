/*
@copyright 2015. iZ Hero
Created by FxHarvest LLP
*/
'use strict';

(function(ng){

    /** @ngInject */
    function AccessCodeCtrl($scope, $http, $state, $stateParams) {
        $scope.data = {};
        $scope.r = {
            body: ''
        };
        $scope.ui = {
            busy: false,
            error: false
        };

        $scope.save = function(model) {
            if ($scope.ui.busy) return;
            $scope.ui.busy = true;

            $http.post('teachers/accesscode', {membership: model.accesscode})
                .success(function (res) {
                    if (res.success) {
                        $scope.ui.busy = false;
                        $state.go('squads.list');
                    } else {
                        $scope.ui.busy = false;
                        $scope.ui.error = true;
                    }
                }).error(function () {
                    $scope.ui.busy = false;
                    $scope.ui.error = true;
                });
        };
    }

    ng.controller('AccessCodeCtrl', AccessCodeCtrl);
})(angular.module(APP_MODULE_NAME));