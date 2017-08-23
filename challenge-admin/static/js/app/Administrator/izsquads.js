/*
@copyright 2015. iZ Hero
Created by FxHarvest LLP
*/

'use strict';


(function(ng){

    /** @ngInject */
    function IZSquadListCtrl($scope, $http, $state, $timeout, uiGridConstants, BASE_URL){
        var filterTimeout = null,
            grid_api = null,
            genExcelTimeout = null;

        $scope.ui = {
            genexcel: null,
            total_items: 0,
            max_pages: 0,
            current_page: 1,
            sort: null,
            filter: null,

            grid_opts: {
                enableRowSelection: true,
                enableSelectAll: true,
                enableRowHeaderSelection: true,
                enableFullRowSelection: true,
                useExternalFiltering: true,
                useExternalSorting: true,
                useExternalPagination: true,
                paginationPageSize: 25,
                paginationPageSizes: [25],
                enableFiltering: true,

                columnDefs: [
                      {field: '_id', visible: false},
                      {field: 'squads.name', displayName: 'Squad Name', width: 250, enableFiltering:false},
                      {field: 'squads.code', displayName: 'Code', width: 80, enableFiltering:false},
                      {field: 'squads.grade', displayName: 'Grade', width: 100, enableFiltering:false},
                      {field: 'squads.school', displayName: 'School', width: 200, enableFiltering:false},
                      {field: 'country', displayName: 'Country', width: 100, enableFiltering:false},
                      {field: 'username', displayName: 'Username', width: 150, enableFiltering:true},
                      {field: 'givenname', displayName: "Given Name", width: 150, enableFiltering:false},
                      {field: 'familyname', displayName: "Family Name", width: 150, enableFiltering:false},
                      {field: 'email', displayName: "Email", width: 200, enableFiltering:false},
                      {field: 'contact', displayName: "Contact", width: 100, enableFiltering:false}
                    ],

                onRegisterApi: function(gridApi){
                    grid_api = gridApi;

                    gridApi.pagination.on.paginationChanged($scope, function (newPage) {
                        $scope.ui.current_page = newPage;
                        getData();
                    });
                    gridApi.core.on.sortChanged( $scope, function( grid, sortColumns ) {
                        if( sortColumns.length === 0){
                            $scope.ui.sort = null;
                            getData();
                        } else {
                            var i = sortColumns.length-1;
                            $scope.ui.sort = sortColumns[i].field;
                            if (sortColumns[i].sort.direction == uiGridConstants.DESC) {
                                $scope.ui.sort = '-' + $scope.ui.sort;
                            } else if (!angular.isDefined(sortColumns[i].sort.direction)) {
                                $scope.ui.sort = null;
                            }
                            getData();
                        }
                    });
                    gridApi.core.on.filterChanged($scope, function() {
                        var grid = this.grid;
                        $scope.ui.current_page = 1;

                        if(angular.isDefined(grid.columns[7].filters[0].term)) {
                            $scope.ui.filter = grid.columns[7].filters[0].term;
                        } else {
                            $scope.ui.filter = null;
                        }

                        if (filterTimeout) {
                            $timeout.cancel(filterTimeout);
                        }
                        filterTimeout = $timeout(function () {
                            getData();
                        }, 500);
                    });
                },

                data: []
            }
        };

        $scope.deleteSquads = function (with_hero) {
            if ($scope.ui.busy) return;
            $scope.ui.busy = true;
            var msg = 'Are you sure you want to delete the squads?'

            if (with_hero) {
                msg = 'Are you sure you want to delete the squads AND the iZ HEROES accounts associated with the Squad?'
            }

            if (confirm(msg)
            && confirm('Once deleted they cannot be restored back.')) {
                var rows = grid_api.selection.getSelectedRows();
                var params = {"code": []};
                grid_api.selection.clearSelectedRows();

                if (angular.isArray(rows) && rows.length > 0) {
                    for (var i = 0; i < rows.length; i++) {
                        params["code"].push(rows[i].squads.code);
                    }
                    if (with_hero) {
                        params["with_izhero"] = true;
                    }
                    $http.delete('izsquads', {params: params})
                        .success(function (res) {
                            $scope.ui.busy = false;
                            getData();
                        }).error(function () {
                            $scope.ui.busy = false;
                        });
                } else {
                    $scope.ui.busy = false;
                }
            } else {
                $scope.ui.busy = false;
            }
        };

        function getData() {
            if (!$scope.ui.max_pages || $scope.ui.current_page <= $scope.ui.max_pages) {
                var params = {p: $scope.ui.current_page};
                if ($scope.ui.sort) {
                    params['o'] = $scope.ui.sort;
                }
                if ($scope.ui.filter) {
                    params['s'] = $scope.ui.filter;
                }

                $http.get('izsquads', {params: params})
                    .success(function(res){
                        $scope.ui.grid_opts.data = res.items;
                        $scope.ui.total_items = res.count;
                        $scope.ui.grid_opts.totalItems = res.count;
                        $scope.ui.max_pages = res.pages;
                    });
            }
        }
        getData();

        $scope.$on("$destroy", function () {
            $timeout.cancel(filterTimeout);
            $timeout.cancel(genExcelTimeout);
        });

        $scope.genExcel = function() {
            $scope.ui.genexcel = true;
            $http.post(BASE_URL + 'izsquads/export')
                .success(function(res) {
                    if (res.working) {
                        $timeout.cancel(genExcelTimeout);
                        genExcelTimeout = $timeout(function() {
                            $scope.genExcel();
                        }, 4000);
                    } else if (!res.working && res.exid) {
                        $scope.ui.genexcel = false;
                        window.location = BASE_URL + 'izsquads/export?exid=' + res.exid;
                    }
                })
                .error(function() {
                    $scope.ui.genexcel = false;
                    alert('Unable to generate excel file.')
                });
        };

        $scope.genMStartExcel = function() {
            genMissionExcel('start');
        };

        $scope.genMSlideExcel = function() {
            genMissionExcel('slide');
        };

        $scope.genMCompleteExcel = function() {
            genMissionExcel('complete');
        };

        $scope.genMLikeExcel = function() {
            genMissionExcel('like');
        };

        function genMissionExcel(sub) {
            $scope.ui.genexcel = true;
            $http.post(BASE_URL + 'dqmissions/export_' + sub)
                .success(function(res) {
                    if (res.working) {
                        $timeout.cancel(genExcelTimeout);
                        genExcelTimeout = $timeout(function() {
                            genMissionExcel(sub);
                        }, 4000);
                    } else if (!res.working && res.exid) {
                        $scope.ui.genexcel = false;
                        window.location = BASE_URL + 'dqmissions/export_' + sub + '?exid=' + res.exid;
                    }
                })
                .error(function() {
                    $scope.ui.genexcel = false;
                    alert('Unable to generate excel file.')
                });
        }
    }

    ng.controller('IZSquadListCtrl', IZSquadListCtrl);

})(angular.module(APP_MODULE_NAME));
