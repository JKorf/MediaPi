(function () {
    angular.module('pi-test').directive('unfinishedLine', function ($rootScope, $state, $timeout) {
        return {
            restrict: 'E',
            scope: {
                percentage: "="
            },
            templateUrl: '/App/Directives/UnfinishedLine/unfinishedline.html',
            link: function ($scope, element, attrs) {
                $scope.$watch("percentage", function (newv, oldv){
                    if(newv)
                    {
                        $(element).find(".unfinished-line").css("width", $scope.percentage *100 + "%")
                    }else{
                        $(element).find(".unfinished-line").css("width", "0%")
                    }
                });
            }
        };
    });
})();