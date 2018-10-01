(function () {

    angular.module('pi-test').controller('LightingController', function ($scope, $http) {
         function Init(){
            $http.get("/lighting/get_lights").then(function(data){
                console.log(data);
            });
         }


         Init();
    });
})();