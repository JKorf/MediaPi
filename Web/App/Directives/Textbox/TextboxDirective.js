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
                $scope.textboxFocus = function($event){
                    $($event.target).css("border", "1px solid #3d7ed3");
                }

                $scope.textboxBlur = function($event){
                     $($event.target).css("border", "1px solid #777");
                }
            }
        };
    });
})();