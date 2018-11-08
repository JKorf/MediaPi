(function () {
    angular.module('pi-test').directive('movieBox', function ($rootScope, $state) {
        return {
            restrict: 'E',
            scope: {
                movie: '='
            },
            templateUrl: '/App/Modules/Movies/moviebox.html',
            link: function ($scope, element, attrs) {

            }
        }
    });
})();