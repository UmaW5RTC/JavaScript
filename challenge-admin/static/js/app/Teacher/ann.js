/*
@copyright 2015. iZ Hero
Created by FxHarvest LLP
*/
'use strict';

(function(ng){

    /** @ngInject */
    function AnnListCtrl($scope, $http, $state) {
        var self = this;

        $scope.ui = {
            total_items: 0,
            max_pages: 0,
            current_page: 1,
            sort: null,
            grid_opts: {
                useExternalSorting: true,
                useExternalPagination: true,
                paginationPageSize: 25,
                paginationPageSizes: [25],

                columnDefs: [
                      {field: '_id', visible: false},
                      {field: 'title', displayName: 'Subject', width: 900, cellTemplate: '<div class="ui-grid-cell-contents"><a ng-click="grid.appScope.view(row.entity)"><strong>{{row.entity.title}}</strong> {{row.entity.summary}}</a></div>'},
                      {field: 'created.username', displayName: 'By', width: 100},
                      {name: 'createdon', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.created.on && (row.entity.created.on | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                       displayName: 'Published On', width: 150}
                    ],
                onRegisterApi: function(gridApi) {
                    $scope.gridApi = gridApi;

                    gridApi.pagination.on.paginationChanged($scope, function (newPage) {
                        $scope.ui.current_page = newPage;
                        getData();
                    });

                    gridApi.core.on.sortChanged( $scope, function( grid, sortColumns ) {
                        if( sortColumns.length === 0){
                            self.ui.sort = null;
                            getData(gridApi);
                        } else {
                            var i = sortColumns.length - 1;
                            self.ui.sort = sortColumns[i].field;
                            if (sortColumns[i].sort.direction == uiGridConstants.DESC) {
                                self.ui.sort = '-' + self.ui.sort;
                            } else if (!angular.isDefined(sortColumns[i].sort.direction)) {
                                self.ui.sort = null;
                            }
                            getData(gridApi);
                        }
                    });
                },
                data: []
            }
        };

        function getData() {
            var params = {p: $scope.ui.current_page};
            if ($scope.ui.sort) {
                params['o'] = $scope.ui.sort;
            }

            $http.get('anns', {params: params})
                .success(function(res){
                    $scope.ui.grid_opts.data = res.items;
                    $scope.ui.total_items = res.count;
                    $scope.ui.grid_opts.totalItems = res.count;
                    $scope.ui.max_pages = res.pages;
                });
        }

        $scope.view = function (entity) {
            $state.go('anns.view', {id: entity._id, entity: entity});
        };

        getData();
    }

    /** @ngInject */
    function AnnCtrl($scope, $http, $state, $stateParams) {
        $scope.data = {};
        $scope.ui = {
            busy: false
        };

        if ($stateParams.id) {
            if ($stateParams.entity && $stateParams.entity._id) {
                $scope.data = $stateParams.entity;
            }

            $http.get('anns/item/' + $stateParams.id)
                .success(function (res) {
                    $scope.data = res;
                }).error(function() {
                    $scope.ui.busy = false;
                });
        } else {
            $state.go('anns.list');
        }
    }

    /** @ngInject */
    function FeedbackListCtrl($scope, $http, $state) {
        var self = this;

        $scope.ui = {
            total_items: 0,
            max_pages: 0,
            current_page: 1,
            sort: null,
            grid_opts: {
                useExternalSorting: true,
                useExternalPagination: true,
                paginationPageSize: 25,
                paginationPageSizes: [25],

                columnDefs: [
                      {field: '_id', visible: false},
                      {field: 'title', displayName: 'Subject', width: 900, cellTemplate: '<div class="ui-grid-cell-contents"><a ng-click="grid.appScope.view(row.entity)"><strong>{{row.entity.title}}</strong> {{row.entity.summary}}</a></div>'},
                      {field: 'created.username', displayName: 'By', width: 100},
                      {name: 'createdon', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.created.on && (row.entity.created.on | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                       displayName: 'On', width: 150}
                    ],
                onRegisterApi: function(gridApi) {
                    $scope.gridApi = gridApi;

                    gridApi.pagination.on.paginationChanged($scope, function (newPage) {
                        $scope.ui.current_page = newPage;
                        getData();
                    });

                    gridApi.core.on.sortChanged( $scope, function( grid, sortColumns ) {
                        if( sortColumns.length === 0){
                            self.ui.sort = null;
                            getData(gridApi);
                        } else {
                            var i = sortColumns.length - 1;
                            self.ui.sort = sortColumns[i].field;
                            if (sortColumns[i].sort.direction == uiGridConstants.DESC) {
                                self.ui.sort = '-' + self.ui.sort;
                            } else if (!angular.isDefined(sortColumns[i].sort.direction)) {
                                self.ui.sort = null;
                            }
                            getData(gridApi);
                        }
                    });
                },
                data: []
            }
        };

        function getData() {
            var params = {p: $scope.ui.current_page};
            if ($scope.ui.sort) {
                params['o'] = $scope.ui.sort;
            }

            $http.get('messages', {params: params})
                .success(function(res){
                    $scope.ui.grid_opts.data = res.items;
                    $scope.ui.total_items = res.count;
                    $scope.ui.grid_opts.totalItems = res.count;
                    $scope.ui.max_pages = res.pages;
                });
        }

        $scope.view = function (entity) {
            $state.go('anns.feedback_view', {id: entity._id, entity: entity});
        };

        getData();
    }

    /** @ngInject */
    function FeedbackCtrl($scope, $http, $state, $stateParams) {
        $scope.data = {};
        $scope.r = {
            body: ''
        };
        $scope.ui = {
            busy: false
        };

        $scope.save = function(model) {
            if ($scope.ui.busy) return;
            $scope.ui.busy = true;

            $http.post('messages', model)
                .success(function (res) {
                    $scope.ui.busy = false;
                    $state.go('anns.feedbacks');
                }).error(function () {
                    $scope.ui.busy = false;
                });
        };

        $scope.reply = function(model) {
            if ($scope.ui.busy || !$scope.data._id) return;
            $scope.ui.busy = true;

            $http.post('messages/item/' + $scope.data._id, model)
                .success(function (res) {
                    $scope.ui.busy = false;
                    $scope.data.replies = res.item.replies;
                }).error(function () {
                    $scope.ui.busy = false;
                });
        };

        if ($stateParams.id) {
            if ($stateParams.entity && $stateParams.entity._id) {
                $scope.data = $stateParams.entity;
            } else {
                $http.get('messages/item/' + $stateParams.id)
                    .success(function (res) {
                        $scope.data = res;
                    }).error(function() {
                        $scope.ui.busy = false;
                    });
            }
        }
    }

    ng.controller('AnnListCtrl', AnnListCtrl);
    ng.controller('AnnCtrl', AnnCtrl);
    ng.controller('FeedbackListCtrl', FeedbackListCtrl);
    ng.controller('FeedbackCtrl', FeedbackCtrl);
})(angular.module(APP_MODULE_NAME));