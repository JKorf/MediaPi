(function () {
    angular.module('pi-test').directive('optionsMenu', function ($rootScope, $state, $http) {
        return {
            restrict: 'E',
            scope: {
            },
            templateUrl: '/App/Directives/OptionsMenu/optionsmenu.html',
            link: function ($scope, element, attrs) {
                $rootScope.$on('toggleOptions', function(){
                    if($(".options-menu").hasClass("open"))
                        $scope.closeOptions();
                    else
                        $scope.openOptions();
                });

                $(document).mouseup(function (e)
                {
                    if (!$(".options-menu").is(e.target) &&
                        !$(".options-button").is(e.target) &&
                        !$(".options-button svg").is(e.target))
                        $scope.closeOptions();
                });

                $rootScope.$on('$stateChangeSuccess', function(event, toState, toParams, fromState, fromParams, options){
                    $scope.currentState = toState.name;
                });

                $scope.openOptions = function(){
                    $(".options-menu").addClass("open");
                }

                $scope.closeOptions = function(){
                    $(".options-menu").removeClass("open");
                }

                $scope.navigate = function(state){
                    $state.go(state);
                }

                $scope.log = function(){
                    $http.post("/util/test");
                }

                $scope.restart = function(){
                    if (confirm('Are you sure you want to restart the Raspberry Pi?')) {
                        $http.post("/util/restart_pi");
                    }
                }
            }
        };
    });
})();