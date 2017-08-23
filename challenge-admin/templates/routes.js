/*
@copyright 2015. iZ Hero
Development by FxHarvest LLP
*/

"use strict";

(function(ng){

    /** @ngInject */
    function routes($stateProvider, $urlRouterProvider) {
        {% include 'routes/%s.js' % current_user.role %}
    }

    ng.config(routes);

})(angular.module(APP_MODULE_NAME));

