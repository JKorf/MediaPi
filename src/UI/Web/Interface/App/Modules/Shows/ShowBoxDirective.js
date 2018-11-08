(function () {
    angular.module('pi-test').directive('showBox', function ($rootScope, $state) {
        return {
            restrict: 'E',
            scope: {
                show: '='
            },
            templateUrl: '/App/Modules/Shows/showbox.html',
            link: function ($scope, element, attrs) {

            }
        }
    });
})();