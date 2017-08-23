/*
@copyright 2015. iZ Hero
Created by FxHarvest LLP
*/

'use strict';


(function(ng){

    /** @ngInject */
    function MemberListCtrl($scope, $http, $state){

        var self = this;
        this.ui = {
            total_items: 0,
            max_pages: 0,
            current_page: 0,

            grid_opts: {
                infiniteScrollPercentage: 10,

                columnDefs: [
                      {field: 'username', displayName: 'Username', width: 150},
                      {name: 'code', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.code|code_humanify}}</div>', displayName: 'Access Code', width: 150},
                      //{field: 'duration', displayName: 'Duration', width: 100},
                      {name: 'started', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.started|moment_date:"YYYY-MM-DD hh:mm a"}}</div>', displayName: 'Account Creation', width: 150},
                      //{name: 'expiry', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.expiry|moment_date:"YYYY-MM-DD hh:mm a"}}</div>', displayName: 'Expiry', width: 150},
                      {field: 'dqreport', displayName: 'DQ Report', width: 100},
                      {field: 'receipt', displayName: 'Receipt No.', width: 150},
                      {field: 'school', displayName: 'School', width: 150},
                      {field: 'sponsor', displayName: 'Sponsor', width: 150},
                      {field: 'byadminname', displayName: 'Created By', width: 150},
                      {name: 'createdon', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.createdon|moment_date:"YYYY-MM-DD hh:mm a"}}</div>', displayName: 'Created On', width: 150}
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
            if (!self.ui.max_pages || current_page <= self.ui.max_pages) {
                $http.get('members/?p=' + current_page)
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
    function MemberCtrl($scope, $http, $state, $stateParams){
        $scope.ui = {
            busy: false
        };
        $scope.data = $stateParams.member || {'duration': 0, 'dqreport': 1};

        $scope.save = function (mem) {
            $scope.ui.busy = true;
            var obj = {
                'sponsor': mem.sponsor,
                'dqreport': mem.dqreport
            };

            if (mem._id) {
                $http.put('members/item/' + mem._id, obj)
                    .success(function (res) {
                        $scope.ui.busy = false;
                        $state.go('users.members');
                    })
                    .error(function (res) {
                        $scope.ui.busy = false;
                    });
            } else {
                $http.post('members/', obj)
                    .success(function (res) {
                        $scope.ui.busy = false;
                        $state.go('users.members');
                    })
                    .error(function (res) {
                        $scope.ui.busy = false;
                    });
            }
        };

        $scope.cancel = function () {
            $state.go('users.members');
        };
    }

    /** @ngInject */
    function SchoolMemberListCtrl($scope, $http, $state){

        var self = this;
        this.ui = {
            total_items: 0,
            max_pages: 0,
            current_page: 0,

            grid_opts: {
                infiniteScrollPercentage: 10,

                columnDefs: [
                      {field: 'username', displayName: 'Username', width: 150},
                      {name: 'code', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.code|code_humanify}}</div>', displayName: 'Access Code', width: 150},
                      {field: 'membership.assigned', displayName: 'Used Accounts', width: 150},
                      {field: 'membership.count', displayName: 'Total Accounts', width: 150},
                      {field: 'receipt', displayName: 'Receipt No.', width: 150},
                      {field: 'school', displayName: 'School', width: 150},
                      {field: 'sponsor', displayName: 'Sponsor', width: 150},
                      {field: 'byadminname', displayName: 'Created By', width: 150},
                      {name: 'createdon', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.createdon|moment_date:"YYYY-MM-DD hh:mm a"}}</div>', displayName: 'Created On', width: 150}
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
            if (!self.ui.max_pages || current_page <= self.ui.max_pages) {
                $http.get('schoolmembers/?p=' + current_page)
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
    function SchoolMemberCtrl($scope, $http, $state, $stateParams){
        $scope.ui = {
            busy: false
        };
        $scope.data = $stateParams.member || {'duration': 0, 'dqreport': 1};

        $scope.save = function (mem) {
            $scope.ui.busy = true;
            var obj = {
                'sponsor': mem.sponsor,
                'count': mem.count
            };

            if (mem._id) {
                $http.put('schoolmembers/item/' + mem._id, obj)
                    .success(function (res) {
                        $scope.ui.busy = false;
                        $state.go('users.schoolmembers');
                    })
                    .error(function (res) {
                        $scope.ui.busy = false;
                    });
            } else {
                $http.post('schoolmembers/', obj)
                    .success(function (res) {
                        $scope.ui.busy = false;
                        $state.go('users.schoolmembers');
                    })
                    .error(function (res) {
                        $scope.ui.busy = false;
                    });
            }
        };

        $scope.cancel = function () {
            $state.go('users.schoolmembers');
        };
    }

    ng.controller('MemberListCtrl', MemberListCtrl);
    ng.controller('MemberCtrl', MemberCtrl);
    ng.controller('SchoolMemberListCtrl', SchoolMemberListCtrl);
    ng.controller('SchoolMemberCtrl', SchoolMemberCtrl);
    ng.filter('code_humanify', function() {
        return function(s) {
            if (!angular.isString(s)) {
                return s;
            }
            s = s.toUpperCase();
            var chars = s.slice(1),
                s = s[0],
                i = 0;

            for (var i = 0; i < chars.length; i++) {
                var c = chars[i],
                    j = i + 1;
                if (j % 4 == 0) {
                    s += '-';
                }
                s += c;
            }
            return s;
        };
    });
})(angular.module(APP_MODULE_NAME))


;

