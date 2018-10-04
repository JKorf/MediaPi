(function () {
    angular.module('pi-test').directive('switch', function ($rootScope, $state, $timeout) {
        return {
            restrict: 'E',
            scope: {
                model: "=",
                onChange: "=",
                obj: "="
            },
            templateUrl: '/App/Directives/Switch/switch.html',
            link: function ($scope, element, attrs) {
            }
        };
    });
})();