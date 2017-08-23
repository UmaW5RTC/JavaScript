(function(ng){

    ng.directive('nxEqual', function() {
        return {
            require: 'ngModel',
            link: function (scope, elem, attrs, model) {
                if (!attrs.nxEqual) {
                    return;
                }
                scope.$watch(attrs.nxEqual, function (value) {
                    model.$setValidity('nxEqual', value === model.$viewValue);
                });
                model.$parsers.push(function (value) {
                    var isValid = value === scope.$eval(attrs.nxEqual);
                    model.$setValidity('nxEqual', isValid);
                    return isValid ? value : undefined;
                });
            }
        };
    })
    .directive('noSpace', function() {
        return {
            require: 'ngModel',
            link: function(scope, ele, attrs, c) {
                ele.bind('blur', function() {
                    var username = scope.$eval(attrs.ngModel);
                    var spacere = /\s/;
                    scope.$apply(function () {
                        c.$setValidity('noSpace', !(username && spacere.test(username)));
                    });
                });
            }
        }
    })
    .directive('ensureUnique', ['$http', function($http) {
        return {
            require: 'ngModel',
            link: function(scope, ele, attrs, c) {
                ele.bind('blur', function() {
                    var params = {};
                    params[attrs.name] = scope.$eval(attrs.ngModel);
                    var minlength = (attrs.minlength) ? parseInt(attrs.minlength) : 3;
                    var spacere = /\s/;
                    if (attrs.params) {
                        _.extend(params, scope.$eval(attrs.params));
                    }
                    if (params[attrs.name] && params[attrs.name].length >= minlength && !spacere.test(params[attrs.name])) {
                        $http.get(attrs.ensureUnique, {params: params})
                            .success(function(res) {
                                c.$setValidity('ensureUnique', res.success);
                            })
                            .error(function(res) {
                                c.$setValidity('ensureUnique', true);
                            });
                    }
                });
            }
        }
    }]);

})(angular.module(APP_MODULE_NAME));