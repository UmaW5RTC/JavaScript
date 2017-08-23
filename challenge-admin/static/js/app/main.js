(function(ng){

    function MainCtrl($scope, $state, Session, BASE_URL) {
        var self = this;
        this.ui = {
            busy: false
        }

        $scope.User = {
            username: Session.username,
            name: Session.name,
            role: Session.role
        };

        $scope.$state = $state;
        $scope.BASE_URL = BASE_URL;

        $scope.logout = function() {
            self.ui.busy = true;
            Session.destroy();
        };

    }

    ng.controller('MainCtrl', MainCtrl);

})(angular.module(APP_MODULE_NAME))