/*
@copyright 2015. iZ Hero
Created by FxHarvest LLP
*/

'use strict';


(function(ng){

    /** @ngInject */
    function UnverifSchoolListCtrl($scope, $http, $state, $timeout, uiGridConstants){
        var filterTimeout = null,
            grid_api = null;

        $scope.ui = {
            total_items: 0,
            current_page: 1,
            school_list: [],
            selected_school: null,
            school: null,
            izheroes: [],
            squads: [],
            teachers: [],

            grid_opts: {
                paginationPageSize: 20,
                paginationPageSizes: [204],
                rowHeight: 40,

                columnDefs: [
                      {name: 'school', cellTemplate: '<div class="ui-grid-cell-contents"><a ng-click="grid.appScope.one(row.entity)" class="btn btn-sm btn-primary">{{row.entity}}</a></div>', displayName: 'School Name'},
                    ],

                data: []
            },

            grid_squad_opts: {
                enableRowSelection: true,
                enableSelectAll: true,
                enableRowHeaderSelection: true,
                enableFullRowSelection: true,

                columnDefs: [
                      {field: 'code', displayName: 'Squad Code', width:'100'},
                      {field: 'name', displayName: 'Squad Name'}
                    ],

                onRegisterApi: function(gridApi) {
                    $scope.gridSquadApi = gridApi;
                },

                data: []
            },

            grid_teacher_opts: {
                enableRowSelection: true,
                enableSelectAll: true,
                enableRowHeaderSelection: true,
                enableFullRowSelection: true,

                columnDefs: [
                      {field: '_id', visible: false},
                      {field: 'username', displayName: 'Teacher Username'}
                    ],

                onRegisterApi: function(gridApi) {
                    $scope.gridTeachApi = gridApi;
                },

                data: []
            },

            grid_izhero_opts: {
                enableRowSelection: true,
                enableSelectAll: true,
                enableRowHeaderSelection: true,
                enableFullRowSelection: true,

                columnDefs: [
                      {field: '_id', visible: false},
                      {field: 'username', displayName: 'iZ HERO Username'}
                    ],

                onRegisterApi: function(gridApi) {
                    $scope.gridIzheroApi = gridApi;
                },

                data: []
            }
        };

        $scope.one = function (school) {
            $scope.ui.school = school;
            $http.get('schools/unverif/Singapore/' + school)
                .success(function(res) {
                    $scope.ui.grid_izhero_opts.data = res.izheroes;
                    $scope.ui.grid_squad_opts.data = res.squads;
                    $scope.ui.grid_teacher_opts.data = res.teachers;
                });
        };

        $scope.rename = function () {
            if ($scope.ui.school && $scope.ui.selected_school && $scope.ui.selected_school != '') {
                var herorows = $scope.gridIzheroApi.selection.getSelectedRows();
                var teachrows = $scope.gridTeachApi.selection.getSelectedRows();
                var squadrows = $scope.gridSquadApi.selection.getSelectedRows();
                var params = {"users_id": [],
                              "teachers_id": [],
                              "squads_id": [],
                              "rename": $scope.ui.selected_school};
                var update = false;

                $scope.gridIzheroApi.selection.clearSelectedRows();
                $scope.gridTeachApi.selection.clearSelectedRows();
                $scope.gridSquadApi.selection.clearSelectedRows();

                if (angular.isArray(herorows) && herorows.length > 0) {
                    for (var i = 0; i < herorows.length; i++) {
                        params["users_id"].push(herorows[i]._id);
                    }
                    update = true;
                }
                if (angular.isArray(teachrows) && teachrows.length > 0) {
                    for (var i = 0; i < teachrows.length; i++) {
                        params["teachers_id"].push(teachrows[i]._id);
                    }
                    update = true;
                }
                if (angular.isArray(squadrows) && squadrows.length > 0) {
                    for (var i = 0; i < squadrows.length; i++) {
                        params["squads_id"].push(squadrows[i].code);
                    }
                    update = true;
                }

                if (update) {
                    $http.put('schools/unverif/Singapore/' + $scope.ui.school, params);
                    $scope.ui.school = null;
                }
            }
        };

        $scope.cancel = function () {
            $scope.ui.school = null;
            $scope.ui.grid_izhero_opts.data = [];
            $scope.ui.grid_squad_opts.data = [];
            $scope.ui.grid_teacher_opts.data = [];
        };

        function getData() {
            $http.get('schools/list/Singapore')
                .success(function(res) {
                    if (res.schools) {
                        $scope.ui.school_list = res.schools;
                    }
                });
            $http.get('schools/unverif/Singapore')
                .success(function(res){
                    if (res.schools) {
                        $scope.ui.grid_opts.data = res.schools;
                        $scope.ui.total_items = res.schools.length;
                        $scope.ui.grid_opts.totalItems = res.schools.length;
                    }
                });
        }
        getData();
    }

    ng.controller('UnverifSchoolListCtrl', UnverifSchoolListCtrl);

})(angular.module(APP_MODULE_NAME));
