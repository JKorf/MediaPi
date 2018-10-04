(function () {

    angular.module('pi-test').controller('LightingController', function ($scope, $http) {
        $scope.devices = [];

         function Init(){
             $http.post("/lighting/debug");

             $http.get("/lighting/get_lights").then(function(data){
                 console.log(data);
                 $scope.devices = data;
             });
         }

         $scope.on = function()
         {
             var id = $scope.devices[0].id;
             $http.post("/lighting/switch_light?id="+id+"&state=on");
         };

         $scope.off = function()
         {
             var id = $scope.devices[0].id;
             $http.post("/lighting/switch_light?id="+id+"&state=off");
         };

         Init();
    });
})();