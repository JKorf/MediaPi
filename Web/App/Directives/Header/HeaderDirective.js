(function () {
    angular.module('pi-test').directive('header', function ($rootScope, $http, $state, $timeout, $state) {
        return {
            restrict: 'E',
            templateUrl: '/App/Directives/Header/header.html',
            link: function ($scope, element, attrs) {

                $scope.toggleMenu = function(){
                    $rootScope.$broadcast('toggleMenu');
                }

                $scope.toggleOptions = function(){
                    $rootScope.$broadcast('toggleOptions');
                }
            }
        };
    });
})();