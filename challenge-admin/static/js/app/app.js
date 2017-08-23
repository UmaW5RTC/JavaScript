/*
@copyright 2015. iZ Hero
Development by FxHarvest LLP
*/

"use strict";

var APP_MODULE_NAME = "izAdmin";

(function(ng){

    ng.config(['$httpProvider', '$provide', '$stateProvider', '$urlRouterProvider', 'BASE_URL', 'XSRF_NAME', 'VERSION', 'VIEW_PATH', function($httpProvider, $provide, $stateProvider, $urlRouterProvider, BASE_URL, XSRF_NAME, VERSION, VIEW_PATH){

        $httpProvider.defaults.xsrfCookieName = XSRF_NAME;

        var r_url = /static\//;
        var r_whitelist = /(ui-grid)/;
        var r_view_url = /^VIEW_PATH\//;

        $provide.decorator('$http', ['$delegate', function ($delegate) {
            var get = $delegate.get;
            $delegate.get = function (url, config) {

                if (!r_whitelist.test(url)) {
                    // GET cache busting
                    if (r_url.test(url)) {
                        url += (url.indexOf("?") == -1 ? "?" : "&") + "_v=" + VERSION;
                    }

                    if (r_view_url.test(url)) {
                        url = url.replace("VIEW_PATH/", VIEW_PATH);
                    }
                    else if (url.substr(0, 1) != '/') {
                        url = BASE_URL + url;
                    }
                }

                return get(url, config);
            };

            var post = $delegate.post;
            $delegate.post = function (url, config) {
                if (r_view_url.test(url)) {
                    url = url.replace("VIEW_PATH/", VIEW_PATH);
                }
                else if (url.substr(0, 1) != '/') {
                    url = BASE_URL + url;
                }
                return post(url, config);
            };

            var put = $delegate.put;
            $delegate.put = function (url, config) {
                if (r_view_url.test(url)) {
                    url = url.replace("VIEW_PATH/", VIEW_PATH);
                }
                else if (url.substr(0, 1) != '/') {
                    url = BASE_URL + url;
                }
                return put(url, config);
            };

            var del = $delegate.delete;
            $delegate.delete = function (url, config) {
                if (r_view_url.test(url)) {
                    url = url.replace("VIEW_PATH/", VIEW_PATH);
                }
                else if (url.substr(0, 1) != '/') {
                    url = BASE_URL + url;
                }
                return del(url, config);
            };

            return $delegate;
        }]);

    }])

    .run(['$templateCache', '$http', '$interval', 'XSRF_NAME', function($templateCache, $http, $interval, XSRF_NAME) {

            // preload form template into cache

            /*if (ngApp.templates) {
                $http.get(ngApp.templates.form, {cache: $templateCache});
            }*/

            /*var token = getCookie(XSRF_NAME);
            if(!token) {
                document.getElementById('wrapper').innerHTML =
                    '<div class="alert alert-danger">' +
                        '<strong>IMPORTANT</strong><br>This site uses cookies for site security protection.<br>Please enable cookie to use this site.' +
                    '</div>';
            }
*/
            /*var nocache = {config: {cache: null}};

            if (AppConfig.current_user_url) {
                $http.get(CURRENT_USER_URL, nocache)
                    .success(function(user){
                        if (user.email) {

                            ng.constant('UserRole', user.role);
                            ng.constant('User', user);

                            $interval(function(){
                                $http.get(CURRENT_USER_URL, nocache)
                                .error(function(){
                                    window.location = LOGOUT_URL;
                                });

                            }, 300000); // check 5min interval

                        }

                    })
                    .error(function(){
                        window.location = LOGOUT_URL;
                    })
            }*/

        }]
    );

    function getCookie(cname, f) {
        var name = cname + "=";
        var ca = document.cookie.split(';');
        for (var i = 0; i < ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0) == ' ') c = c.substring(1);
            if (c.indexOf(name) != -1) {
                var v = decodeURIComponent(c.substring(name.length, c.length));
                return f && f(v) || v;
            }
        }
        return null;
    }

    function setCookie(cname, cvalue, exdays, f) {
        var expires = "";
        if (exdays) {
            expires = "expires=";
            if (exdays > 0) {
                var d = new Date();
                d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
                expires += d.toUTCString();
            }
            else {
                cvalue = '';
                expires += "Thu, 01 Jan 1970 00:00:00 UTC";
            }
        }
        if (f) {
            cvalue = f(cvalue);
        }
        document.cookie = cname + "=" + encodeURIComponent(cvalue) + "; " + expires;
    }


})(angular.module(APP_MODULE_NAME, [CONFIG_MODULE_NAME, 'ui.grid', 'ui.grid.resizeColumns', 'ui.grid.infiniteScroll', 'ui.grid.pagination', 'ui.grid.selection', 'ngAnimate', 'ui.router', 'ui.grid.edit', 'mgcrea.ngStrap.tooltip']))


