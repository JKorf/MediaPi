(function () {

    angular.module('pi-test').controller('TVController', function ($scope, $http, MemoryFactory) {

         function Init(){
            $http.get("/tv/get_devices").then(function(data){
                console.log(data);
            });

         }

         $scope.on = function(){
            $http.post("/tv/tv_on");
         }

         $scope.off = function(){
            $http.post("/tv/tv_off");
         }

         $scope.up = function(){
            $http.post("/tv/channel_up");
         }

         $scope.down = function(){
            $http.post("/tv/channel_down");
         }

         Init();
    });
})();