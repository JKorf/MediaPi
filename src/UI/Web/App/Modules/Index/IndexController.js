(function () {

    angular.module('pi-test').controller('IndexController', function ($scope, $rootScope, $q, $http, $state, $timeout, $compile, $window, CacheFactory, RealtimeFactory, PopupFactory, SVGFactory) {
        $http.defaults.headers.post["Content-Type"] = "application/x-www-form-urlencoded";

        $rootScope.$watch('playerState', function (newv, oldv){
            SetHeight(newv);
        });

        $rootScope.$on('$stateChangeSuccess', function(event, toState, toParams, fromState, fromParams, options){
            $timeout(function(){
                SetHeight($rootScope.playerState);
            }, 1);
        });

        $rootScope.openMenu = function(event){
            if($(event.target).parent(".slider").length == 0)
                $rootScope.$broadcast('openMenu');
        }

        $rootScope.closeMenu = function(event){
            if($(event.target).parent(".slider").length == 0)
                $rootScope.$broadcast('closeMenu');
        }

        function SetHeight(playerState){
            $(".view").removeClass("player-closed");
            $(".view").removeClass("player-visible");

            if (playerState && playerState != 'Nothing' && playerState != 'disconnected' && playerState != 'Ended'){
                $(".view").addClass("player-visible");
                $("menu").addClass("player-open");
            }else{
                $(".view").addClass("player-closed");
                $("menu").removeClass("player-open");
            }
        }

        function Init(){
            $rootScope.pageTitle = "Mediaplayer";
            $http.get("/util/startup").then(function (response) {
                $rootScope.pageTitle = response.data.instance_name;
                $rootScope.lightingEnabled = response.data.lighting_enabled;
            });
        }

        Init();
    });
})();