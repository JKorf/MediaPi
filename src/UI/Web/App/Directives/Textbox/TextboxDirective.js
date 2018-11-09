(function () {
    angular.module('pi-test').directive('textbox', function ($rootScope, $state, $timeout) {
        return {
            restrict: 'E',
            scope: {
                model: "=",
                placeholder: "@",
                enter: "="
            },
            templateUrl: '/App/Directives/Textbox/textbox.html',
            link: function ($scope, element, attrs) {
            }
        };
    });
})();