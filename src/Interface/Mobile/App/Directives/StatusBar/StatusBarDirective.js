(function () {
    angular.module('pi-test').directive('statusBar', function ($rootScope, $state, RequestFactory) {
        return {
            restrict: 'E',
            scope: {
            },
            templateUrl: '/App/Directives/StatusBar/statusbar.html',
            link: function ($scope, element, attrs) {
                statusInterval = RequestFactory.StartRequesting("/util/status", 2000, handleStatus, handleError);

                function handleStatus(response){
                    $scope.data = response.data;
                    $(".status-ellipse").css('background', colorForReady($scope.data.buffer_ready));
                    $(".memory-item").css('color', colorForMemory($scope.data.memory));
                }

                function handleError(err){
                    console.log(err);
                    $scope.data = {};
                }

                function colorForReady(ready){
                    if (ready < 2000000)
                        return "#e07700";
                    if (ready < 10000000)
                        return "#f7ff21";
                    return "#7bff0f";
                }

                function colorForMemory(mem){
                    if (mem < 80)
                        return "#999";
                    if (mem < 94)
                        return "#e07700";
                    return "#ff2b2b";
                }
            }
        };
    });
})();