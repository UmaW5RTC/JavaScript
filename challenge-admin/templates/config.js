/*
@copyright 2015. iZ Hero
Development by FxHarvest LLP
*/

"use strict";

var CONFIG_MODULE_NAME = 'izApp.config';

(function(ng){

    ng.constant('XSRF_NAME', '{{xsrf_name}}');
    ng.constant('BASE_URL', '{{base_url}}/');
    ng.constant('VIEW_PATH', '{{ url_for("client.views", filename="", _v=True)}}');
    ng.constant('CURRENT_USER_URL', '{{current_user_url}}');
    ng.constant('LOGOUT_URL', '{{logout_url}}');
    ng.constant('VERSION', '{{config['VERSION']}}');
    ng.constant('LANG', '{{g.lang}}');

    ng.constant('AUTH_EVENTS', {
      loginSuccess: 'auth-login-success',
      loginFailed: 'auth-login-failed',
      logoutSuccess: 'auth-logout-success',
      sessionTimeout: 'auth-session-timeout',
      notAuthenticated: 'auth-not-authenticated',
      notAuthorized: 'auth-not-authorized'
    });

    ng.constant('USER_ROLES', {
      administrator: 'Administrator',
      counselor: 'Counselor',
      teacher: 'Teacher',
      student: 'Student'
    });

    /** @ngInject */
    function Session($http) {
        var self = this;

        this.id = "{{current_user.id}}";
        if (this.id) {
            this.name = "{{current_user.get_name().replace('"', '\\"')}}";
            this.username = "{{current_user.get_username().replace('"', '\\"')}}";
            this.role = "{{current_user.get_role().replace('"', '\\"')}}";
            this.school = "{{(current_user.get('school') or '').replace('"', '\\"')}}";
            this.is_subteacher = {{((current_user.get("hod") and "true") or "false")}};
        }

        this.destroy = function () {
            var step = 0;
            var to_root = function() {
                step++;
                if (step == 2) {
                    self.id = null;
                    self.name = null;
                    self.username = null;
                    self.role = null;
                    //window.location = '{{login_url}}';
                    window.location = '/';
                }
            };

            $http.post('{{logout_url}}').then(to_root);
            $http.post('/api/acct/logout').then(to_root);
        };

        this.is_authorized = function (authorizedRoles) {
            if (!angular.isArray(authorizedRoles)) {
                authorizedRoles = [authorizedRoles];
            }
            return self.id && authorizedRoles.indexOf(self.role) !== -1;
        };

        return this;
    }

    {%-if token %}

    ng.run(['$http', function($http) {
      $http.defaults.headers.common['X-AUTH'] = "{{token}}";
    }])

    {%endif-%}

    ng.service('Session', Session);

})(angular.module(CONFIG_MODULE_NAME, []))
