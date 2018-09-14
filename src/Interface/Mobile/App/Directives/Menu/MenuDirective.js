(function () {
    angular.module('pi-test').directive('menu', function ($rootScope, $state) {
        return {
            restrict: 'E',
            scope: {
            },
            templateUrl: '/App/Directives/Menu/menu.html',
            link: function ($scope, element, attrs) {

                $(document).mouseup(function (e)
                {
                    if (!$("menu").is(e.target) &&
                        !$(".menu-button").is(e.target) &&
                        !$(".menu-button svg").is(e.target))
                        $scope.closeMenu();
                });

                $rootScope.$on('$stateChangeSuccess', function(event, toState, toParams, fromState, fromParams, options){
                    $scope.currentState = toState.name;
                });

                $rootScope.$on('openMenu', function(){
                    $scope.openMenu();
                });

                $rootScope.$on('closeMenu', function(){
                    $scope.closeMenu();
                });

                $rootScope.$on('toggleMenu', function(){
                    if($("menu").hasClass("open-menu"))
                        $scope.closeMenu();
                    else
                        $scope.openMenu();
                });

                $scope.navigate = function(state){
                    $state.go(state, { type: state });
                }

                $scope.openMenu = function(){
                    $("menu").addClass("open-menu");
                }

                $scope.closeMenu = function(){
                    $("menu").removeClass("open-menu");
                }
            }
        };
    });
})();