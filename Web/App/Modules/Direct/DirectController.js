(function () {

    angular.module('pi-test').controller('DirectController', function ($scope, $rootScope, $http, $state, ConfirmationFactory) {
        $scope.link = "";

        $scope.watch = function(){
            ConfirmationFactory.confirm_play().then(function(){
                $http.post('/movies/play_direct_link?url=' + encodeURIComponent($scope.link) + '&title=Direct%20Link');
            });
        }
    });

})();