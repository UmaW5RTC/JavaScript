/*
@copyright 2015. iZ Hero
Created by FxHarvest LLP
*/

'use strict';


(function(ng){

    /** @ngInject */
    function UserListCtrl($scope, $http, BASE_URL, $timeout){

        var self = this,
            genExcelTimeout = null;
        this.ui = {
            genexcel: false,
            total_items: 0,
            grid_opts: {
                minRowsToShow: 25,
                infiniteScrollPercentage: 10,

                columnDefs: [
                      {field: 'id', visible: false},
                      {field: 'name', displayName: 'Name', width: 150},
                      {field: 'email', displayName: 'Email', width: 150},
                      {field: 'firstname', displayName: 'First Name', width: 150},
                      {field: 'lastname', displayName: 'Last Name', width: 150},
                      {field: 'guardiansemail', displayName: 'Guardian\'s Email', width: 150},
                      {field: 'points', displayName: 'Points', width: 80},
                      {field: 'type', displayName: 'Type', width: 80, enableColumnResizing: false},
                      {field: 'schoolname', displayName: 'School', width: 150},
                      {field: 'classname', displayName: 'Class', width: 150},
                      {name: 'logindate', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.lastlogindate | moment_date:"YYYY-MM-DD hh:mm a"}}</div>', displayName: 'Last Login', width: 150},
                      {field: 'status', displayName: 'Status', width: 70, enableColumnResizing: false},
                      {name: 'guardiansack', displayName: 'G.Ack', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.guardiansack && "Y" || "N"}}</div>', width: 70, enableColumnResizing: false},
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

        }

        $scope.$on("$destroy", function () {
            $timeout.cancel(genExcelTimeout);
        });

        $scope.genExcel = function(single) {
            self.ui.genexcel = true;
            $http.post(BASE_URL + 'users/exportfull' + (single ? '?single=true' : ''))
                .success(function(res) {
                    if (res.working) {
                        $timeout.cancel(genExcelTimeout);
                        genExcelTimeout = $timeout(function() {
                            $scope.genExcel(single);
                        }, 4000);
                    } else if (!res.working && res.exid) {
                        self.ui.genexcel = false;
                        window.location = BASE_URL + 'users/exportfull?exid=' + res.exid + (single ? '&single=true' : '');;
                    }
                })
                .error(function() {
                    self.ui.genexcel = false;
                    alert('Unable to generate excel file.')
                });
        };

        var current_page = 1;
        function getData(gridApi) {
            $http.get('users/?p=' + current_page)
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

    /** @ngInject */
    function IZHEROListCtrl($scope, $http, $state, $timeout, uiGridConstants, BASE_URL) {
        var self = this,
            filterTimeout = null,
            genExcelTimeout = null;

        this.ui = {
            total_items: 0,
            squads_list: [],
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
                      {field: 'givenname', displayName: 'Given Name', width:150, enableCellEdit:true, enableFiltering:false},
                      {field: 'familyname', displayName: 'Family Name', width:120, enableCellEdit:true, enableFiltering:false},
                      {field: 'school', displayName: 'School', width: 200, enableCellEdit:true, enableFiltering:false},
                      {field: 'points', displayName: 'iZP', width:80, enableCellEdit:false, enableFiltering:false},
                      {field: 'dq_points', displayName: 'Score', width:80, enableCellEdit:false, enableFiltering:false},
                      {name: 'created', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.created && (row.entity.created | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                       displayName: 'Created', width: 150, enableFiltering:false},
                      {name: 'lastlogin', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.lastlogin && (row.entity.lastlogin | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                       displayName: 'Last Login', width: 150, enableFiltering:false},
                      {field: 'parent.email', displayName: 'Email', width:200, enableCellEdit:false, enableFiltering:false},
                      {field: 'squad.code', displayName: 'Squad Code', width:100, enableCellEdit:false, enableFiltering:false},
                      {field: 'coins', displayName: 'Coin', width:60, enableCellEdit:false, enableFiltering:false},
                      {field: 'dq_coins', displayName: 'DQ Coin', width:60, enableCellEdit:false, enableFiltering:false},
                      {field: 'dq_level', displayName: 'DQ Level', width:60, enableCellEdit:false, enableFiltering:false},
                      {field: 'donated', displayName: 'Donated', width:80, enableCellEdit:false, enableFiltering:false, enableFiltering:false},
                      {field: 'dq_progress.screentimebadge.first', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.dq_progress.screentimebadge.first && (row.entity.dq_progress.screentimebadge.first | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                      displayName: 'Screen Time Badge', enableCellEdit:false, enableFiltering:false, width:150},
                      {field: 'dq_progress.privacybadge.first', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.dq_progress.privacybadge.first && (row.entity.dq_progress.privacybadge.first | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                      displayName: 'Privacy Badge', enableCellEdit:false, enableFiltering:false, width:150},
                      {field: 'dq_progress.cyberbullyingbadge.first', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.dq_progress.cyberbullyingbadge.first && (row.entity.dq_progress.cyberbullyingbadge.first | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                      displayName: 'Cyberbullying Badge', enableCellEdit:false, enableFiltering:false, width:150},
                      {field: 'dq_progress.digitalcitizensbadge.first', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.dq_progress.digitalcitizensbadge.first && (row.entity.dq_progress.digitalcitizensbadge.first | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                      displayName: 'Digital Citizens Badge', enableCellEdit:false, enableFiltering:false, width:150},
                      {field: 'dq_progress.digitalfootprintbadge.first', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.dq_progress.digitalfootprintbadge.first && (row.entity.dq_progress.digitalfootprintbadge.first | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                      displayName: 'Digital Footprint Badge', enableCellEdit:false, enableFiltering:false, width:150},
                      {field: 'dq_progress.securitybadge.first', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.dq_progress.securitybadge.first && (row.entity.dq_progress.securitybadge.first | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                      displayName: 'Security Badge', enableCellEdit:false, enableFiltering:false, width:150},
                      {field: 'dq_progress.criticalthinkingbadge.first', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.dq_progress.criticalthinkingbadge.first && (row.entity.dq_progress.criticalthinkingbadge.first | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                      displayName: 'Critical Thinking Badge', enableCellEdit:false, enableFiltering:false, width:150},
                      {field: 'dq_progress.empathybadge.first', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.dq_progress.empathybadge.first && (row.entity.dq_progress.empathybadge.first | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                      displayName: 'Empathy Badge', enableCellEdit:false, enableFiltering:false, width:150},
                      /*{field: 'points_stage.e2', displayName: 'iZ RADAR iZPs', enableCellEdit:false, enableFiltering:false, width: 130},
                      {field: 'points_stage.e1', displayName: 'iZ EYES iZPs', enableCellEdit:false, enableFiltering:false, width: 130},
                      {field: 'points_stage.e5', displayName: 'iZ SHOUT iZPs', enableCellEdit:false, enableFiltering:false, width: 130},
                      {field: 'points_stage.e4', displayName: 'iZ PROTECT iZPs', enableCellEdit:false, enableFiltering:false, width: 130},
                      {field: 'points_stage.e6', displayName: 'iZ EARS iZPs', enableCellEdit:false, enableFiltering:false, width: 130},
                      {field: 'points_stage.e3', displayName: 'iZ CONTROL iZPs', enableCellEdit:false, enableFiltering:false, width: 130},
                      {field: 'points_stage.e7', displayName: 'iZ TELEPORT iZPs', enableCellEdit:false, enableFiltering:false, width: 130},*/
                      /*{field: 'progress.2._completed', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.progress[2]._completed && (row.entity.progress[2]._completed | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                      displayName: 'iZ RADAR Complete', enableCellEdit:false, enableFiltering:false, width:150},
                      {field: 'progress.1._completed', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.progress[1]._completed && (row.entity.progress[1]._completed | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                      displayName: 'iZ EYES Complete', enableCellEdit:false, enableFiltering:false, width:150},
                      {field: 'progress.5._completed', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.progress[5]._completed && (row.entity.progress[5]._completed | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                      displayName: 'iZ SHOUT Complete', enableCellEdit:false, enableFiltering:false, width:150},
                      {field: 'progress.4._completed', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.progress[4]._completed && (row.entity.progress[4]._completed | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                      displayName: 'iZ PROTECT Complete', enableCellEdit:false, enableFiltering:false, width:150},
                      {field: 'progress.6._completed', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.progress[6]._completed && (row.entity.progress[6]._completed | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                      displayName: 'iZ EARS Complete', enableCellEdit:false, enableFiltering:false, width:150},
                      {field: 'progress.3._completed', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.progress[3]._completed && (row.entity.progress[3]._completed | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                      displayName: 'iZ CONTROL Complete', enableCellEdit:false, enableFiltering:false, width:150},
                      {field: 'progress.7._completed', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.progress[7]._completed && (row.entity.progress[7]._completed | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                      displayName: 'iZ TELEPORT Complete', enableCellEdit:false, enableFiltering:false, width:150},*/
                      {field: 'status', displayName: 'Status', width:80, enableCellEdit:true, enableFiltering:false, type: 'boolean'},
                      {field: 'guardiansack', displayName: 'Guardian Ack.', width:100, enableCellEdit:true, enableFiltering:false, type: 'boolean'},
                      {name: "edit", displayName: 'Edit', enableCellEdit:false, enableFiltering:false, cellTemplate: '<div class="ui-grid-cell-contents"><button ng-click="grid.appScope.edit(row.entity)" type="button" class="btn-xs btn-warning">Edit</button></div>', width:80},
                      {name: "resendact", displayName: 'Resend Activation', enableCellEdit:false, enableFiltering:false, cellTemplate: '<div ng-show="!row.entity.guardiansack&&row.entity.parent.email" class="ui-grid-cell-contents"><button ng-click="grid.appScope.resendact(row.entity)" type="button" class="btn-xs btn-warning">Resend Activation</button></div>', width:180}
                    ],
                onRegisterApi: function(gridApi) {
                    $scope.gridApi = gridApi;
                    gridApi.pagination.on.paginationChanged($scope, function (newPage) {
                        self.ui.current_page = newPage;
                        getData();
                    });
                    gridApi.edit.on.afterCellEdit($scope, function(rowEntity, colDef, newValue, oldValue) {
                        if (colDef.field == 'status') {
                            if (newValue != oldValue) {
                                if (newValue) {
                                    $http.post('students/status/' + rowEntity._id)
                                        .success(function(res) {
                                        })
                                        .error(function(res) {
                                        });
                                } else {
                                    $http.delete('students/status/' + rowEntity._id)
                                        .success(function(res) {
                                        })
                                        .error(function(res) {
                                        });
                                }
                            }
                        }
                        else if (colDef.field == 'guardiansack') {
                            if (newValue != oldValue) {
                                if (newValue) {
                                    $http.post('students/guardack/' + rowEntity._id)
                                        .success(function(res) {
                                        })
                                        .error(function(res) {
                                        });
                                } else {
                                    $http.delete('students/guardack/' + rowEntity._id)
                                        .success(function(res) {
                                        })
                                        .error(function(res) {
                                        });
                                }
                            }
                        }
                        else if (newValue && newValue != oldValue) {
                            var params = {};
                            params[colDef.field] = newValue;
                            $http.put('students/item/' + rowEntity._id, params)
                                .success(function(res){
                                    // success
                                })
                                .error(function(res) {
                                });
                        }
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
                $http.get('students/', {params: params})
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
            $http.post(BASE_URL + 'students/export')
                .success(function(res) {
                    if (res.working) {
                        $timeout.cancel(genExcelTimeout);
                        genExcelTimeout = $timeout(function() {
                            $scope.genExcel();
                        }, 4000);
                    } else if (!res.working && res.exid) {
                        self.ui.genexcel = false;
                        window.location = BASE_URL + 'students/export?exid=' + res.exid;
                    }
                })
                .error(function() {
                    self.ui.genexcel = false;
                    alert('Unable to generate excel file.')
                });
        };

        $scope.edit= function(row) {
            $state.go('users.izhero_edit', {izhero: row, id: row._id});
        };

        $scope.resendact = function(row) {
            if (confirm("Are you sure you want to resend "+row.username+"'s activation email?")) {
                $http.post('students/update/' + row._id)
                    .success(function() {
                        alert('Activation email has been sent to ' + row.parent.email + '.');
                    });
            }
        };

        $scope.deleteAccounts = function() {
            if (self.ui.busy) return;
            self.ui.busy = true;

            if (confirm('Are you sure you want to delete the accounts?')
            && confirm('Once deleted they cannot be restored back.')) {
                var rows = $scope.gridApi.selection.getSelectedRows();
                var params = {"id": []};
                $scope.gridApi.selection.clearSelectedRows();

                if (angular.isArray(rows) && rows.length > 0) {
                    for (var i = 0; i < rows.length; i++) {
                        params["id"].push(rows[i]._id);
                    }
                    $http.delete('students/', {params: params})
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
    }

    /** @ngInject */
    function IZHEROCtrl($scope, $http, $state, $stateParams){
        $scope.ui = {
            busy: false,
            username_in_use: false
        };
        $scope.data = $stateParams.izhero;

        $http.get('students/item/' + $stateParams.id)
            .success(function (res) {
                if (res) {
                    $scope.data = res;
                }
            });

        $scope.save = function (hero) {
            $scope.ui.busy = true;
            $scope.ui.username_in_use = false;

            if (hero._id) {
                var obj = {
                    'username': hero.username,
                    'points': hero.points,
                    'coins': hero.coins,
                    'guardiansack': hero.guardiansack ? 'true' : 'false'
                };
                $http.put('students/update/' + hero._id, obj)
                    .success(function (res) {
                        $scope.ui.busy = false;
                        if (res.success) {
                            $state.go('users.izheroes');
                        } else if (res.errorcode && res.errorcode > 100) {
                            $scope.ui.username_in_use = true;
                        }
                    })
                    .error(function (res) {
                        $scope.ui.busy = false;
                    });
            } else {
                $state.go('users.izheroes');
            }
        };

        $scope.cancel = function () {
            $state.go('users.izheroes');
        };

        $scope.resetdq = function() {
            if ($scope.data._id && confirm('Are you sure you want to reset the DQ progress?')) {
                $scope.ui.busy = true;
                $http.post('students/resetdq/' + $scope.data._id)
                    .success(function () {
                        $scope.ui.busy = false;
                        $state.go('users.izheroes');
                    }).error(function() {
                        $scope.ui.busy = false;
                    });
            }
        };
    }

    /** @ngInject */
    function TeacherListCtrl($scope, $http, $state, $timeout, uiGridConstants, BASE_URL) {
        var self = this,
            filterTimeout = null,
            genExcelTimeout = null;

        this.ui = {
            genexcel: null,
            total_items: 0,
            squads_list: [],
            max_pages: 0,
            current_page: 0,
            sort: null,
            filter: null,
            grid_opts: {
                enableFiltering: true,
                useExternalSorting: true,
                useExternalFiltering: true,
                columnDefs: [
                      {field: '_id', visible: false},
                      {field: 'username', displayName: 'Username', width: 250, enableCellEdit:false},
                      {field: 'givenname', displayName: 'Given Name', width:150, enableCellEdit:true, enableFiltering:false},
                      {field: 'familyname', displayName: 'Family Name', width:150, enableCellEdit:true, enableFiltering:false},
                      {field: 'country', displayName: 'Country', width:150, enableCellEdit:false, enableFiltering:false},
                      {field: 'school', displayName: 'School', width:150, enableCellEdit:true, enableFiltering:false},
                      {field: 'referral', displayName: 'Access Code', width:100, enableCellEdit:true, enableFiltering:false},
                      {field: 'contact', displayName: 'Contact No.', width:100, enableCellEdit:false, enableFiltering:false},
                      {field: 'status', displayName: 'Status', width:100, enableCellEdit:true, enableFiltering:false, type: 'boolean'},
                      {name: 'created', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.created && (row.entity.created | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                       displayName: 'Created', width: 150, enableFiltering:false},
                      {name: 'lastlogin', cellTemplate: '<div class="ui-grid-cell-contents">{{row.entity.lastlogin && (row.entity.lastlogin | moment_date:"YYYY-MM-DD hh:mm a")}}</div>',
                       displayName: 'Last Login', width: 150, enableFiltering:false},
                      {field: 'email', displayName: 'Email', width: 200, enableCellEdit:false},
                      {name: "resendact", displayName: 'Resend Activation', enableCellEdit:false, enableFiltering:false, cellTemplate: '<div ng-show="!row.entity.status&&row.entity.email" class="ui-grid-cell-contents"><button ng-click="grid.appScope.resendact(row.entity)" type="button" class="btn-xs btn-warning">Resend Activation</button></div>', width:180},
                      {name: "edit", displayName: 'Change Password', enableCellEdit:false, enableFiltering:false, cellTemplate: '<div class="ui-grid-cell-contents"><button ng-click="grid.appScope.edit(row.entity)" type="button" class="btn-xs btn-warning">Change Password</button></div>', width: 150}
                    ],
                onRegisterApi: function(gridApi) {
                    $scope.gridApi = gridApi;
                    gridApi.infiniteScroll.on.needLoadMoreData($scope, function(){
                        getData(gridApi);
                    });
                    gridApi.edit.on.afterCellEdit($scope, function(rowEntity, colDef, newValue, oldValue) {
                        if (colDef.field == 'status') {
                            if (newValue != oldValue) {
                                if (newValue) {
                                    $http.post('teachers/status/' + rowEntity._id)
                                        .success(function(res) {
                                        })
                                        .error(function(res) {
                                        });
                                } else {
                                    $http.delete('teachers/status/' + rowEntity._id)
                                        .success(function(res) {
                                        })
                                        .error(function(res) {
                                        });
                                }
                            }
                        }
                        else if (newValue && newValue != oldValue) {
                            var params = {};
                            params[colDef.field] = newValue;
                            $http.put('teachers/item/' + rowEntity._id, params)
                                .success(function(res){
                                    // success
                                })
                                .error(function(res) {
                                });
                        }
                    });
                    gridApi.core.on.sortChanged( $scope, function( grid, sortColumns ) {
                        self.ui.current_page = 0;
                        if( sortColumns.length === 0){
                            self.ui.sort = null;
                            getData(gridApi);
                        } else {
                            self.ui.sort = sortColumns[0].field;
                            if (sortColumns[0].sort.direction == uiGridConstants.DESC) {
                                self.ui.sort = '-' + self.ui.sort;
                            } else if (!angular.isDefined(sortColumns[0].sort.direction)) {
                                self.ui.sort = null;
                            }
                            getData(gridApi);
                        }
                    });
                    gridApi.core.on.filterChanged($scope, function() {
                        var grid = this.grid;
                        self.ui.current_page = 0;

                        if(angular.isDefined(grid.columns[1].filters[0].term)) {
                            self.ui.filter = grid.columns[1].filters[0].term;
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
            if (!self.ui.max_pages || self.ui.current_page < self.ui.max_pages) {
                self.ui.current_page++;
                var params = {p: self.ui.current_page}
                if (self.ui.sort) {
                    params['o'] = self.ui.sort;
                }
                if (self.ui.filter) {
                    params['s'] = self.ui.filter;
                }
                $http.get('teachers/', {params: params})
                    .success(function(res){
                        if (res.items) {
                            if (self.ui.current_page == 1) {
                                self.ui.grid_opts.data = res.items;
                            } else {
                                self.ui.grid_opts.data = self.ui.grid_opts.data.concat(res.items);
                            }
                        }
                        self.ui.total_items = (res.pages === 1 && res.items.length) || res.pages * 25;
                        self.ui.max_pages = res.pages;
                        if (gridApi) gridApi.infiniteScroll.dataLoaded();
                    })
                    .error(function(res){
                        if (gridApi) gridApi.infiniteScroll.dataLoaded();
                    });
            } else if (gridApi) {
                //gridApi.infiniteScroll.dataLoaded();
            }
        }

        getData();

        $scope.$on("$destroy", function (event) {
            $timeout.cancel(filterTimeout);
            $timeout.cancel(genExcelTimeout);
        });

        $scope.genExcel = function() {
            self.ui.genexcel = true;
            $http.post(BASE_URL + 'teachers/export')
                .success(function(res) {
                    if (res.working) {
                        $timeout.cancel(genExcelTimeout);
                        genExcelTimeout = $timeout(function() {
                            $scope.genExcel();
                        }, 4000);
                    } else if (!res.working && res.exid) {
                        self.ui.genexcel = false;
                        window.location = BASE_URL + 'teachers/export?exid=' + res.exid;
                    }
                })
                .error(function() {
                    self.ui.genexcel = false;
                    alert('Unable to generate excel file.')
                });
        };

        $scope.resendact = function(row) {
            if (confirm("Are you sure you want to resend "+row.username+"'s activation email?")) {
                $http.put('teachers/activate/' + row._id)
                    .success(function() {
                        alert('Activation email has been sent to ' + row.email + '.');
                    });
            }
        };

        $scope.edit= function(row) {
            $state.go('users.teacher_edit', {teacher: row, id: row._id});
        };
    }

    /** @ngInject */
    function TeacherCtrl($scope, $http, $state, $stateParams){
        $scope.ui = {
            busy: false
        };
        $scope.data = $stateParams.teacher;

        if (!$scope.data || !$scope.data.username) {
            $http.get('teachers/item/' + $stateParams.id)
                .success(function (res) {
                    if (res) {
                        $scope.data = res;
                    }
                });
        }

        $scope.save = function (teacher) {
            if (teacher._id && confirm("Are you sure you want to change the teacher's password?")) {
                $scope.ui.busy = true;
                var obj = {
                    'password': teacher.password
                };
                $http.put('teachers/item/' + teacher._id, obj)
                    .success(function (res) {
                        $scope.ui.busy = false;
                        if (res.success) {
                            $state.go('users.teachers');
                        }
                    })
                    .error(function (res) {
                        $scope.ui.busy = false;
                    });
            } else {
                $state.go('users.teachers');
            }
        };

        $scope.cancel = function () {
            $state.go('users.teachers');
        };
    }

    ng.controller('UserListCtrl', UserListCtrl);
    ng.controller('IZHEROListCtrl', IZHEROListCtrl);
    ng.controller('IZHEROCtrl', IZHEROCtrl);
    ng.controller('TeacherListCtrl', TeacherListCtrl);
    ng.controller('TeacherCtrl', TeacherCtrl);

})(angular.module(APP_MODULE_NAME))


;

