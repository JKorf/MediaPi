(function () {
    angular.module('pi-test').directive('dropdown', function ($rootScope, $state, $timeout) {
        return {
            restrict: 'E',
            scope: {
                model: "=",
                options: "=",
                placeholder: "@"
            },
            templateUrl: '/App/Directives/Dropdown/dropdown.html',
            link: function ($scope, element, attrs) {
            }
        };
    });
})();