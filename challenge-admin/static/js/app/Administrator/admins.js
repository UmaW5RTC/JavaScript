/*
@copyright 2015. iZ Hero
Created by FxHarvest LLP
*/

'use strict';


(function(ng){

    /** @ngInject */
    function AdminListCtrl($scope, $http, $state){

        var self = this;
        this.ui = {
            total_items: 0,
            max_pages: 0,
            current_page: 0,

            grid_opts: {
                infiniteScrollPercentage: 10,

                columnDefs: [
                      {field: 'email', displayName: 'Email', width: 250},
                      {field: 'name', displayName: 'Name', width: 250},
                      {field: 'status', displayName: 'Status', width: 70},
                      {field: 'role', displayName: 'Role', width: 150},
                      {name: "edit", displayName: 'Edit', cellTemplate: '<div class="ui-grid-cell-contents"><button ng-click="grid.appScope.edit(row.entity)" type="button" class="btn-xs btn-warning">Edit</button></div>', width: 150}
                    ],

                onRegisterApi: function(gridApi){
                    gridApi.infiniteScroll.on.needLoadMoreData($scope,function(){
                            getData(gridApi);
                    });
                },

                data: []
            }
        };

        $scope.edit = function(row) {
            $state.go('users.admins_edit', {admin: row});
        };

        var current_page = 1;
        function getData(gridApi) {
            if (!self.ui.max_pages || current_page <= self.ui.max_pages) {
                $http.get('admins/?p=' + current_page)
                    .success(function(res){
                        self.ui.grid_opts.data = self.ui.grid_opts.data.concat(res.items);
                        self.ui.total_items = res.pages == 1 ? res.items.length : res.pages * 25;
                        self.ui.max_pages = res.pages;

                        current_page++;

                        if (gridApi) gridApi.infiniteScroll.dataLoaded();
                    })
                    .error(function(res){
                        if (gridApi) gridApi.infiniteScroll.dataLoaded();
                    });
            }
        }

        getData();

    }

    /** @ngInject */
    function AdminCtrl($scope, $http, $state, $stateParams){
        $scope.ui = {
            busy: false,
            password_req: false
        };
        $scope.data = $stateParams.admin || {'email': '', 'name': '', 'role': 'Administrator', 'password': ''};

        $scope.save = function (admin) {
            $scope.ui.busy = true;

            if (admin._id) {
                var obj = {
                    'email': admin.email,
                    'name': admin.name,
                    'role': admin.role
                };
                if (admin.password && admin.password.length >= 6) {
                    obj.password = admin.password;
                }
                $http.put('admins/item/' + admin._id, obj)
                    .success(function (res) {
                        $scope.ui.busy = false;
                        $state.go('users.admins');
                    })
                    .error(function (res) {
                        $scope.ui.busy = false;
                    });
            } else {
                if (!admin.password || admin.password.length < 6) {
                    $scope.ui.password_req = true;
                }
                $http.post('admins/', admin)
                    .success(function (res) {
                        $scope.ui.busy = false;
                        $state.go('users.admins');
                    })
                    .error(function (res) {
                        $scope.ui.busy = false;
                    });
            }
        };

        $scope.cancel = function () {
            $state.go('users.admins');
        };
    }

    ng.controller('AdminListCtrl', AdminListCtrl);
    ng.controller('AdminCtrl', AdminCtrl);

})(angular.module(APP_MODULE_NAME))


;

