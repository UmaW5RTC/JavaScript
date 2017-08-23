/*
@copyright 2015. iZ Hero
Created by FxHarvest LLP
*/

'use strict';


(function(ng){

    /** @ngInject */
    function MissionRootCtrl($scope) {

        $scope.common_ui = {}
    }

    /** @ngInject */
    function MissionListCtrl($scope, $http, $state){

        var self = this;

        $scope.common_ui.selected_mission_name = null;

        this.ui = {
            grid_opts: {
                columnDefs: [
                    {field: 'id', visible: false},
                      {name: 'name', displayName: 'Mission',  cellTemplate: '<div class="ui-grid-cell-contents"><a ng-click="grid.appScope.view(row.entity)" >{{row.entity.name}}</a></div>', width: 250},
                      {field: 'totalhits', displayName: 'Total Hits', width: 100}
                    ],

                onRegisterApi: function(gridApi){
                    gridApi.infiniteScroll.on.needLoadMoreData($scope,function(){
                            getData(gridApi);
                    });
                },

                data: []
            }
        };

        $scope.view = function(entity) {
            $scope.common_ui.selected_mission_name = entity.name;
            $state.go("^.detail", {id: entity.id});
        }

        var current_page = 1;
        function getData(gridApi) {
            $http.get('missions/?p=' + current_page)
                .success(function(res){
                    self.ui.grid_opts.data = self.ui.grid_opts.data.concat(res.items);
                    current_page++;

                    if (gridApi) gridApi.infiniteScroll.dataLoaded();
                })
                .error(function(res){
                    if (gridApi) gridApi.infiniteScroll.dataLoaded();
                })
        }

        getData();

    }

    /** @ngInject */
    function MissionCtrl($scope, $http, $stateParams){

        var self = this;

        this.ui = {
            total_items: 0,
            grid_opts: {
                columnDefs: [
                      {field: 'userid', visible: false},
                      {field: 'user.name', displayName: 'Username', width: 250},
                      {field: 'hits', displayName: 'Hits', width: 100}
                    ],

                onRegisterApi: function(gridApi){
                    gridApi.infiniteScroll.on.needLoadMoreData($scope,function(){
                            getData(gridApi);
                    });
                },

                data: []
            }
        };

        var current_page = 1;
        function getData(gridApi) {
            $http.get('missions/item/' + $stateParams.id + '?p=' + current_page)
                .success(function(res){
                    self.ui.grid_opts.data = self.ui.grid_opts.data.concat(res.items);
                    self.ui.total_items = res.pages * 25;
                    current_page++;

                    if (gridApi) gridApi.infiniteScroll.dataLoaded();
                })
                .error(function(res){
                    if (gridApi) gridApi.infiniteScroll.dataLoaded();
                })
        }

        getData();

    }


    ng.controller('MissionRootCtrl', MissionRootCtrl);
    ng.controller('MissionListCtrl', MissionListCtrl);
    ng.controller('MissionCtrl', MissionCtrl);

})(angular.module(APP_MODULE_NAME))


;

