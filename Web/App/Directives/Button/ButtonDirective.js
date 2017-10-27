(function () {
    angular.module('pi-test').directive('basicButton', function ($rootScope, $state, $timeout) {
        return {
            restrict: 'E',
            scope: {
                click: "=",
                text: "@"
            },
            templateUrl: '/App/Directives/Button/button.html',
            link: function ($scope, element, attrs) {
            }
        };
    });
})();