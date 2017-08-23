/*
@copyright 2015. iZ Hero
Created by FxHarvest LLP
*/

'use strict';


(function(ng){

    /** @ngInject */
    function EncyclopediaCtrl($scope, $http, $state, $stateParams, BASE_URL){
        var self = this;
        $scope.lang = $stateParams.lang || 'en';

        $scope.categories = [];
        $scope.create = function() {
            $state.go('encyclopedia.category_create', {lang: $scope.lang});
        };
        $scope.edit = function(row) {
            $state.go('encyclopedia.category_edit', {cid: row._id, c: row, lang: row.lang});
        };
        $scope.go = function(row) {
            $state.go('encyclopedia.pages', {cid: row._id, lang: row.lang});
        };
        $scope.moveup = function(row) {
            if (row.order <= 1) {
                return;
            }
            $http.put(BASE_URL + 'encyclopedia', {id: row._id, order: row.order-1})
                .success(function(res) {
                    if (res.success) {
                        row.order -= 1;
                        for (var i = 0; i < $scope.categories.length; i++) {
                            if (row._id == $scope.categories[i]._id) {
                                var tmp = $scope.categories[i];
                                $scope.categories[i] = $scope.categories[i-1];
                                $scope.categories[i-1] = tmp;
                                break;
                            }
                        }
                    }
                })
        };
        $scope.movedown = function(row) {
            $http.put(BASE_URL + 'encyclopedia', {id: row._id, order: row.order+1})
                .success(function(res) {
                    if (res.success) {
                        row.order += 1;
                        for (var i = 0; i < $scope.categories.length; i++) {
                            if (row._id == $scope.categories[i]._id) {
                                var tmp = $scope.categories[i];
                                $scope.categories[i] = $scope.categories[i+1];
                                $scope.categories[i+1] = tmp;
                                break;
                            }
                        }
                    }
                });
        };

        $scope.refresh = function() {
            $http.get(BASE_URL + 'encyclopedia', {params: {lang: $scope.lang}})
                .success(function(res) {
                    $scope.categories = res.items;
                });
        }

        $scope.refresh();
    }

    /** @ngInject */
    function ECategoryCtrl($scope, $http, $state, $stateParams, BASE_URL) {
        var self = this;

        $scope.category = $stateParams.c || {};
        $scope.lang = $stateParams.lang || 'en';
        $scope.categories = [];

        $http.get(BASE_URL + 'encyclopedia', {params: {lang: $scope.lang}})
            .success(function(res) {
                $scope.categories = res.items;
            });

        $scope.back = function() {
            $state.go('encyclopedia.category', {lang: $scope.lang});
        };

        $scope.save = function() {
            var p;
            var category = _.clone($scope.category);

            if (!category.lang) {
                category.lang = $scope.lang;
            }

            if (!category._id) {
                p = $http.post(BASE_URL + 'encyclopedia', category);
            } else {
                delete category._id;
                p = $http.put(BASE_URL + 'encyclopedia/item/' + $scope.category._id, category);
            }
            p.success(function(res) {
                if (res.success) {
                    $scope.back();
                }
            });
        };
    }

    /** @ngInject */
    function PagesCtrl($scope, $http, $state, $stateParams, BASE_URL){
        if (!$stateParams.cid) {
            $state.go('encyclopedia.category');
            return;
        }

        $scope.pages = [];
        $scope.lang = $stateParams.lang;
        $scope.create = function() {
            $state.go('encyclopedia.page_create', {cid: $stateParams.cid, lang: $scope.lang});
        };
        $scope.back = function() {
            $state.go('encyclopedia.category', {lang: $scope.lang});
        };
        $scope.edit = function(row) {
            $state.go('encyclopedia.page_edit', {pid: row._id, p: row, lang: row.lang});
        };
        $scope.moveup = function(row) {
            if (row.order <= 1) {
                return;
            }
            $http.put(BASE_URL + 'encyclopedia/pages', {id: row._id, order: row.order-1})
                .success(function(res) {
                    if (res.success) {
                        row.order -= 1;
                        for (var i = 0; i < $scope.pages.length; i++) {
                            if (row._id == $scope.pages[i]._id) {
                                var tmp = $scope.pages[i];
                                $scope.pages[i] = $scope.pages[i-1];
                                $scope.pages[i-1] = tmp;
                                break;
                            }
                        }
                    }
                })
        };
        $scope.movedown = function(row) {
            $http.put(BASE_URL + 'encyclopedia/pages', {id: row._id, order: row.order+1})
                .success(function(res) {
                    if (res.success) {
                        row.order += 1;
                        for (var i = 0; i < $scope.pages.length; i++) {
                            if (row._id == $scope.pages[i]._id) {
                                var tmp = $scope.pages[i];
                                $scope.pages[i] = $scope.pages[i+1];
                                $scope.pages[i+1] = tmp;
                                break;
                            }
                        }
                    }
                });
        };

        $http.get(BASE_URL + 'encyclopedia/pages', {params: {category: $stateParams.cid}})
            .success(function(res) {
                $scope.pages = res.items;
            });
    }

    /** @ngInject */
    function PageCtrl($scope, $http, $state, $stateParams, BASE_URL) {
        if (!$stateParams.cid && !$stateParams.p) {
            return;
        }
        var self = this;

        $scope.lang = $stateParams.lang;
        $scope.back = function() {
            $state.go('encyclopedia.pages', {cid: $stateParams.cid||$scope.page.category, lang: $scope.lang});
        };
        $scope.page = $stateParams.p || {};
        if ($stateParams.cid) {
            $scope.page.category = $stateParams.cid;
        }

        $scope.save = function() {
            var p;
            var page = _.clone($scope.page);

            if (!page._id) {
                p = $http.post(BASE_URL + 'encyclopedia/pages', page);
            } else {
                delete page._id;
                p = $http.put(BASE_URL + 'encyclopedia/pages/item/' + $scope.page._id, page);
            }
            p.success(function(res) {
                if (res.success) {
                    $scope.back();
                }
            });
        };
    }

    ng.controller('EncyclopediaCtrl', EncyclopediaCtrl);
    ng.controller('ECategoryCtrl', ECategoryCtrl);
    ng.controller('PagesCtrl', PagesCtrl);
    ng.controller('PageCtrl', PageCtrl);

})(angular.module(APP_MODULE_NAME));