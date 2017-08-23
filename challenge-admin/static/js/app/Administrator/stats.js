/*
@copyright 2015. iZ Hero
Created by FxHarvest LLP
*/

'use strict';


(function(ng){
    var default1 = {backgroundColor: "rgba(100,100,255,0.5)",
                    borderColor: "rgba(100,100,255,1)",
                    pointBackgroundColor: "rgba(100,100,255,1)",
                    pointBorderColor: "#fff",
                    pointHoverBackgroundColor: "rgba(100,100,255,1)",
                    pointHoverBorderColor: "rgba(100,100,255,1)",
                    borderWidth: 2},
        default2 = {label: "Cumulative New Users",
                    backgroundColor: "rgba(255,100,100,1)",
                    borderColor: "rgba(255,50,50,1)",
                    pointBackgroundColor: "rgba(255,50,50,1)",
                    pointBorderColor: "#fff",
                    pointHoverBackgroundColor: "rgba(255,50,50,1)",
                    pointHoverBorderColor: "rgba(255,50,50,1)",
                    borderWidth: 2},
        options = {elements: {line: {tension:0}}}

    function render_chart(label, arr, chart, canvas) {
        var data = {
                labels: [],
                datasets: [_.extend({
                        label: label,
                        data: []
                    }, default1),
                    _.extend({
                        data: []
                    }, default2)
                ]
            },
            total = 0;

        for (var i in arr) {
            var d = arr[i];
            data.labels.push(d.year + '-' + d.month + (angular.isDefined(d.day) ? '-' + d.day : '') + (angular.isDefined(d.hour) ? ' ' + d.hour + ':00' : ''));
            data.datasets[0].data.push(d.count);
            total += d.count;
            data.datasets[1].data.push(total);
        }

        if (chart) {
            chart.destroy();
        }

        chart = new Chart(canvas, {type: 'line', data: data, options: options});

        return [chart, total];
    }

    /** @ngInject */
    function StatsCtrl($scope, $http, $state){
        var self = this,
            monthlyusers = document.getElementById("monthlyusers").getContext("2d"),
            dailyusers = document.getElementById("dailyusers").getContext("2d"),
            hourlyusers = document.getElementById("hourlyusers").getContext("2d"),
            monthlychart = null,
            dailychart = null,
            hourlychart = null;

        $scope.ui = {
            loggedin: 0
        };
        $scope.data = {};
        $scope.total = {
            year: 0,
            month: 0,
            day: 0
        };

        $scope.getMonth = function(year, month) {
            $http.get('stats', {params: {year: year, month: month, loggedin: $scope.ui.loggedin}})
                .success(function (res) {
                    $scope.data.days = res.days;

                    var dchart = render_chart("Daily New Users", $scope.data.days, dailychart, dailyusers);
                    dailychart = dchart[0];
                    $scope.total.month = dchart[1];
                });
        };

        $scope.getDay = function(year, month, day) {
            $http.get('stats', {params: {year: year, month: month, day: day, loggedin: $scope.ui.loggedin}})
                .success(function (res) {
                    $scope.data.hours = res.hours;

                    var hchart = render_chart("Hourly New Users", $scope.data.hours, hourlychart, hourlyusers);
                    hourlychart = hchart[0];
                    $scope.total.day = hchart[1];
                });
        };

        function initData() {
            $http.get('stats', {params: {loggedin: $scope.ui.loggedin}})
                .success(function(res){
                    $scope.data = res;

                    var mchart = render_chart("Monthly New Users", $scope.data.months, monthlychart, monthlyusers);
                    monthlychart = mchart[0];
                    $scope.total.year = mchart[1];

                    var dchart = render_chart("Daily New Users", $scope.data.days, dailychart, dailyusers);
                    dailychart = dchart[0];
                    $scope.total.month = dchart[1];
                });
        }

        $scope.$watch('ui.loggedin', function (newVal, oldVal) {
            if (newVal !== oldVal) {
                initData();
            }
        });

        initData();
    }

    /** @ngInject */
    function StatsSchoolCtrl($scope, $http, $state, uiGridConstants, $timeout, BASE_URL){
        var grid_api = null,
            monthly = document.getElementById("monthly").getContext("2d"),
            daily = document.getElementById("daily").getContext("2d"),
            hourly = document.getElementById("hourly").getContext("2d"),
            monthlychart = null,
            dailychart = null,
            hourlychart = null,
            genExcelTimeout = null;

        $scope.data = {};
        $scope.total = {};
        $scope.ui = {
            genexcel: false,
            school: null,
            loggedin: 0,
            countries: [],
            country: 'Singapore',
            total_items: 0,
            max_pages: 0,
            current_page: 1,
            sort: null,
            filter: null,

            grid_opts: {
                useExternalSorting: true,
                useExternalPagination: true,
                paginationPageSize: 25,
                paginationPageSizes: [25],

                columnDefs: [
                      {field: 'schools', displayName: 'School', width: 300},
                      {field: 'count', displayName: 'No. Users', cellTemplate: '<div class="ui-grid-cell-contents"><a ng-click="grid.appScope.monthchart(row.entity.schools, 0)">{{row.entity.count}}</a></div>', width: 150, enableSorting:false},
                      {field: 'count_loggedin', displayName: 'No. Users (Logged In)', cellTemplate: '<div class="ui-grid-cell-contents"><a ng-click="grid.appScope.monthchart(row.entity.schools, 1)">{{row.entity.count_loggedin}}</a></div>', width: 200, enableSorting:false},
                      {field: 'points', displayName: 'Total iZPs', cellTemplate: '<div class="ui-grid-cell-contents"><a ng-click="grid.appScope.monthchart(row.entity.schools, 1)">{{row.entity.points}}</a></div>', width: 150, enableSorting:false},
                      {field: 'donated', displayName: 'Total Donations', cellTemplate: '<div class="ui-grid-cell-contents"><a ng-click="grid.appScope.monthchart(row.entity.schools, 1)">{{row.entity.donated}}</a></div>', width: 150, enableSorting:false}
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
                },

                data: []
            }
        };

        $http.get('countries/list')
            .success(function (res) {
                if (res.countries) {
                    $scope.ui.countries = res.countries;
                    if (!$scope.ui.country) {
                        $scope.ui.country = 'Singapore';
                    }
                }
            });

        function getData() {
            var params = {p: $scope.ui.current_page, country: $scope.ui.country};
            if ($scope.ui.sort) {
                params['o'] = $scope.ui.sort;
            }

            $http.get('stats/schools', {params: params})
                .success(function(res){
                    $scope.ui.grid_opts.data = res.items;
                    $scope.ui.total_items = res.count;
                    $scope.ui.grid_opts.totalItems = res.count;
                    $scope.ui.max_pages = res.pages;
                });
        }

        getData();

        $scope.$watch('ui.country', function (newVal, oldVal) {
            if (newVal != oldVal) {
                getData();
            }
        });

        $scope.monthchart = function(school, loggedin) {
            $scope.ui.school = school;
            $scope.ui.loggedin = loggedin;
            var params = {school: $scope.ui.school, loggedin: $scope.ui.loggedin, country: $scope.ui.country};

            $http.get('stats/schools', {params: params})
                .success(function(res){
                    $scope.data.months = res.months;
                    var mchart = render_chart("Monthly New Users", res.months, monthlychart, monthly);
                    monthlychart = mchart[0];
                    $scope.total.year = mchart[1];
                });
        };

        $scope.daychart = function(year, month) {
            var params = {school: $scope.ui.school, loggedin: $scope.ui.loggedin, country: $scope.ui.country,
                          year: year, month: month};

            $http.get('stats/schools', {params: params})
                .success(function(res){
                    $scope.data.days = res.days;
                    var dchart = render_chart("Daily New Users", res.days, dailychart, daily);
                    dailychart = dchart[0];
                    $scope.total.month = dchart[1];
                });
        };

        $scope.hourchart = function(year, month, day) {
            var params = {school: $scope.ui.school, loggedin: $scope.ui.loggedin, country: $scope.ui.country,
                          year: year, month: month, day: day};

            $http.get('stats/schools', {params: params})
                .success(function(res){
                    $scope.data.hours = res.hours;
                    var hchart = render_chart("Hourly New Users", res.hours, hourlychart, hourly);
                    hourlychart = hchart[0];
                    $scope.total.day = hchart[1];
                });
        };

        $scope.$on("$destroy", function () {
            $timeout.cancel(genExcelTimeout);
        });

        $scope.genExcel = function(c) {
            $scope.ui.genexcel = true;
            if (!angular.isDefined(c)) {
                c = $scope.ui.country;
            }

            $http.post(BASE_URL + 'stats/schools/export?country=' + c)
                .success(function(res) {
                    if (res.working) {
                        $timeout.cancel(genExcelTimeout);
                        genExcelTimeout = $timeout(function() {
                            $scope.genExcel(c);
                        }, 4000);
                    } else if (!res.working && res.exid) {
                        $scope.ui.genexcel = false;
                        window.location = BASE_URL + 'stats/schools/export?exid=' + res.exid + '&country=' + c;
                    }
                })
                .error(function() {
                    $scope.ui.genexcel = false;
                    alert('Unable to generate excel file.')
                });
        };
    }

    ng.controller('StatsCtrl', StatsCtrl);
    ng.controller('StatsSchoolCtrl', StatsSchoolCtrl);

})(angular.module(APP_MODULE_NAME));