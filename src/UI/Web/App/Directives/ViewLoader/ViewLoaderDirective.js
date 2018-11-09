(function () {
    angular.module('pi-test').directive('viewLoader', function ($rootScope, $state, $timeout) {
        return {
            restrict: 'E',
            scope: {
                promise: "="
            },
            templateUrl: '/App/Directives/ViewLoader/loader.html',
            link: function ($scope, element, attrs) {
                checkPromise();

                $scope.$watch("promise", function (newv, oldv){
                    if(newv)
                    {
                        showLoader();
                        checkPromise();
                    }
                });

                function checkPromise(){
                    if(!$scope.promise)
                        return;

                    $scope.promise.then(function(){
                        hideLoader();
                    },
                    function(){
                        hideLoader();
                    });
                }

                function showLoader(){
                    $(".view-loader").css("display", "block");
                    $(".view").scrollTop(0);
                    $(".view").css("overflow", "hidden");
                }

                function hideLoader(){
                    $(".view-loader").css("display", "none");
                    $(".view").css("overflow-y", "auto");
                }
            }
        };
    });
})();