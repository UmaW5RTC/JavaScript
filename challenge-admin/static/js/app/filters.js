/*
@copyright 2015. FxHarvest LLP
*/

'use strict';

(function(ng){

    ng.filter('moment_date', function() {
        return function(input, format) {
            var d = moment.isMoment(input) && input || moment(input);
            if(!format) format='D MMM YYYY';
            return d.format(format);
        }
    })

})(angular.module(APP_MODULE_NAME))