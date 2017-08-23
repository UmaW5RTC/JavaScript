/*
@copyright 2015. iZ Hero
Created by FxHarvest LLP
*/

'use strict';


(function(ng){

    /** @ngInject */
    function PretestListCtrl($scope, $http, $state, $timeout, uiGridConstants, BASE_URL) {
        var self = this,
            filterTimeout = null,
            genExcelTimeout = null;

        this.ui = {
            total_items: 0,
            max_pages: 0,
            current_page: 0,
            sort: null,
            filter: null,
            busy: null,
            grid_opts: {
                enableFiltering: true,
                useExternalSorting: true,
                useExternalFiltering: true,
                enableRowSelection: true,
                enableSelectAll: false,
                enableRowHeaderSelection: true,
                enableFullRowSelection: true,
                useExternalPagination: true,
                paginationPageSize: 25,
                paginationPageSizes: [25],
                columnDefs: [
                      {field: '_id', visible: false},
                      {field: 'username', displayName: 'Username', width: 180, enableCellEdit:false},
                      {field: 'demo_name_first', displayName: 'demo_name_first', width: 150, enableCellEdit:false, enableFiltering:false},
                      {field: 'demo_name_last', displayName: 'demo_name_last', width:150, enableCellEdit:false, enableFiltering:false},
                      {field: 'demo_gender', displayName: 'demo_gender', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'demo_birthyear', displayName: 'demo_birthyear', width: 100, enableCellEdit:false, enableFiltering:false},
                      {field: 'demo_country', displayName: 'demo_country', width: 100, enableCellEdit:false, enableFiltering:false},
                      {field: 'pri_pi_beh_pre_1', displayName: 'pri_pi_beh_pre_1', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'pri_pi_beh_pre_2', displayName: 'pri_pi_beh_pre_2', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'pri_pi_beh_pre_3', displayName: 'pri_pi_beh_pre_3', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'pri_pi_beh_pre_4', displayName: 'pri_pi_beh_pre_4', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'pri_pi_beh_pre_5', displayName: 'pri_pi_beh_pre_5', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'pri_pi_beh_pre_6', displayName: 'pri_pi_beh_pre_6', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'pri_pi_beh_pre_7', displayName: 'pri_pi_beh_pre_7', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'pri_pi_beh_pre_8', displayName: 'pri_pi_beh_pre_8', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'pri_pi_beh_pre_9', displayName: 'pri_pi_beh_pre_9', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'pri_pi_beh_pre_10', displayName: 'pri_pi_beh_pre_10', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'pri_pi_beh_pre_11', displayName: 'pri_pi_beh_pre_11', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'pri_pi_beh_pre_12', displayName: 'pri_pi_beh_pre_12', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'pri_pi_beh_pre_13', displayName: 'pri_pi_beh_pre_13', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'pri_decide_pre', displayName: 'pri_decide_pre', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'pri_pri_skill_pre_1', displayName: 'pri_pri_skill_pre_1', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'pri_pri_skill_pre_2', displayName: 'pri_pri_skill_pre_2', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'pri_pri_skill_pre_3', displayName: 'pri_pri_skill_pre_3', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'pri_pri_skill_pre_4', displayName: 'pri_pri_skill_pre_4', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'pri_pri_skill_pre_5', displayName: 'pri_pri_skill_pre_5', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_beh_pre_1', displayName: 'df_beh_pre_1', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_beh_pre_2', displayName: 'df_beh_pre_2', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_beh_pre_3', displayName: 'df_beh_pre_3', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_beh_pre_4', displayName: 'df_beh_pre_4', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_beh_pre_5', displayName: 'df_beh_pre_5', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_beh_pre_6', displayName: 'df_beh_pre_6', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_beh_pre_7', displayName: 'df_beh_pre_7', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_beh_pre_8', displayName: 'df_beh_pre_8', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_beh_pre_9', displayName: 'df_beh_pre_9', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_beh_pre_10', displayName: 'df_beh_pre_10', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_dp_quiz_pre_1_1', displayName: 'df_dp_quiz_pre_1_1', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_dp_quiz_pre_1_2', displayName: 'df_dp_quiz_pre_1_2', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_dp_quiz_pre_1_3', displayName: 'df_dp_quiz_pre_1_3', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_dp_quiz_pre_1_4', displayName: 'df_dp_quiz_pre_1_4', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_dp_quiz_pre_12_1', displayName: 'df_dp_quiz_pre_12_1', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_dp_quiz_pre_12_2', displayName: 'df_dp_quiz_pre_12_2', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_dp_quiz_pre_12_3', displayName: 'df_dp_quiz_pre_12_3', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_dp_quiz_pre_12_4', displayName: 'df_dp_quiz_pre_12_4', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_dp_quiz_pre_12_5', displayName: 'df_dp_quiz_pre_12_5', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'df_dp_quiz_pre_12_6', displayName: 'df_dp_quiz_pre_12_6', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'dc_dt_du_1', displayName: 'dc_dt_du_1', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'dc_dt_du_2', displayName: 'dc_dt_du_2', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'dc_dt_du_3', displayName: 'dc_dt_du_3', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'dc_dt_du_4', displayName: 'dc_dt_du_4', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'dc_dt_du_5', displayName: 'dc_dt_du_5', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'dc_dt_du_6', displayName: 'dc_dt_du_6', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'dc_dt_du_7', displayName: 'dc_dt_du_7', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'dc_dt_du_8', displayName: 'dc_dt_du_8', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'dc_dt_du_9', displayName: 'dc_dt_du_9', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'dt_cong_1_p', displayName: 'dt_cong_1_p', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'dc_citizen_quiz_pre_4_1', displayName: 'dc_citizen_quiz_pre_4_1', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'dc_citizen_quiz_pre_4_2', displayName: 'dc_citizen_quiz_pre_4_2', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'dc_citizen_quiz_pre_4_3', displayName: 'dc_citizen_quiz_pre_4_3', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'dc_citizen_quiz_pre_4_4', displayName: 'dc_citizen_quiz_pre_4_4', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'ct_risk_beh_pre_1', displayName: 'ct_risk_beh_pre_1', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'ct_risk_beh_pre_2', displayName: 'ct_risk_beh_pre_2', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'ct_risk_beh_pre_3', displayName: 'ct_risk_beh_pre_3', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'ct_risk_beh_pre_4', displayName: 'ct_risk_beh_pre_4', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'ct_block_a_pre_1', displayName: 'ct_block_a_pre_1', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'ct_block_a_pre_2', displayName: 'ct_block_a_pre_2', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'ct_block_a_pre_3', displayName: 'ct_block_a_pre_3', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'ct_block_a_pre_4', displayName: 'ct_block_a_pre_4', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'ct_block_a_pre_5', displayName: 'ct_block_a_pre_5', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'ct_block_a_pre_6', displayName: 'ct_block_a_pre_6', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'ct_block_a_pre_7', displayName: 'ct_block_a_pre_7', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'ct_block_a_pre_8', displayName: 'ct_block_a_pre_8', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'ct_literacy_pre_1', displayName: 'ct_literacy_pre_1', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'ct_literacy_pre_2', displayName: 'ct_literacy_pre_2', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'ct_literacy_pre_3', displayName: 'ct_literacy_pre_3', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'cb_risk_pre', displayName: 'cb_risk_pre', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'cb_cbmgmt_pre_1', displayName: 'cb_cbmgmt_pre_1', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'cb_cbmgmt_pre_2', displayName: 'cb_cbmgmt_pre_2', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'cb_cbmgmt_pre_3', displayName: 'cb_cbmgmt_pre_3', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'cb_cbmgmt_pre_4', displayName: 'cb_cbmgmt_pre_4', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'cb_cbmgmt_pre_5', displayName: 'cb_cbmgmt_pre_5', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'cb_cbmgmt_pre_6', displayName: 'cb_cbmgmt_pre_6', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'cb_cbmgmt_pre_7', displayName: 'cb_cbmgmt_pre_7', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'cb_cbmgmt_pre_8', displayName: 'cb_cbmgmt_pre_8', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'cb_cbmgmt_pre_9', displayName: 'cb_cbmgmt_pre_9', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'cb_cbmgmt_pre_10', displayName: 'cb_cbmgmt_pre_10', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'cb_cbatt_pre', displayName: 'cb_cbatt_pre', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'cb_beh_pre', displayName: 'cb_beh_pre', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'emp_emp_6_p', displayName: 'emp_emp_6_p', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'emp_emp_8_p', displayName: 'emp_emp_8_p', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'sec_pwd_act_pre', displayName: 'sec_pwd_act_pre', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'sec_pwd_skill_pre_1', displayName: 'sec_pwd_skill_pre_1', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'sec_pwd_skill_pre_2', displayName: 'sec_pwd_skill_pre_2', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'sec_pwd_skill_pre_3', displayName: 'sec_pwd_skill_pre_3', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'sec_pwd_skill_pre_4', displayName: 'sec_pwd_skill_pre_4', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'sec_popup_pre', displayName: 'sec_popup_pre', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'bst_ga_pre_1', displayName: 'bst_ga_pre_1', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'bst_ga_pre_2', displayName: 'bst_ga_pre_2', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'bst_ga_pre_3', displayName: 'bst_ga_pre_3', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'bst_ga_pre_4', displayName: 'bst_ga_pre_4', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'dc_pm_pre_2', displayName: 'dc_pm_pre_2', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'bst_sr_pre', displayName: 'bst_sr_pre', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'preDQ_pri', displayName: 'preDQ_pri', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'preDQ_df', displayName: 'preDQ_df', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'preDQ_dc', displayName: 'preDQ_dc', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'preDQ_ct', displayName: 'preDQ_ct', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'preDQ_cb', displayName: 'preDQ_cb', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'preDQ_emp', displayName: 'preDQ_emp', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'preDQ_sec', displayName: 'preDQ_sec', width:50, enableCellEdit:false, enableFiltering:false},
                      {field: 'preDQ_bst', displayName: 'preDQ_bst', width:50, enableCellEdit:false, enableFiltering:false}
                    ],
                onRegisterApi: function(gridApi) {
                    $scope.gridApi = gridApi;
                    gridApi.pagination.on.paginationChanged($scope, function (newPage) {
                        self.ui.current_page = newPage;
                        getData();
                    });
                    gridApi.core.on.sortChanged( $scope, function( grid, sortColumns ) {
                        self.ui.current_page = 0;
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
                    gridApi.core.on.filterChanged($scope, function() {
                        var grid = this.grid;
                        self.ui.current_page = 0;

                        if(angular.isDefined(grid.columns[2].filters[0].term)) {
                            self.ui.filter = grid.columns[2].filters[0].term;
                        } else {
                            self.ui.filter = null;
                        }

                        if (filterTimeout) {
                            $timeout.cancel(filterTimeout);
                        }
                        filterTimeout = $timeout(function () {
                            getData(gridApi);
                        }, 500);
                    });
                },
                data: []
            }
        };

        function getData(gridApi) {
            if (!self.ui.max_pages || self.ui.current_page <= self.ui.max_pages) {
                var params = {p: self.ui.current_page}
                if (self.ui.sort) {
                    params['o'] = self.ui.sort;
                }
                if (self.ui.filter) {
                    params['s'] = self.ui.filter;
                }
                $http.get('dqresults/pretest/', {params: params})
                    .success(function(res){
                        self.ui.grid_opts.data = res.items;
                        self.ui.total_items = res.count;
                        self.ui.max_pages = res.pages;
                        self.ui.grid_opts.totalItems = res.count;
                    });
            } else if (gridApi) {
                //gridApi.infiniteScroll.dataLoaded();
            }
        }

        getData();

        $scope.$on("$destroy", function () {
            $timeout.cancel(filterTimeout);
            $timeout.cancel(genExcelTimeout);
        });

        $scope.genExcel = function() {
            self.ui.genexcel = true;
            $http.post(BASE_URL + 'dqresults/pretest/export')
                .success(function(res) {
                    if (res.working) {
                        $timeout.cancel(genExcelTimeout);
                        genExcelTimeout = $timeout(function() {
                            $scope.genExcel();
                        }, 4000);
                    } else if (!res.working && res.exid) {
                        self.ui.genexcel = false;
                        window.location = BASE_URL + 'dqresults/pretest/export?exid=' + res.exid;
                    }
                })
                .error(function() {
                    self.ui.genexcel = false;
                    alert('Unable to generate excel file.')
                });
        };

        $scope.deleteAccounts = function() {
            if (self.ui.busy) return;
            self.ui.busy = true;

            if (confirm('Are you sure you want to delete the dqresults?')) {
                var rows = $scope.gridApi.selection.getSelectedRows();
                var params = {"id": []};
                $scope.gridApi.selection.clearSelectedRows();

                if (angular.isArray(rows) && rows.length > 0) {
                    for (var i = 0; i < rows.length; i++) {
                        params["id"].push(rows[i]._id);
                    }
                    $http.delete('dqresults/pretest/', {params: params})
                        .success(function (res) {
                            self.ui.busy = false;
                            self.ui.current_page = 0;
                            getData();
                        }).error(function () {
                            self.ui.busy = false;
                        });
                } else {
                    self.ui.busy = false;
                }
            } else {
                self.ui.busy = false;
            }
        };

        $scope.calcResult = function(username) {
            if (username && username.length>=3) {
                if (self.ui.busy) return;
                self.ui.busy = true;

                $http.post('dqresults/pretest/', {username: username})
                    .success(function(res) {
                        self.ui.busy = false;
                        if (res.success) {
                            getData();
                        }
                    }).error(function() {
                        self.ui.busy = false;
                    });
            }
        }
    }

    ng.controller('PretestListCtrl', PretestListCtrl);

})(angular.module(APP_MODULE_NAME))


;

