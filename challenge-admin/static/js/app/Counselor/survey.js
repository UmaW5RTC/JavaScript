/*
@copyright 2015. iZ Hero
Created by FxHarvest LLP
*/
'use strict';

(function(ng){
    /** @ngInject */
    function SurveyRootCtrl($scope) {
        $scope.common_ui = {}
        $scope.data = {
            list: []
        }
    }

    /** @ngInject */
    function SurveyListCtrl($scope, $http, $state){
        var self = this;
        $scope.common_ui.selected_user_name = null;
        this.ui = {
            total_items: 0,
            grid_opts: {
                // minRowsToShow: 25,
                // infiniteScrollPercentage: 10,

                columnDefs: [
                      {field: 'id', visible: false},
                      {field: 'user_fullname', displayName: 'Name', width: 150,
                        cellTemplate: '<div class="ui-grid-cell-contents"><a ng-click="grid.appScope.view(row.entity)">{{row.entity.user_fullname}}</a></div>'},
                      {field: 'user_school', displayName: 'School', width: 150},
                      {field: 'pre', displayName: 'Pre-survey', width: 150},
                      {field: 'post', displayName: 'Post-survey', width: 150},
                      {field: 'control', displayName: 'Control-survey', width: 150},
                      {field: 'date', displayName: 'Date', width: 200,
                        cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.id.substring(4, 14)}}</a></div>'}
                    ],

                // onRegisterApi: function(gridApi){
                //     gridApi.infiniteScroll.on.needLoadMoreData($scope,function(){
                //             getData(gridApi);
                //     });
                // },

                data: []
            }
        };

        $scope.view = function(row) {
            $state.go('surveys.one', {id: row.id});
        }

        function getData() {
            //var url = '/admin/static/js/displayRecords.json';
            var url = '/counseling/Api/displayRecords';

            $http.get(url)
                .success(function(res){
                    if (res.list) {
                        $scope.data.list = res.list;
                        self.ui.grid_opts.data = _.map(res.list, function(row) {
                            return {
                                id: row.id,
                                user_fullname: row.user_details.user_fullname,
                                user_school: row.user_school.user_school,
                                pre: row.pre ? row.pre.length > 0 && 'Y' || 'N' : 0,
                                post: row.post ? row.post.length > 0 && 'Y' || 'N' : 0,
                                control: row.control ? row.control.length > 0 && 'Y' || 'N' : 0,
                            }
                        });

                        self.ui.total_items = res.length;
                    }
                })
                .error(function(res){
                });
        }

        getData();
    }

    /** @ngInject */
    function SurveyCtrl($scope, $http, $state, $stateParams) {
        var self = this;

        if (!$scope.data.list || !$scope.data.list.length) {
            $http.get('/counseling/Api/retrieveRecord/' + $stateParams.id)
                .success(function(res) {
                    self.data = res;
                    $scope.common_ui.selected_user_name = self.data.user_details.user_fullname;
                    $http.get('students/item/' + res.user_details.userid)
                        .success(function(res) {
                            if (res.parent) {
                                self.parent_info = res.parent;
                            };
                        });
                });
        }
        else {
            this.data = _.find($scope.data.list, 'id', $stateParams.id);
            $http.get('students/item/' + this.data.user_details.userid)
                .success(function(res) {
                    if (res.parent) {
                        self.parent_info = res.parent;
                    };
                });
        }

        if (this.data) {
            $scope.common_ui.selected_user_name = this.data.user_details.user_fullname;
        }

    }



    ng.controller('SurveyRootCtrl', SurveyRootCtrl);
    ng.controller('SurveyListCtrl', SurveyListCtrl);
    ng.controller('SurveyCtrl', SurveyCtrl);

})(angular.module(APP_MODULE_NAME));