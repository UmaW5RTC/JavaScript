/*
@copyright 2015. iZ Hero
Created by FxHarvest LLP
*/
'use strict';

(function(ng) {


    /** @ngInject */
    function StickerRootCtrl($scope, $http){
        $scope.common_ui = {
            selected_mission_name: null
        };
    }

    /** @ngInject */
    function StickerListCtrl($scope, $http, $timeout, $anchorScroll){
        var bound = false,
            limit = 24;

        $scope.missions = [];
        $scope.filter = {
            stage: '',
            mission: '',
            sub_mission: ''
        };
        $scope.sort = '-_id';
        $scope.open_sticker = function (stker, index) {
            $scope.sticker = stker;
            $scope.ui.has_prev = index > 0 || $scope.ui.page > 1;
            $scope.ui.has_next = index < ($scope.stickers.length - 1) || $scope.ui.page < $scope.ui.pages;
            $scope.ui.current_index = index;
            $anchorScroll();
        };
        $scope.prev = function () {
            if ($scope.sticker && $scope.ui.current_index > 0 && $scope.stickers) {
                $scope.ui.current_index -= 1;
                $scope.open_sticker($scope.stickers[$scope.ui.current_index], $scope.ui.current_index);
            } else if ($scope.ui.page > 1) {
                $scope.ui.page -= 1;
                $scope.getData(function() {
                    $scope.ui.current_index = $scope.stickers.length;
                    $scope.prev();
                })
            }
        };
        $scope.next = function () {
            if ($scope.sticker) {
                if ($scope.ui.current_index < ($scope.stickers.length - 1)) {
                    $scope.ui.current_index += 1;
                    $scope.open_sticker($scope.stickers[$scope.ui.current_index], $scope.ui.current_index);
                } else if ($scope.ui.page < $scope.ui.pages) {
                    var curpage = $scope.ui.page;
                    $scope.ui.page += 1;
                    $scope.getData(function () {
                        if ($scope.ui.page > curpage) {
                            $scope.ui.current_index = -1;
                            $scope.next();
                        }
                    });
                }
            }
        };

        $scope.open_nominate = function (sticker) {
            if (!$scope.ui.busy) {
                $scope.ui.busy = true;
                $scope.ui.nominate_box = sticker;

                $http.get('../api/gallery/item/' + sticker._id)
                    .success(function (res) {
                        if (res.nominated && res.nominated.length > 0) {
                            for (var i = 0; i < res.nominated.length; i++) {
                                if (res.nominated[i].username === 'iZ HERO TEAM') {
                                    $scope.ui.nominate_text = res.nominated[i].text;
                                    break;
                                }
                            }
                        }
                        $scope.ui.busy = false;
                    })
                    .error(function (res) {
                        $scope.ui.busy = false;
                    });
            }
        };

        $scope.close_nominate = function () {
            if (!$scope.ui.busy) {
                $scope.ui.nominate_box = null;
                $scope.ui.nominate_text = '';
            }
        };

        $scope.nominate = function (sticker) {
            if (!$scope.ui.busy) {
                $scope.ui.busy = true;

                $http.post('gallery', {sticker: sticker._id, text: $scope.ui.nominate_text})
                    .success(function (res) {
                        $scope.ui.nominate_text = '';
                        $scope.ui.busy = false;
                        $scope.ui.nominate_box = null;
                    })
                    .error(function (res) {
                        $scope.ui.nominate_text = '';
                        $scope.ui.busy = false;
                        $scope.ui.nominate_box = null;
                    });
            }
        };

        /*
        function detectBtm () {
            var scrollTop = (document.documentElement && document.documentElement.scrollTop) || document.body.scrollTop;
            var isBtm = (window.innerHeight + scrollTop + 200) >= document.body.offsetHeight;
            if (isBtm) {
                $scope.getData($scope.ui.squad_code);
            }
        }*/

        $scope.getData = function (callback) {
            if ($scope.ui.page > $scope.ui.pages) {
                $scope.ui.page = $scope.ui.pages;
            }
            //if (!$scope.ui.busy && $scope.ui.page < $scope.ui.pages) {
            if (!$scope.ui.busy && $scope.ui.page <= $scope.ui.pages) {
                $scope.ui.busy = true;
                //var params = {l:limit, p:$scope.ui.page+1, o:$scope.sort}
                var params = {l:limit, p:$scope.ui.page, o:$scope.sort}
                angular.extend(params, $scope.filter);

                $http.get('stickers', {params:params})
                    .success(function(res){
                        $scope.ui.busy = false;
                        //$scope.ui.page += 1;
                        $scope.ui.pages = res.pages;

                        if (res.items) {
                            for (var i = 0; i < res.items.length; i++) {
                                var stk = res.items[i];
                                var path = stk.folder ? stk.folder + '/' : ''
                                path += stk.filename;
                                stk.path = path;
                            }

                            $scope.stickers = res.items;//$scope.stickers.concat(res.items);
                            $scope.ui.total = res.pages === 1 ? res.items.length : res.pages * limit;
                        }

                        /*
                        if (res.pages > 1 && !bound) {
                            bound = true;
                            angular.element(window).on('scroll', detectBtm);
                        }*/

                        if (callback && angular.isFunction(callback)) {
                            callback();
                        }

                        $anchorScroll();
                    })
                    .error(function(res){
                        $scope.ui.busy = false;
                    });
            }/* else if ($scope.ui.page >= $scope.ui.pages && bound) {
                bound = false;
                angular.element(window).off('scroll');
            }*/
        }

        $scope.regetData = function () {
            $scope.stickers = [];
            $scope.sticker = null;
            $scope.ui = {
                //page: 0,
                page: 1,
                pages: 1,
                busy: false,
                has_prev: false,
                has_next: false,
                current_index: 0
            };
            $scope.getData();
        };

        var getPageTimeout = null;

        $scope.getPage = function (p, timeout) {
            if (angular.isDefined(timeout) && timeout) {
                $timeout.cancel(getPageTimeout);
                getPageTimeout = $timeout(function () {
                    $scope.ui.page = p;
                    $scope.getData();
                }, 500);
            } else {
                $scope.ui.page = p;
                $scope.getData();
            }
        };

        $scope.regetData();

        $scope.$watch('filter.stage', function (val) {
            if (!val || val === '0') {
                $scope.missions = [];
            } else if (val === '1') {
                $scope.missions = [
                    {value: 'izeyes',
                     label: 'iZ EYES'},
                    {value: 'mirror',
                     label: 'Mirror of Truth'},
                    {value: 'childlight',
                     label: 'Children of Light'},
                    {value: 'keeper',
                     label: 'iZ KEEPER'},
                    {value: 'pandora',
                     label: 'Pandora Box'},
                    {value: 'dreamhut',
                     label: 'Dreamhut'},
                    {value: 'tree',
                     label: 'Tree of Respect'},
                    {value: 'lightworld',
                     label: 'Light of the World'},
                    {value: 'izsquad',
                     label: 'iZ SQUAD'},
                    {value: 'star',
                     label: 'Star'}
                ];
            } else if (val === '2') {
                $scope.missions = [
                    {value: 'izradar',
                     label: 'iZ RADAR'},
                    {value: 'knowyourenemy',
                     label: 'Know Your Enemy'},
                    {value: 'flameofanger',
                     label: 'Flame of Anger'},
                    {value: 'slowtoanger',
                     label: 'Stay Cool'},
                    {value: 'enails',
                     label: 'E-Nails'},
                    {value: 'three',
                     label: 'Take the 3 Steps'},
                    {value: 'izsquad',
                     label: 'iZ SQUAD MISSION'},
                    {value: 'sense',
                     label: "Sense What's Wrong"},
                    {value: 'izkeeper',
                     label: 'iZ KEEPER'},
                    {value: 'star',
                     label: 'Star'}
                ];
            } else if (val === '3') {
                $scope.missions = [
                    {value: 'izcontrol',
                     label: 'iZ CONTROL'},
                    {value: 'knowyourenemy',
                     label: 'Know Your Enemy'},
                    {value: 'childlight',
                     label: 'Children of Light'},
                    {value: 'izkeeper',
                     label: 'iZ KEEPER'},
                    {value: 'discipline',
                     label: 'Power of your Tongue'},
                    {value: 'time',
                     label: 'Time Management'},
                    {value: 'izsquad',
                     label: 'iZ SQUAD MISSION'},
                    {value: 'brutus',
                     label: "Brutus' Mind Games"},
                    {value: 'dungeon',
                     label: "Boolee's Dungeon"},
                    {value: 'contentcritique',
                     label: "Content Critique"},
                    {value: 'contentcritique2',
                     label: "Inappropriate Content"},
                    {value: 'star',
                     label: 'Star'}
                ];
            } else if (val === '4') {
                $scope.missions = [
                    {value: 'izprotect',
                     label: 'iZ PROTECT'},
                    {value: 'knowyourenemy',
                     label: 'Know Your Enemy'},
                    {value: 'izkeeper',
                     label: 'iZ KEEPER'},
                    {value: 'childlight',
                     label: 'Children of Light'},
                    {value: 'permission',
                     label: "When in Doubt, Don't Click"},
                    {value: 'personal',
                     label: 'Personal Information'},
                    {value: 'izsquad',
                     label: 'iZ SQUAD MISSION'},
                    {value: 'safety',
                     label: 'Mobile Safety'},
                    {value: 'star',
                     label: 'Star'}
                ];
            } else if (val === '5') {
                $scope.missions = [
                    {value: 'izshout',
                     label: 'iZ SHOUT'},
                    {value: 'knowyourenemy',
                     label: 'Know Your Enemy'},
                    {value: 'team',
                     label: 'We are a Team'},
                    {value: 'childlight',
                     label: 'Children of Light'},
                    {value: 'powerpose',
                     label: 'iZ SHOUT Power Pose'},
                    {value: 'speakup',
                     label: 'How to Speak Up'},
                    {value: 'izsquad',
                     label: 'iZ SQUAD MISSION'},
                    {value: 'izkeeper',
                     label: 'iZ KEEPER'},
                    {value: 'star',
                     label: 'Star'}
                ];
            } else if (val === '6') {
                $scope.missions = [
                    {value: 'izears',
                     label: 'iZ EARS'},
                    {value: 'knowyourenemy',
                     label: 'Know Your Enemy'},
                    {value: 'childlight',
                     label: 'Children of Light'},
                    {value: 'izkeeper',
                     label: 'iZ KEEPER'},
                    {value: 'express',
                     label: 'Be Kind'},
                    {value: 'hear',
                     label: 'Hear your Inner Voice'},
                    {value: 'izsquad',
                     label: 'iZ SQUAD MISSION'},
                    {value: 'lightworld',
                     label: 'Light of the World'},
                    {value: 'star',
                     label: 'Star'}
                ];
            } else if (val === '7') {
                $scope.missions = [
                    {value: 'izteleport',
                     label: 'iZ TELEPORT'},
                    {value: 'knowyourenemy',
                     label: 'Know Your Enemy'},
                    {value: 'childlight',
                     label: 'Children of Light'},
                    {value: 'mediarules',
                     label: 'Set the Media Rules'},
                    {value: 'mediapledge',
                     label: 'My Family Media Pledge'},
                    {value: 'teach',
                     label: 'Teach your Parents'},
                    {value: 'izsquad',
                     label: 'iZ SQUAD MISSION'},
                    {value: 'lightworld',
                     label: 'Light of the World'},
                    {value: 'when',
                     label: 'When to Use iZ TELEPORT'},
                    {value: 'star',
                     label: 'Star'}
                ];
            } else {
                $scope.missions = [];
            }
        })
    }

    /** @ngInject */
    function GalleryListCtrl($scope, $http, BASE_URL){
        var bound = false,
            limit = 24,
            pages = null,
            page_index = 0,
            has_page_next = false,
            has_page_prev = false;

        $scope.open_sticker = function (stker, index) {
            if (stker.meta.type == 'story') {
                pages = [{image: stker.file.filename, caption: stker.file.title}];
                if (!stker.pages) {
                    $http.get('/api/gallery/item/' + stker._id)
                        .success(function (res) {
                            stker.pages = res.pages;
                            pages = pages.concat(stker.pages);
                            page_index = 0;
                            $scope.ui.has_page_next = (pages.length > 1);
                            $scope.ui.has_page_prev = false;
                        });
                } else {
                    pages = pages.concat(stker.pages);
                    page_index = 0;
                    $scope.ui.has_page_next = (pages.length > 1);
                    $scope.ui.has_page_prev = false;
                }
                $scope.current = pages[0];
            } else {
                $scope.ui.has_page_next = false;
                $scope.ui.has_page_prev = false;
                $scope.current = {image: stker.file.filename};
            }
            $scope.sticker = stker;
            $scope.ui.has_prev = index > 0;
            $scope.ui.has_next = index < ($scope.stickers.length - 1) || $scope.ui.page < $scope.ui.pages;
            $scope.ui.current_index = index;
        };
        $scope.prev = function () {
            if ($scope.sticker && $scope.ui.current_index > 0 && $scope.stickers) {
                $scope.ui.current_index -= 1;
                $scope.open_sticker($scope.stickers[$scope.ui.current_index], $scope.ui.current_index);
            }
        };
        $scope.next = function () {
            if ($scope.sticker) {
                if ($scope.ui.current_index < ($scope.stickers.length - 1)) {
                    $scope.ui.current_index += 1;
                    $scope.open_sticker($scope.stickers[$scope.ui.current_index], $scope.ui.current_index);
                } else if ($scope.ui.page < $scope.ui.pages) {
                    var curpage = $scope.ui.page;
                    $scope.getData($scope.ui.squad_code, function () {
                        if ($scope.ui.page > curpage) {
                            $scope.next();
                        }
                    });
                }
            }
        };
        $scope.page_prev = function () {
            if (page_index > 0) {
                page_index--;
                $scope.current = pages[page_index];
                if (page_index <= 0) {
                    $scope.ui.has_page_prev = false;
                }
                $scope.ui.has_page_next = true;
            }
        };
        $scope.page_next = function () {
            if (page_index < (pages.length-1)) {
                page_index++;
                $scope.current = pages[page_index];
                if (page_index >= (pages.length-1)) {
                    $scope.ui.has_page_next = false;
                }
                $scope.ui.has_page_prev = true;
            }
        };
        $scope.remove_sticker = function (stker) {
            if (!$scope.ui.busy) {
                $scope.ui.busy = true;
                $http.delete('gallery/delete/' + stker._id)
                    .success(function (res) {
                        $scope.ui.busy = false;
                        if (res.success) {
                            if ($scope.sticker) {
                                if ($scope.ui.has_next) {
                                    $scope.next();
                                } else if ($scope.ui.has_prev) {
                                    $scope.prev();
                                } else {
                                    $scope.sticker = null;
                                }

                                if ($scope.sticker) {
                                    $scope.ui.current_index -= 1;
                                    if ($scope.ui.current_index == 0) {
                                        $scope.ui.has_prev = false;
                                    }
                                }
                            }

                            for (var i = 0; i < $scope.stickers.length; i++) {
                                if (stker._id == $scope.stickers[i]._id) {
                                    $scope.stickers.splice(i, 1);
                                    break;
                                }
                            }
                        }
                    }).error(function () {
                        $scope.ui.busy = false;
                    });
            }
        };
        $scope.readd_sticker = function (stker) {
            if (!$scope.ui.busy) {
                $scope.ui.busy = true;
                $http.post('gallery/delete/' + stker._id)
                    .success(function (res) {
                        $scope.ui.busy = false;
                        if (res.success) {
                            if ($scope.sticker) {
                                if ($scope.ui.has_next) {
                                    $scope.next();
                                } else if ($scope.ui.has_prev) {
                                    $scope.prev();
                                } else {
                                    $scope.sticker = null;
                                }

                                if ($scope.sticker) {
                                    $scope.ui.current_index -= 1;
                                    if ($scope.ui.current_index == 0) {
                                        $scope.ui.has_prev = false;
                                    }
                                }
                            }

                            for (var i = 0; i < $scope.stickers.length; i++) {
                                if (stker._id == $scope.stickers[i]._id) {
                                    $scope.stickers.splice(i, 1);
                                    break;
                                }
                            }
                        }
                    }).error(function () {
                        $scope.ui.busy = false;
                    });
            }
        }

        function detectBtm () {
            var scrollTop = (document.documentElement && document.documentElement.scrollTop) || document.body.scrollTop;
            var isBtm = (window.innerHeight + scrollTop + 200) >= document.body.offsetHeight;
            if (isBtm) {
                $scope.getData($scope.ui.squad_code);
            }
        }

        $scope.getData = function (callback) {
            if (!$scope.ui.busy && $scope.ui.page < $scope.ui.pages) {
                $scope.ui.busy = true;
                var params = {l:limit, p:$scope.ui.page+1};

                switch($scope.galltype) {
                case 'removed':
                    params.removed = true;
                    break;
                case 'reported':
                    params.reported = true;
                    break;
                }

                $http.get('/api/gallery', {params:params})
                    .success(function(res){
                        $scope.ui.busy = false;
                        $scope.ui.page += 1;
                        $scope.ui.pages = res.pages;

                        if (res.items) {
                            for (var i = 0; i < res.items.length; i++) {
                                var stk = res.items[i];
                                if (stk.meta.type == 'story') {
                                    if (stk.file.filename.substring(0, 8) != '/static/') {
                                        stk.file.filename = BASE_URL + 'stickers/download/' + stk.file.filename.substring(14);
                                    }
                                } else {
                                    var path = BASE_URL + 'stickers/download/' + (stk.file.folder ? stk.file.folder + '/' : '');
                                    path += stk.file.filename;
                                    stk.file.filename = path;
                                }
                            }

                            $scope.stickers = $scope.stickers.concat(res.items);
                            $scope.ui.total = res.count;
                        }

                        if (res.pages > 1 && !bound) {
                            bound = true;
                            angular.element(window).on('scroll', detectBtm);
                        }

                        if (callback && angular.isFunction(callback)) {
                            callback();
                        }
                    })
                    .error(function(res){
                        $scope.ui.busy = false;
                    });
            } else if ($scope.ui.page >= $scope.ui.pages && bound) {
                bound = false;
                angular.element(window).off('scroll');
            }
        }

        $scope.regetData = function () {
            $scope.stickers = [];
            $scope.sticker = null;
            $scope.ui = {
                page: 0,
                pages: 1,
                busy: false,
                has_prev: false,
                has_next: false,
                has_page_next: false,
                has_page_prev: false,
                current_index: 0
            };
            $scope.getData();
        }

        $scope.regetData();
    }

    ng.controller('StickerRootCtrl', StickerRootCtrl);
    ng.controller('StickerListCtrl', StickerListCtrl);
    ng.controller('GalleryListCtrl', GalleryListCtrl);
})(angular.module(APP_MODULE_NAME));